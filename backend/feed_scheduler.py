"""
feed_scheduler.py — Open Intelligence Lab v0.4.0
Intelligence Feed Orchestrator

Manages periodic ingestion from configured MISP instances and TAXII feeds.
This is the engine that makes the knowledge graph live — running background
jobs that pull fresh intelligence, validate provenance, and push new objects
into the graph on a schedule.

The scheduler maintains:
  - A registry of configured feed sources (MISP + TAXII)
  - Per-feed run history and last-success timestamps
  - A unified ingestion log for audit purposes
  - The merged, provenance-stamped object store

In production: run as a background thread alongside the FastAPI server.
In development: call run_once() manually from demo.py or the API.

Author: Alborz Nazari
License: MIT
"""

import logging
import threading
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

from misp_client import MISPClient
from taxii_ingestor import TAXIIIngestor
from provenance import ProvenanceRecord

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


# ─────────────────────────────────────────────
# Feed Configuration
# ─────────────────────────────────────────────


@dataclass
class MISPFeedConfig:
    """Configuration for a single MISP source."""

    label: str  # Human-readable label, e.g. "MISP-CERT-EU"
    base_url: str  # https://misp.example.org
    api_key: str  # MISP auth key
    pull_days: int = 7  # How many days back to fetch on each run
    limit: int = 200  # Max events per run
    verify_ssl: bool = True
    enabled: bool = True


@dataclass
class TAXIIFeedConfig:
    """Configuration for a single TAXII 2.1 feed source."""

    label: str  # Human-readable label, e.g. "TAXII-OpenCTI"
    server_url: str  # https://opencti.example.org/taxii/
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    bearer_token: Optional[str] = None
    pull_days: int = 7
    max_per_collection: int = 500
    collection_ids: Optional[list] = None  # None = ingest all readable collections
    verify_ssl: bool = True
    enabled: bool = True


# ─────────────────────────────────────────────
# Run Record
# ─────────────────────────────────────────────


@dataclass
class FeedRunRecord:
    """Audit log entry for a single feed ingestion run."""

    run_id: str
    feed_label: str
    feed_type: str  # "misp" | "taxii"
    started_at: str
    completed_at: Optional[str]
    status: str  # "running" | "success" | "error"
    objects_fetched: int = 0
    objects_validated: int = 0
    objects_rejected: int = 0
    stale_objects: int = 0
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────
# Feed Scheduler
# ─────────────────────────────────────────────


class FeedScheduler:
    """
    Orchestrates periodic intelligence ingestion from MISP and TAXII feeds.

    Maintains an in-memory object store of all validated, provenance-stamped
    STIX objects ingested across all feeds. This store is the live data layer
    that backs the dynamic knowledge graph — making OI Lab bidirectional:
    consume → enrich → export.

    Thread safety: the object store and run log are protected by a lock.
    """

    def __init__(self):
        self._misp_feeds: list[MISPFeedConfig] = []
        self._taxii_feeds: list[TAXIIFeedConfig] = []
        self._object_store: dict[str, dict] = {}  # stix_id → stamped STIX object
        self._provenance_store: dict[str, dict] = {}  # stix_id → provenance record dict
        self._run_log: list[FeedRunRecord] = []
        self._lock = threading.Lock()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ── Feed registration ──────────────────────

    def add_misp_feed(self, config: MISPFeedConfig) -> None:
        self._misp_feeds.append(config)
        logger.info(f"[Scheduler] Registered MISP feed: {config.label}")

    def add_taxii_feed(self, config: TAXIIFeedConfig) -> None:
        self._taxii_feeds.append(config)
        logger.info(f"[Scheduler] Registered TAXII feed: {config.label}")

    # ── Manual / scheduled run ─────────────────

    def run_once(self) -> dict:
        """
        Run a single ingestion cycle across all configured feeds.
        Blocks until all feeds are processed. Safe to call manually.
        Returns a summary of the run.
        """
        logger.info("[Scheduler] Starting ingestion cycle")
        run_summary = {
            "cycle_id": str(uuid.uuid4()),
            "started_at": _now(),
            "feeds_processed": 0,
            "total_fetched": 0,
            "total_validated": 0,
            "total_rejected": 0,
            "feed_results": [],
        }

        # MISP feeds
        for config in self._misp_feeds:
            if not config.enabled:
                continue
            result = self._run_misp_feed(config)
            run_summary["feeds_processed"] += 1
            run_summary["total_fetched"] += result.objects_fetched
            run_summary["total_validated"] += result.objects_validated
            run_summary["total_rejected"] += result.objects_rejected
            run_summary["feed_results"].append(result.to_dict())

        # TAXII feeds
        for config in self._taxii_feeds:
            if not config.enabled:
                continue
            result = self._run_taxii_feed(config)
            run_summary["feeds_processed"] += 1
            run_summary["total_fetched"] += result.objects_fetched
            run_summary["total_validated"] += result.objects_validated
            run_summary["total_rejected"] += result.objects_rejected
            run_summary["feed_results"].append(result.to_dict())

        run_summary["completed_at"] = _now()
        run_summary["object_store_size"] = len(self._object_store)
        logger.info(
            f"[Scheduler] Cycle complete — "
            f"{run_summary['total_validated']} objects validated across "
            f"{run_summary['feeds_processed']} feeds"
        )
        return run_summary

    def start_background(self, interval_seconds: int = 3600) -> None:
        """
        Start a background thread that runs ingestion every interval_seconds.
        Default: hourly. Does not block the caller.
        """
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            logger.warning("[Scheduler] Background scheduler already running")
            return

        self._stop_event.clear()

        def _loop():
            logger.info(
                f"[Scheduler] Background scheduler started — "
                f"interval: {interval_seconds}s"
            )
            while not self._stop_event.is_set():
                try:
                    self.run_once()
                except Exception as e:
                    logger.error(f"[Scheduler] Unhandled error in ingestion cycle: {e}")
                self._stop_event.wait(timeout=interval_seconds)
            logger.info("[Scheduler] Background scheduler stopped")

        self._scheduler_thread = threading.Thread(target=_loop, daemon=True)
        self._scheduler_thread.start()

    def stop_background(self) -> None:
        """Signal the background scheduler to stop after the current cycle."""
        self._stop_event.set()

    # ── Feed runners ───────────────────────────

    def _run_misp_feed(self, config: MISPFeedConfig) -> FeedRunRecord:
        run = FeedRunRecord(
            run_id=str(uuid.uuid4()),
            feed_label=config.label,
            feed_type="misp",
            started_at=_now(),
            completed_at=None,
            status="running",
        )
        with self._lock:
            self._run_log.append(run)

        logger.info(f"[Scheduler] Running MISP feed: {config.label}")

        try:
            client = MISPClient(
                base_url=config.base_url,
                api_key=config.api_key,
                source_label=config.label,
                verify_ssl=config.verify_ssl,
            )
            stix_objects, provenance_records = client.fetch_recent_events(
                days=config.pull_days,
                limit=config.limit,
            )
            self._merge_results(stix_objects, provenance_records)

            run.objects_fetched = len(stix_objects) + len(
                [p for p in provenance_records if not p.passed_validation]
            )
            run.objects_validated = len(stix_objects)
            run.objects_rejected = len(
                [p for p in provenance_records if not p.passed_validation]
            )
            run.stale_objects = len([p for p in provenance_records if p.is_stale])
            run.status = "success"

        except Exception as e:
            run.status = "error"
            run.error_message = str(e)
            logger.error(f"[Scheduler] MISP feed {config.label} failed: {e}")

        run.completed_at = _now()
        return run

    def _run_taxii_feed(self, config: TAXIIFeedConfig) -> FeedRunRecord:
        run = FeedRunRecord(
            run_id=str(uuid.uuid4()),
            feed_label=config.label,
            feed_type="taxii",
            started_at=_now(),
            completed_at=None,
            status="running",
        )
        with self._lock:
            self._run_log.append(run)

        logger.info(f"[Scheduler] Running TAXII feed: {config.label}")

        try:
            ingestor = TAXIIIngestor(
                server_url=config.server_url,
                source_label=config.label,
                api_key=config.api_key,
                username=config.username,
                password=config.password,
                bearer_token=config.bearer_token,
                verify_ssl=config.verify_ssl,
            )

            if config.collection_ids:
                all_validated: list[dict] = []
                all_provenance: list[ProvenanceRecord] = []
                for col_id in config.collection_ids:
                    validated, provenance = ingestor.ingest_collection(
                        collection_id=col_id,
                        added_after_days=config.pull_days,
                        max_objects=config.max_per_collection,
                    )
                    all_validated.extend(validated)
                    all_provenance.extend(provenance)
            else:
                all_validated, all_provenance = ingestor.ingest_all_collections(
                    added_after_days=config.pull_days,
                    max_per_collection=config.max_per_collection,
                )

            self._merge_results(all_validated, all_provenance)

            prov_summary = ingestor.get_provenance_summary()
            run.objects_fetched = prov_summary.get("total_records", 0)
            run.objects_validated = prov_summary.get("accepted", 0)
            run.objects_rejected = prov_summary.get("rejected", 0)
            run.stale_objects = prov_summary.get("stale_flagged", 0)
            run.status = "success"

        except Exception as e:
            run.status = "error"
            run.error_message = str(e)
            logger.error(f"[Scheduler] TAXII feed {config.label} failed: {e}")

        run.completed_at = _now()
        return run

    # ── Object store management ────────────────

    def _merge_results(
        self,
        stix_objects: list[dict],
        provenance_records: list[ProvenanceRecord],
    ) -> None:
        """
        Merge validated STIX objects and their provenance records into the store.
        Uses STIX ID as the deduplication key — newer ingestion overwrites older.
        Thread-safe.
        """
        prov_by_stix_id = {p.stix_id: p for p in provenance_records}

        with self._lock:
            for obj in stix_objects:
                stix_id = obj.get("id", "")
                if stix_id:
                    self._object_store[stix_id] = obj
                    prov = prov_by_stix_id.get(stix_id)
                    if prov:
                        self._provenance_store[stix_id] = prov.to_dict()

    def get_ingested_objects(
        self,
        stix_type: Optional[str] = None,
        source: Optional[str] = None,
        min_trust: Optional[float] = None,
        exclude_stale: bool = False,
    ) -> list[dict]:
        """
        Query the live object store with optional filters.
        This is the data layer for the dynamic knowledge graph.
        """
        with self._lock:
            objects = list(self._object_store.values())

        if stix_type:
            objects = [o for o in objects if o.get("type") == stix_type]
        if source:
            objects = [o for o in objects if o.get("x_oi_source", "") == source]
        if min_trust is not None:
            objects = [
                o for o in objects if o.get("x_oi_trust_level", 0.0) >= min_trust
            ]
        if exclude_stale:
            objects = [o for o in objects if not o.get("x_oi_is_stale", False)]

        return objects

    def get_store_summary(self) -> dict:
        """Return a summary of the current live object store state."""
        with self._lock:
            objects = list(self._object_store.values())
            prov_records = list(self._provenance_store.values())

        by_type: dict[str, int] = {}
        by_source: dict[str, int] = {}
        stale_count = 0
        trust_sum = 0.0

        for obj in objects:
            obj_type = obj.get("type", "unknown")
            source = obj.get("x_oi_source", "unknown")
            by_type[obj_type] = by_type.get(obj_type, 0) + 1
            by_source[source] = by_source.get(source, 0) + 1
            trust_sum += obj.get("x_oi_trust_level", 0.0)
            if obj.get("x_oi_is_stale", False):
                stale_count += 1

        return {
            "total_objects": len(objects),
            "stale_objects": stale_count,
            "average_trust_level": (
                round(trust_sum / len(objects), 4) if objects else 0.0
            ),
            "by_type": by_type,
            "by_source": by_source,
            "total_provenance_records": len(prov_records),
            "feeds_configured": len(self._misp_feeds) + len(self._taxii_feeds),
            "run_log_entries": len(self._run_log),
        }

    def get_run_log(self, limit: int = 50) -> list[dict]:
        """Return the most recent ingestion run records."""
        with self._lock:
            return [r.to_dict() for r in self._run_log[-limit:]]

    def export_as_stix_bundle(self, **query_kwargs) -> dict:
        """
        Export the live ingested object store as a STIX 2.1 bundle.
        Merges with the static graph data for a unified export.
        """
        objects = self.get_ingested_objects(**query_kwargs)
        return {
            "type": "bundle",
            "id": f"bundle--{uuid.uuid4()}",
            "spec_version": "2.1",
            "objects": objects,
        }


# ─────────────────────────────────────────────
# Singleton — shared across the FastAPI app
# ─────────────────────────────────────────────

_scheduler_instance: Optional[FeedScheduler] = None


def get_scheduler() -> FeedScheduler:
    """Return the global FeedScheduler singleton."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = FeedScheduler()
    return _scheduler_instance
