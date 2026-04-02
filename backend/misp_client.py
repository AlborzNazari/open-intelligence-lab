"""
misp_client.py — Open Intelligence Lab v0.4.0
MISP REST API Client

Connects to a MISP (Malware Information Sharing Platform) instance and pulls
threat intelligence events as STIX 2.1 objects. Each ingested object is passed
through the provenance engine before entering the knowledge graph.

MISP is the de facto community standard used by government agencies, national
CERTs, and ISACs globally. This client makes Open Intelligence Lab a participant
in the live threat sharing ecosystem rather than an isolated tool.

Tested against: MISP >= 2.4.x
MISP REST API docs: https://www.misp-project.org/openapi/

Author: Alborz Nazari
License: MIT
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
import urllib.request
import urllib.error
import ssl

from provenance import ProvenanceRecord, ProvenanceEngine

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# MISP Attribute Type → STIX Type Mapping
# ─────────────────────────────────────────────

# Maps MISP attribute categories/types to STIX 2.1 object types.
# MISP uses a flat attribute model; we lift these into structured STIX objects.
MISP_TYPE_TO_STIX: dict[str, str] = {
    "ip-src": "indicator",
    "ip-dst": "indicator",
    "domain": "indicator",
    "hostname": "indicator",
    "url": "indicator",
    "md5": "indicator",
    "sha1": "indicator",
    "sha256": "indicator",
    "filename": "indicator",
    "threat-actor": "threat-actor",
    "malware-type": "malware",
    "vulnerability": "vulnerability",
    "campaign-name": "campaign",
}

# MISP threat levels map to STIX confidence bands
MISP_THREAT_LEVEL_TO_CONFIDENCE: dict[str, float] = {
    "1": 0.95,  # High
    "2": 0.75,  # Medium
    "3": 0.50,  # Low
    "4": 0.25,  # Undefined
}

# MISP analysis states
MISP_ANALYSIS_TO_LABEL: dict[str, str] = {
    "0": "initial",
    "1": "ongoing",
    "2": "complete",
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _stix_id(object_type: str) -> str:
    return f"{object_type}--{uuid.uuid4()}"


# ─────────────────────────────────────────────
# MISP Client
# ─────────────────────────────────────────────


class MISPClient:
    """
    REST client for a MISP instance.

    Pulls events and attributes, normalizes them to STIX 2.1 objects,
    and stamps each with a provenance record for chain-of-custody tracking.

    Usage:
        client = MISPClient(
            base_url="https://misp.example.org",
            api_key="your-misp-auth-key",
            source_label="MISP-CERT-EU",
            verify_ssl=True,
        )
        stix_objects, provenance_records = client.fetch_recent_events(days=7)
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        source_label: str = "MISP",
        verify_ssl: bool = True,
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.source_label = source_label
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.provenance_engine = ProvenanceEngine()

    # ── HTTP helpers ──────────────────────────

    def _request(self, path: str, payload: Optional[dict] = None) -> dict:
        """
        Make an authenticated request to the MISP REST API.
        MISP uses an Authorization header with the API key.
        All MISP API traffic runs over HTTPS (TLS mandatory).
        """
        url = f"{self.base_url}{path}"
        body = json.dumps(payload).encode("utf-8") if payload else None
        method = "POST" if payload else "GET"

        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Authorization", self.api_key)
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")

        ssl_ctx = ssl.create_default_context()
        if not self.verify_ssl:
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

        try:
            with urllib.request.urlopen(
                req, context=ssl_ctx, timeout=self.timeout
            ) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            raise ConnectionError(
                f"MISP API error {e.code} at {url}: {body_text[:200]}"
            ) from e
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Cannot reach MISP at {self.base_url}: {e.reason}"
            ) from e

    # ── Event fetching ─────────────────────────

    def fetch_recent_events(
        self, days: int = 7, limit: int = 100
    ) -> tuple[list[dict], list[ProvenanceRecord]]:
        """
        Fetch MISP events from the last N days.
        Returns (stix_objects, provenance_records).

        Each STIX object has a corresponding ProvenanceRecord carrying:
        - source: which MISP instance
        - reported_by: event org name
        - timestamp: when the event was created
        - trust_level: derived from MISP threat level
        - analysis_state: initial / ongoing / complete
        """
        logger.info(
            f"[MISP] Fetching events from last {days} days — source: {self.source_label}"
        )

        payload = {
            "returnFormat": "json",
            "limit": limit,
            "page": 1,
            "last": f"{days}d",
            "published": True,
        }

        try:
            response = self._request("/events/restSearch", payload)
        except ConnectionError as e:
            logger.error(f"[MISP] Feed fetch failed: {e}")
            return [], []

        events = response.get("response", [])
        if not events:
            logger.warning(f"[MISP] No events returned from {self.source_label}")
            return [], []

        all_stix: list[dict] = []
        all_provenance: list[ProvenanceRecord] = []

        for event_wrapper in events:
            event = event_wrapper.get("Event", event_wrapper)
            stix_objs, prov_records = self._event_to_stix(event)
            all_stix.extend(stix_objs)
            all_provenance.extend(prov_records)

        logger.info(
            f"[MISP] Ingested {len(all_stix)} STIX objects "
            f"from {len(events)} events — {self.source_label}"
        )
        return all_stix, all_provenance

    def fetch_event_by_id(
        self, event_id: str
    ) -> tuple[list[dict], list[ProvenanceRecord]]:
        """Fetch a single MISP event by ID."""
        try:
            response = self._request(f"/events/view/{event_id}")
        except ConnectionError as e:
            logger.error(f"[MISP] Failed to fetch event {event_id}: {e}")
            return [], []

        event = response.get("Event", response)
        return self._event_to_stix(event)

    # ── MISP Event → STIX Normalization ───────

    def _event_to_stix(self, event: dict) -> tuple[list[dict], list[ProvenanceRecord]]:
        """
        Convert one MISP event and its attributes into STIX 2.1 objects.
        Generates a ProvenanceRecord for each object for chain-of-custody tracking.
        """
        stix_objects: list[dict] = []
        provenance_records: list[ProvenanceRecord] = []

        event_id = event.get("id", "unknown")
        event_uuid = event.get("uuid", str(uuid.uuid4()))
        org_name = event.get("Orgc", {}).get("name", self.source_label)
        threat_level = str(event.get("threat_level_id", "4"))
        analysis_state = str(event.get("analysis", "0"))
        event_date = event.get("date", _now()[:10])
        event_info = event.get("info", "MISP Event")
        distribution = int(event.get("distribution", 0))

        base_confidence = MISP_THREAT_LEVEL_TO_CONFIDENCE.get(threat_level, 0.25)
        # Distribution level also affects trust:
        # 0=org-only, 1=community, 2=connected communities, 3=all, 4=sharing-group, 5=inherit
        distribution_modifier = {0: -0.15, 1: 0.0, 2: 0.05, 3: 0.05, 4: 0.0, 5: 0.0}
        adjusted_confidence = max(
            0.05,
            min(1.0, base_confidence + distribution_modifier.get(distribution, 0.0)),
        )

        # Build a STIX note to represent the MISP event context
        event_note = {
            "type": "note",
            "spec_version": "2.1",
            "id": _stix_id("note"),
            "created": f"{event_date}T00:00:00.000Z",
            "modified": _now(),
            "abstract": f"MISP Event {event_id}: {event_info}",
            "content": event_info,
            "authors": [org_name],
            "labels": [
                "misp-event",
                MISP_ANALYSIS_TO_LABEL.get(analysis_state, "initial"),
            ],
            "confidence": int(adjusted_confidence * 100),
            # Chain-of-custody extension fields
            "x_oi_source": self.source_label,
            "x_oi_misp_event_id": event_id,
            "x_oi_misp_uuid": event_uuid,
            "x_oi_reported_by": org_name,
            "x_oi_ingested_at": _now(),
            "x_oi_threat_level": threat_level,
            "x_oi_analysis_state": MISP_ANALYSIS_TO_LABEL.get(
                analysis_state, "initial"
            ),
        }
        stix_objects.append(event_note)

        prov = self.provenance_engine.create_record(
            stix_id=event_note["id"],
            source=self.source_label,
            reported_by=org_name,
            original_timestamp=f"{event_date}T00:00:00.000Z",
            trust_level=adjusted_confidence,
            feed_type="misp",
            misp_event_id=event_id,
            analysis_state=MISP_ANALYSIS_TO_LABEL.get(analysis_state, "initial"),
        )
        provenance_records.append(prov)

        # Process each MISP attribute
        attributes = event.get("Attribute", [])
        for attr in attributes:
            stix_obj = self._attribute_to_stix(
                attr, event_note["id"], adjusted_confidence, org_name, event_date
            )
            if stix_obj:
                stix_objects.append(stix_obj)
                attr_prov = self.provenance_engine.create_record(
                    stix_id=stix_obj["id"],
                    source=self.source_label,
                    reported_by=org_name,
                    original_timestamp=f"{event_date}T00:00:00.000Z",
                    trust_level=adjusted_confidence,
                    feed_type="misp",
                    misp_event_id=event_id,
                    analysis_state=MISP_ANALYSIS_TO_LABEL.get(
                        analysis_state, "initial"
                    ),
                    misp_attribute_uuid=attr.get("uuid", ""),
                    misp_category=attr.get("category", ""),
                )
                provenance_records.append(attr_prov)

        return stix_objects, provenance_records

    def _attribute_to_stix(
        self,
        attr: dict,
        parent_note_id: str,
        confidence: float,
        org_name: str,
        event_date: str,
    ) -> Optional[dict]:
        """
        Convert a single MISP attribute to the most appropriate STIX 2.1 object.
        IOC-type attributes become STIX indicators with pattern expressions.
        """
        attr_type = attr.get("type", "")
        attr_value = attr.get("value", "")
        attr_comment = attr.get("comment", "")
        attr_uuid = attr.get("uuid", str(uuid.uuid4()))

        if not attr_value:
            return None

        stix_type = MISP_TYPE_TO_STIX.get(attr_type)
        if not stix_type:
            return None  # Unsupported attribute type — skip silently

        created_ts = f"{event_date}T00:00:00.000Z"

        # Network and file IOCs → STIX indicator with pattern
        if stix_type == "indicator":
            pattern = self._build_indicator_pattern(attr_type, attr_value)
            if not pattern:
                return None
            return {
                "type": "indicator",
                "spec_version": "2.1",
                "id": _stix_id("indicator"),
                "created": created_ts,
                "modified": _now(),
                "name": f"{attr_type}: {attr_value}",
                "description": attr_comment or f"MISP attribute — {attr_type}",
                "pattern": pattern,
                "pattern_type": "stix",
                "valid_from": created_ts,
                "indicator_types": [self._indicator_type_from_misp(attr_type)],
                "confidence": int(confidence * 100),
                "labels": ["misp-attribute", attr_type],
                "object_marking_refs": [],
                # Chain-of-custody extension fields
                "x_oi_source": self.source_label,
                "x_oi_reported_by": org_name,
                "x_oi_ingested_at": _now(),
                "x_oi_misp_attribute_uuid": attr_uuid,
                "x_oi_misp_category": attr.get("category", ""),
                "x_oi_parent_event_ref": parent_note_id,
                "x_oi_to_ids": attr.get("to_ids", False),
            }

        elif stix_type == "threat-actor":
            return {
                "type": "threat-actor",
                "spec_version": "2.1",
                "id": _stix_id("threat-actor"),
                "created": created_ts,
                "modified": _now(),
                "name": attr_value,
                "description": attr_comment
                or f"Threat actor from MISP — {self.source_label}",
                "threat_actor_types": ["unknown"],
                "confidence": int(confidence * 100),
                "labels": ["misp-attribute", "threat-actor"],
                "x_oi_source": self.source_label,
                "x_oi_reported_by": org_name,
                "x_oi_ingested_at": _now(),
                "x_oi_misp_attribute_uuid": attr_uuid,
            }

        elif stix_type == "malware":
            return {
                "type": "malware",
                "spec_version": "2.1",
                "id": _stix_id("malware"),
                "created": created_ts,
                "modified": _now(),
                "name": attr_value,
                "description": attr_comment
                or f"Malware from MISP — {self.source_label}",
                "malware_types": ["unknown"],
                "is_family": False,
                "confidence": int(confidence * 100),
                "labels": ["misp-attribute", "malware"],
                "x_oi_source": self.source_label,
                "x_oi_reported_by": org_name,
                "x_oi_ingested_at": _now(),
                "x_oi_misp_attribute_uuid": attr_uuid,
            }

        elif stix_type == "vulnerability":
            return {
                "type": "vulnerability",
                "spec_version": "2.1",
                "id": _stix_id("vulnerability"),
                "created": created_ts,
                "modified": _now(),
                "name": attr_value,
                "description": attr_comment
                or f"Vulnerability from MISP — {self.source_label}",
                "confidence": int(confidence * 100),
                "labels": ["misp-attribute", "vulnerability"],
                "x_oi_source": self.source_label,
                "x_oi_reported_by": org_name,
                "x_oi_ingested_at": _now(),
                "x_oi_misp_attribute_uuid": attr_uuid,
            }

        elif stix_type == "campaign":
            return {
                "type": "campaign",
                "spec_version": "2.1",
                "id": _stix_id("campaign"),
                "created": created_ts,
                "modified": _now(),
                "name": attr_value,
                "description": attr_comment
                or f"Campaign from MISP — {self.source_label}",
                "confidence": int(confidence * 100),
                "labels": ["misp-attribute", "campaign"],
                "x_oi_source": self.source_label,
                "x_oi_reported_by": org_name,
                "x_oi_ingested_at": _now(),
                "x_oi_misp_attribute_uuid": attr_uuid,
            }

        return None

    @staticmethod
    def _build_indicator_pattern(attr_type: str, value: str) -> Optional[str]:
        """Build a STIX 2.1 patterning expression from a MISP attribute type/value."""
        patterns = {
            "ip-src": f"[network-traffic:src_ref.type = 'ipv4-addr' AND network-traffic:src_ref.value = '{value}']",
            "ip-dst": f"[network-traffic:dst_ref.type = 'ipv4-addr' AND network-traffic:dst_ref.value = '{value}']",
            "domain": f"[domain-name:value = '{value}']",
            "hostname": f"[domain-name:value = '{value}']",
            "url": f"[url:value = '{value}']",
            "md5": f"[file:hashes.MD5 = '{value}']",
            "sha1": f"[file:hashes.SHA-1 = '{value}']",
            "sha256": f"[file:hashes.SHA-256 = '{value}']",
            "filename": f"[file:name = '{value}']",
        }
        return patterns.get(attr_type)

    @staticmethod
    def _indicator_type_from_misp(attr_type: str) -> str:
        mapping = {
            "ip-src": "malicious-activity",
            "ip-dst": "malicious-activity",
            "domain": "malicious-activity",
            "hostname": "malicious-activity",
            "url": "malicious-activity",
            "md5": "malicious-activity",
            "sha1": "malicious-activity",
            "sha256": "malicious-activity",
            "filename": "malicious-activity",
        }
        return mapping.get(attr_type, "unknown")

    # ── Connection test ────────────────────────

    def test_connection(self) -> dict:
        """
        Verify connectivity to the MISP instance.
        Returns server version info or raises ConnectionError.
        """
        try:
            response = self._request("/servers/getPyMISPVersion")
            return {
                "status": "ok",
                "source": self.source_label,
                "misp_response": response,
            }
        except ConnectionError as e:
            return {"status": "error", "source": self.source_label, "error": str(e)}
