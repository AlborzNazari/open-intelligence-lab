"""
provenance.py — Open Intelligence Lab v0.4.0
Provenance Validation Engine

Every STIX object ingested from an external feed (MISP or TAXII) receives
a ProvenanceRecord — a chain-of-custody stamp carrying:

  - source:            which platform/feed delivered the data
  - reported_by:       originating organization
  - original_timestamp: when the intelligence was first published
  - ingested_at:       when OI Lab received it
  - trust_level:       confidence score [0.0 – 1.0]
  - staleness_days:    age of the intelligence at ingestion time
  - is_stale:          True if older than the configured staleness threshold
  - feed_type:         "misp" | "taxii" | "manual"

This is the foundation of bidirectional trust. Without provenance,
ingested IOCs and curated IOCs are indistinguishable. With it, every
graph node knows where it came from and how much to trust it.

Author: Alborz Nazari
License: MIT
"""

import uuid
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

# Intelligence older than this is flagged as stale
DEFAULT_STALENESS_THRESHOLD_DAYS = 90

# Minimum trust floor — nothing below this enters the graph
MINIMUM_TRUST_THRESHOLD = 0.10

# Source trust priors — base multiplier before threat-level adjustment
SOURCE_TRUST_PRIORS: dict[str, float] = {
    "MISP-CISA": 1.00,
    "MISP-CERT-EU": 0.95,
    "MISP-CIRCL": 0.95,
    "MISP-NATO": 0.95,
    "MISP-Community": 0.75,
    "TAXII-Commercial": 0.80,
    "TAXII-OpenCTI": 0.85,
    "TAXII-Unknown": 0.60,
    "manual": 1.00,  # Hand-curated entries are always trusted
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _parse_timestamp(ts: str) -> Optional[datetime]:
    """Parse an ISO 8601 timestamp string to a timezone-aware datetime."""
    if not ts:
        return None
    formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.000Z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(ts[: len(fmt)], fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


# ─────────────────────────────────────────────
# ProvenanceRecord — the chain-of-custody unit
# ─────────────────────────────────────────────


@dataclass
class ProvenanceRecord:
    """
    Immutable chain-of-custody record for a single STIX object.

    Attached to every ingested object before it enters the graph.
    Think of this as the evidence tag in a forensic chain of custody:
    who collected it, when, from where, and how reliable is the source.
    """

    # Identity
    record_id: str  # Unique ID for this provenance record
    stix_id: str  # The STIX object this record belongs to

    # Chain of custody fields
    source: str  # Feed/platform name (e.g. "MISP-CERT-EU")
    reported_by: str  # Originating organization
    original_timestamp: str  # When the intelligence was first published
    ingested_at: str  # When OI Lab ingested it

    # Trust and confidence
    trust_level: float  # Computed [0.0 – 1.0] confidence score
    source_prior: float  # Base trust prior for this source
    feed_type: str  # "misp" | "taxii" | "manual"

    # Staleness
    staleness_days: int  # Age in days at ingestion time
    is_stale: bool  # True if older than threshold

    # Optional MISP-specific context
    misp_event_id: Optional[str] = None
    misp_attribute_uuid: Optional[str] = None
    misp_category: Optional[str] = None
    analysis_state: Optional[str] = None  # "initial" | "ongoing" | "complete"

    # Optional TAXII-specific context
    taxii_collection_id: Optional[str] = None
    taxii_server_url: Optional[str] = None

    # Validation outcome
    passed_validation: bool = True
    rejection_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_stix_extension(self) -> dict:
        """
        Serialize this record as a set of x_oi_ extension fields
        that can be embedded directly into a STIX object.
        """
        return {
            "x_oi_provenance_id": self.record_id,
            "x_oi_source": self.source,
            "x_oi_reported_by": self.reported_by,
            "x_oi_original_timestamp": self.original_timestamp,
            "x_oi_ingested_at": self.ingested_at,
            "x_oi_trust_level": round(self.trust_level, 4),
            "x_oi_feed_type": self.feed_type,
            "x_oi_staleness_days": self.staleness_days,
            "x_oi_is_stale": self.is_stale,
            "x_oi_passed_validation": self.passed_validation,
            "x_oi_rejection_reason": self.rejection_reason,
            "x_oi_analysis_state": self.analysis_state,
        }


# ─────────────────────────────────────────────
# ProvenanceEngine — the trusted handshake
# ─────────────────────────────────────────────


class ProvenanceEngine:
    """
    Creates and validates ProvenanceRecords for ingested intelligence.

    The provenance engine is the trusted handshake between external feeds
    and the OI Lab knowledge graph. No ingested object enters the graph
    without passing through this engine first.

    Responsibilities:
    1. Compute adjusted trust score from source prior + feed-specific signals
    2. Detect staleness based on original_timestamp
    3. Reject objects that fall below the minimum trust threshold
    4. Attach chain-of-custody fields to STIX objects

    Staleness policy:
    - Objects older than DEFAULT_STALENESS_THRESHOLD_DAYS are flagged is_stale=True
    - Stale objects are still ingested but their trust_level is penalized (-0.20)
    - Objects below MINIMUM_TRUST_THRESHOLD after penalty are rejected entirely
    """

    def __init__(
        self,
        staleness_threshold_days: int = DEFAULT_STALENESS_THRESHOLD_DAYS,
        min_trust: float = MINIMUM_TRUST_THRESHOLD,
    ):
        self.staleness_threshold_days = staleness_threshold_days
        self.min_trust = min_trust
        self._registry: dict[str, ProvenanceRecord] = {}

    # ── Record Creation ────────────────────────

    def create_record(
        self,
        stix_id: str,
        source: str,
        reported_by: str,
        original_timestamp: str,
        trust_level: float,
        feed_type: str = "taxii",
        **kwargs,
    ) -> ProvenanceRecord:
        """
        Create a validated ProvenanceRecord for a STIX object.

        Steps:
        1. Look up source trust prior
        2. Apply staleness penalty if applicable
        3. Reject if below minimum trust floor
        4. Register record in internal registry
        """
        ingested_at = _now()
        record_id = f"provenance--{uuid.uuid4()}"

        # Step 1 — source prior
        source_prior = self._get_source_prior(source)

        # Step 2 — staleness
        staleness_days = self._compute_staleness(original_timestamp)
        is_stale = staleness_days > self.staleness_threshold_days

        # Step 3 — adjusted trust
        adjusted_trust = self._adjust_trust(trust_level, source_prior, is_stale)

        # Step 4 — validation
        passed = adjusted_trust >= self.min_trust
        rejection_reason = None
        if not passed:
            rejection_reason = (
                f"Trust level {adjusted_trust:.2f} below minimum threshold "
                f"{self.min_trust:.2f} after staleness/source adjustment"
            )
            logger.warning(
                f"[Provenance] REJECTED {stix_id} from {source} — {rejection_reason}"
            )
        else:
            logger.debug(
                f"[Provenance] ACCEPTED {stix_id} from {source} "
                f"trust={adjusted_trust:.2f} stale={is_stale} age={staleness_days}d"
            )

        record = ProvenanceRecord(
            record_id=record_id,
            stix_id=stix_id,
            source=source,
            reported_by=reported_by,
            original_timestamp=original_timestamp,
            ingested_at=ingested_at,
            trust_level=adjusted_trust,
            source_prior=source_prior,
            feed_type=feed_type,
            staleness_days=staleness_days,
            is_stale=is_stale,
            passed_validation=passed,
            rejection_reason=rejection_reason,
            **{
                k: v
                for k, v in kwargs.items()
                if k in ProvenanceRecord.__dataclass_fields__
            },
        )

        self._registry[stix_id] = record
        return record

    def validate_and_stamp(
        self,
        stix_object: dict,
        provenance: ProvenanceRecord,
    ) -> Optional[dict]:
        """
        Stamp a STIX object with its provenance chain-of-custody fields.
        Returns None if the object failed provenance validation.

        This is the gate: objects that don't pass are not returned,
        and therefore never enter the knowledge graph.
        """
        if not provenance.passed_validation:
            return None

        # Embed provenance fields directly into the STIX object
        stamped = dict(stix_object)
        stamped.update(provenance.to_stix_extension())
        return stamped

    def get_record(self, stix_id: str) -> Optional[ProvenanceRecord]:
        return self._registry.get(stix_id)

    def get_all_records(self) -> list[dict]:
        return [r.to_dict() for r in self._registry.values()]

    def get_stale_records(self) -> list[dict]:
        return [r.to_dict() for r in self._registry.values() if r.is_stale]

    def get_rejected_records(self) -> list[dict]:
        return [r.to_dict() for r in self._registry.values() if not r.passed_validation]

    def get_summary(self) -> dict:
        records = list(self._registry.values())
        total = len(records)
        accepted = sum(1 for r in records if r.passed_validation)
        rejected = sum(1 for r in records if not r.passed_validation)
        stale = sum(1 for r in records if r.is_stale)
        by_source = {}
        for r in records:
            by_source.setdefault(r.source, {"accepted": 0, "rejected": 0, "stale": 0})
            if r.passed_validation:
                by_source[r.source]["accepted"] += 1
            else:
                by_source[r.source]["rejected"] += 1
            if r.is_stale:
                by_source[r.source]["stale"] += 1
        avg_trust = (
            round(sum(r.trust_level for r in records) / total, 4) if total > 0 else 0.0
        )

        return {
            "total_records": total,
            "accepted": accepted,
            "rejected": rejected,
            "stale_flagged": stale,
            "average_trust_level": avg_trust,
            "by_source": by_source,
        }

    # ── Internal helpers ───────────────────────

    def _get_source_prior(self, source: str) -> float:
        """
        Look up the base trust prior for a source.
        Falls back to partial match, then to TAXII-Unknown default.
        """
        if source in SOURCE_TRUST_PRIORS:
            return SOURCE_TRUST_PRIORS[source]
        # Try partial match — e.g. "MISP-MyOrg" → MISP-Community prior
        for key, prior in SOURCE_TRUST_PRIORS.items():
            if key.split("-")[0].lower() in source.lower():
                return prior
        return SOURCE_TRUST_PRIORS["TAXII-Unknown"]

    def _compute_staleness(self, original_timestamp: str) -> int:
        """Return the age in days of the intelligence at ingestion time."""
        dt = _parse_timestamp(original_timestamp)
        if not dt:
            return 0
        now = datetime.now(timezone.utc)
        delta = now - dt
        return max(0, delta.days)

    def _adjust_trust(
        self,
        raw_trust: float,
        source_prior: float,
        is_stale: bool,
    ) -> float:
        """
        Compute final adjusted trust level.

        Formula: adjusted = raw_trust * source_prior — staleness_penalty
        Clamped to [0.0, 1.0].
        """
        adjusted = raw_trust * source_prior
        if is_stale:
            adjusted -= 0.20  # Staleness penalty
        return round(max(0.0, min(1.0, adjusted)), 4)
