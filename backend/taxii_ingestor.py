"""
taxii_ingestor.py — Open Intelligence Lab v0.4.0
TAXII 2.1 Feed Ingestion Client

This is the subscriber side of the TAXII protocol — the complement to
taxii_server.py which serves as the publisher. Where taxii_server.py
exposes OI Lab's intelligence for Splunk/Sentinel/QRadar to pull,
taxii_ingestor.py pulls from external TAXII sources (MISP, OpenCTI,
commercial feeds) and ingests their STIX 2.1 objects into the graph.

TAXII 2.1 spec: https://docs.oasis-open.org/cti/taxii/v2.1/os/taxii-v2.1-os.html

Supported authentication:
  - API key (most MISP/OpenCTI TAXII endpoints)
  - HTTP Basic auth (some commercial feeds)
  - Bearer token

Author: Alborz Nazari
License: MIT
"""

import json
import logging
import uuid
import base64
import ssl
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Optional

from provenance import ProvenanceEngine, ProvenanceRecord

logger = logging.getLogger(__name__)


TAXII_CONTENT_TYPE = "application/taxii+json;version=2.1"
STIX_CONTENT_TYPE = "application/stix+json;version=2.1"

# Accept header required by TAXII 2.1 spec
TAXII_ACCEPT = f"{TAXII_CONTENT_TYPE}, {STIX_CONTENT_TYPE}"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _days_ago(days: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


# ─────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────


def _build_auth_header(
    api_key: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    bearer_token: Optional[str] = None,
) -> Optional[str]:
    """Return the appropriate Authorization header value."""
    if bearer_token:
        return f"Bearer {bearer_token}"
    if api_key:
        return api_key  # Many TAXII servers accept bare API key
    if username and password:
        creds = base64.b64encode(f"{username}:{password}".encode()).decode()
        return f"Basic {creds}"
    return None


# ─────────────────────────────────────────────
# TAXII Ingestor
# ─────────────────────────────────────────────


class TAXIIIngestor:
    """
    TAXII 2.1 client — pulls STIX 2.1 objects from external collections.

    This class handles:
    - TAXII server discovery (GET /taxii/)
    - Collection enumeration (GET /collections/)
    - Paginated object fetching with added_after filtering
    - Provenance stamping on every ingested object

    Usage:
        ingestor = TAXIIIngestor(
            server_url="https://otx.alienvault.com/taxii/",
            api_key="your-api-key",
            source_label="TAXII-AlienVault-OTX",
            verify_ssl=True,
        )
        collections = ingestor.discover_collections()
        stix_objects, provenance = ingestor.ingest_collection(
            collection_id=collections[0]["id"],
            added_after_days=7,
        )
    """

    def __init__(
        self,
        server_url: str,
        source_label: str,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        bearer_token: Optional[str] = None,
        verify_ssl: bool = True,
        timeout: int = 30,
        page_size: int = 100,
    ):
        self.server_url = server_url.rstrip("/")
        self.source_label = source_label
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.page_size = page_size
        self.auth_header = _build_auth_header(api_key, username, password, bearer_token)
        self.provenance_engine = ProvenanceEngine()
        self._api_root: Optional[str] = None

    # ── HTTP ───────────────────────────────────

    def _get(self, url: str, accept: str = TAXII_ACCEPT) -> dict:
        """
        Execute an authenticated TAXII GET request.
        TAXII 2.1 mandates HTTPS/TLS — all traffic is encrypted end-to-end.
        """
        req = urllib.request.Request(url)
        req.add_header("Accept", accept)
        if self.auth_header:
            req.add_header("Authorization", self.auth_header)

        ssl_ctx = ssl.create_default_context()
        if not self.verify_ssl:
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

        try:
            with urllib.request.urlopen(
                req, context=ssl_ctx, timeout=self.timeout
            ) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise ConnectionError(f"TAXII HTTP {e.code} at {url}: {body[:200]}") from e
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Cannot reach TAXII server {self.server_url}: {e.reason}"
            ) from e

    # ── Discovery ──────────────────────────────

    def discover(self) -> dict:
        """
        TAXII 2.1 Discovery — GET /taxii/
        Returns server title, description, and api_roots.
        """
        try:
            info = self._get(f"{self.server_url}/taxii/")
            logger.info(
                f"[TAXII] Discovered server: {info.get('title', 'Unknown')} "
                f"— {self.source_label}"
            )
            # Cache the first api_root for subsequent calls
            api_roots = info.get("api_roots", [])
            if api_roots:
                self._api_root = api_roots[0].rstrip("/")
            return info
        except ConnectionError as e:
            logger.error(f"[TAXII] Discovery failed for {self.source_label}: {e}")
            raise

    def discover_collections(self) -> list[dict]:
        """
        List all available collections on this TAXII server.
        Performs discovery first if api_root is not cached.
        """
        if not self._api_root:
            self.discover()

        url = f"{self._api_root}/collections/"
        try:
            data = self._get(url)
            collections = data.get("collections", [])
            logger.info(
                f"[TAXII] {len(collections)} collections found — {self.source_label}"
            )
            return collections
        except ConnectionError as e:
            logger.error(f"[TAXII] Collection discovery failed: {e}")
            return []

    # ── Ingestion ──────────────────────────────

    def ingest_collection(
        self,
        collection_id: str,
        added_after_days: Optional[int] = 7,
        max_objects: int = 1000,
        stix_types: Optional[list[str]] = None,
    ) -> tuple[list[dict], list[ProvenanceRecord]]:
        """
        Pull STIX 2.1 objects from a specific collection.

        Supports:
        - Temporal filtering via added_after (only pull new intelligence)
        - Type filtering via match[type]
        - Pagination (follows more=True until max_objects reached)

        Returns (validated_stix_objects, provenance_records).
        Objects that fail provenance validation are excluded from the first list
        but their rejection records are still present in provenance_records.
        """
        if not self._api_root:
            try:
                self.discover()
            except ConnectionError:
                return [], []

        base_url = f"{self._api_root}/collections/{collection_id}/objects/"
        params = [f"limit={self.page_size}"]

        if added_after_days is not None:
            params.append(f"added_after={_days_ago(added_after_days)}")
        if stix_types:
            for t in stix_types:
                params.append(f"match[type]={t}")

        url = base_url + "?" + "&".join(params)

        all_validated: list[dict] = []
        all_provenance: list[ProvenanceRecord] = []
        page = 0

        logger.info(
            f"[TAXII] Starting ingestion from collection {collection_id} "
            f"— {self.source_label}"
        )

        while url and len(all_validated) < max_objects:
            try:
                envelope = self._get(url, accept=STIX_CONTENT_TYPE)
            except ConnectionError as e:
                logger.error(f"[TAXII] Ingestion error on page {page}: {e}")
                break

            objects = envelope.get("objects", [])
            page += 1

            for obj in objects:
                validated, prov = self._process_object(obj, collection_id)
                all_provenance.append(prov)
                if validated:
                    all_validated.append(validated)

            logger.debug(
                f"[TAXII] Page {page}: {len(objects)} objects fetched, "
                f"{len(all_validated)} validated so far"
            )

            # TAXII 2.1 pagination: follow next page if more=True
            has_more = envelope.get("more", False)
            next_url = envelope.get("next")
            if has_more and next_url:
                url = (
                    next_url
                    if next_url.startswith("http")
                    else f"{self._api_root}{next_url}"
                )
            else:
                break

        logger.info(
            f"[TAXII] Completed ingestion — {len(all_validated)} validated objects "
            f"from {self.source_label} collection {collection_id}"
        )
        return all_validated, all_provenance

    def ingest_all_collections(
        self,
        added_after_days: int = 7,
        max_per_collection: int = 500,
    ) -> tuple[list[dict], list[ProvenanceRecord]]:
        """
        Discover and ingest from all readable collections on this server.
        Skips write-only collections.
        """
        collections = self.discover_collections()
        all_validated: list[dict] = []
        all_provenance: list[ProvenanceRecord] = []

        for col in collections:
            if not col.get("can_read", True):
                continue
            validated, provenance = self.ingest_collection(
                collection_id=col["id"],
                added_after_days=added_after_days,
                max_objects=max_per_collection,
            )
            all_validated.extend(validated)
            all_provenance.extend(provenance)

        return all_validated, all_provenance

    # ── Object processing ──────────────────────

    def _process_object(
        self,
        stix_obj: dict,
        collection_id: str,
    ) -> tuple[Optional[dict], ProvenanceRecord]:
        """
        Apply provenance validation to a single incoming STIX object.

        Returns (stamped_object_or_None, provenance_record).
        If the object fails validation, the first element is None.
        """
        stix_id = stix_obj.get("id", f"unknown--{uuid.uuid4()}")
        created = stix_obj.get("created", _now())
        confidence_int = stix_obj.get("confidence", 50)
        trust_level = max(0.0, min(1.0, confidence_int / 100.0))

        prov = self.provenance_engine.create_record(
            stix_id=stix_id,
            source=self.source_label,
            reported_by=stix_obj.get("x_oi_reported_by", self.source_label),
            original_timestamp=created,
            trust_level=trust_level,
            feed_type="taxii",
            taxii_collection_id=collection_id,
            taxii_server_url=self.server_url,
        )

        stamped = self.provenance_engine.validate_and_stamp(stix_obj, prov)
        return stamped, prov

    # ── Connection test ────────────────────────

    def test_connection(self) -> dict:
        """Verify connectivity and return discovery metadata."""
        try:
            info = self.discover()
            return {
                "status": "ok",
                "source": self.source_label,
                "server_title": info.get("title", "Unknown"),
                "api_roots": info.get("api_roots", []),
            }
        except ConnectionError as e:
            return {"status": "error", "source": self.source_label, "error": str(e)}

    def get_provenance_summary(self) -> dict:
        return self.provenance_engine.get_summary()
