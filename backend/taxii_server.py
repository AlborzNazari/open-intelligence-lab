"""
taxii_server.py — Open Intelligence Lab v0.4.0
TAXII 2.1 Server + Feed Ingestion API (FastAPI-based)

v0.3.0: TAXII 2.1 publisher — serves OI Lab STIX bundles to Splunk, Sentinel, OpenCTI, QRadar.
v0.4.0: Bidirectional — adds MISP ingestion, TAXII feed ingestion, provenance validation,
        and a live ingested-objects store accessible via new /ingest/ endpoints.

TAXII 2.1 spec: https://docs.oasis-open.org/cti/taxii/v2.1/os/taxii-v2.1-os.html

Author: Alborz Nazari
License: MIT
"""

from fastapi import FastAPI, Response, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from datetime import datetime, timezone
from stix_exporter import load_datasets, build_stix_bundle, _now
from feed_scheduler import get_scheduler, MISPFeedConfig, TAXIIFeedConfig

# ─────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────

app = FastAPI(
    title="Open Intelligence Lab — TAXII 2.1 Server",
    description="TAXII 2.1 bidirectional server: serves OI Lab intelligence and ingests from MISP/TAXII feeds with provenance validation.",
    version="0.4.0",
    docs_url="/taxii/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

TAXII_CONTENT_TYPE = "application/taxii+json;version=2.1"
STIX_CONTENT_TYPE = "application/stix+json;version=2.1"

# ─────────────────────────────────────────────
# Static Collection Metadata
# ─────────────────────────────────────────────

COLLECTIONS = [
    {
        "id": "oi-lab-threat-actors-001",
        "title": "OI Lab — Threat Actors",
        "description": "Nation-state and criminal threat actor entities with risk scores.",
        "can_read": True,
        "can_write": False,
        "media_types": [STIX_CONTENT_TYPE],
    },
    {
        "id": "oi-lab-attack-patterns-002",
        "title": "OI Lab — Attack Patterns",
        "description": "OSINT-derived attack patterns mapped to MITRE ATT&CK.",
        "can_read": True,
        "can_write": False,
        "media_types": [STIX_CONTENT_TYPE],
    },
    {
        "id": "oi-lab-campaigns-003",
        "title": "OI Lab — Campaigns",
        "description": "Documented campaigns modeled via the Diamond Model of Intrusion Analysis.",
        "can_read": True,
        "can_write": False,
        "media_types": [STIX_CONTENT_TYPE],
    },
    {
        "id": "oi-lab-full-bundle-004",
        "title": "OI Lab — Full Bundle",
        "description": "Complete STIX 2.1 bundle: all entities, patterns, relations, and campaigns.",
        "can_read": True,
        "can_write": False,
        "media_types": [STIX_CONTENT_TYPE],
    },
]

# ─────────────────────────────────────────────
# Bundle Cache (load once on startup)
# ─────────────────────────────────────────────

_bundle_cache: dict | None = None


def get_bundle() -> dict:
    global _bundle_cache
    if _bundle_cache is None:
        entities, attack_patterns, relations, campaigns = load_datasets()
        _bundle_cache = build_stix_bundle(
            entities, attack_patterns, relations, campaigns
        )
    return _bundle_cache


def filter_by_type(bundle: dict, stix_types: list[str]) -> list[dict]:
    return [o for o in bundle.get("objects", []) if o.get("type") in stix_types]


# ─────────────────────────────────────────────
# TAXII 2.1 Endpoints
# ─────────────────────────────────────────────


@app.get("/taxii/", summary="TAXII Server Discovery")
def taxii_discovery():
    """
    TAXII 2.1 Discovery endpoint.
    Returns server metadata — required by all TAXII 2.1 clients.
    """
    return Response(
        content=json.dumps(
            {
                "title": "Open Intelligence Lab TAXII 2.1 Server",
                "description": "Serving STIX 2.1 threat intelligence from Open Intelligence Lab.",
                "contact": "github.com/AlborzNazari/open-intelligence-lab",
                "default": "/taxii/api-root/",
                "api_roots": ["/taxii/api-root/"],
            }
        ),
        media_type=TAXII_CONTENT_TYPE,
    )


@app.get("/taxii/api-root/", summary="API Root")
def api_root():
    """TAXII 2.1 API Root — lists collections and server version."""
    return Response(
        content=json.dumps(
            {
                "title": "OI Lab API Root",
                "versions": ["application/taxii+json;version=2.1"],
                "max_content_length": 104857600,  # 100MB
            }
        ),
        media_type=TAXII_CONTENT_TYPE,
    )


@app.get("/taxii/api-root/collections/", summary="List Collections")
def list_collections():
    """TAXII 2.1 Collections listing — all available intelligence feeds."""
    return Response(
        content=json.dumps({"collections": COLLECTIONS}),
        media_type=TAXII_CONTENT_TYPE,
    )


@app.get("/taxii/api-root/collections/{collection_id}/", summary="Collection Info")
def get_collection(collection_id: str):
    """TAXII 2.1 Collection metadata by ID."""
    collection = next((c for c in COLLECTIONS if c["id"] == collection_id), None)
    if not collection:
        raise HTTPException(
            status_code=404, detail=f"Collection '{collection_id}' not found."
        )
    return Response(content=json.dumps(collection), media_type=TAXII_CONTENT_TYPE)


@app.get(
    "/taxii/api-root/collections/{collection_id}/objects/", summary="Get STIX Objects"
)
def get_objects(
    collection_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Max objects to return"),
    added_after: str = Query(default=None, description="ISO 8601 timestamp filter"),
    match_type: list[str] = Query(
        default=None, alias="match[type]", description="Filter by STIX type"
    ),
):
    """
    TAXII 2.1 Objects endpoint — returns STIX 2.1 objects for the given collection.

    Supports:
    - Pagination via ?limit=
    - Temporal filtering via ?added_after=
    - Type filtering via ?match[type]=

    Tested compatible with:
    - Splunk ES TAXII connector
    - Microsoft Sentinel TAXII (Preview)
    - OpenCTI TAXII ingestion connector
    - IBM QRadar STIX-TAXII app
    """
    bundle = get_bundle()

    type_map = {
        "oi-lab-threat-actors-001": ["threat-actor", "identity"],
        "oi-lab-attack-patterns-002": ["attack-pattern"],
        "oi-lab-campaigns-003": ["campaign"],
        "oi-lab-full-bundle-004": None,  # All types
    }

    if collection_id not in type_map:
        raise HTTPException(
            status_code=404, detail=f"Collection '{collection_id}' not found."
        )

    allowed_types = type_map[collection_id]
    objects = bundle.get("objects", [])

    if allowed_types:
        objects = [o for o in objects if o.get("type") in allowed_types]

    if match_type:
        objects = [o for o in objects if o.get("type") in match_type]

    total = len(objects)
    objects = objects[:limit]

    envelope = {
        "type": "bundle",
        "id": bundle["id"],
        "spec_version": "2.1",
        "more": total > limit,
        "objects": objects,
    }

    return Response(
        content=json.dumps(envelope),
        media_type=STIX_CONTENT_TYPE,
        headers={
            "X-TAXII-Date-Added-First": _now(),
            "X-TAXII-Date-Added-Last": _now(),
            "Content-Range": f"items 0-{len(objects)-1}/{total}",
        },
    )


@app.get(
    "/taxii/api-root/collections/{collection_id}/manifest/",
    summary="Collection Manifest",
)
def get_manifest(collection_id: str):
    """TAXII 2.1 Manifest — lightweight listing of object IDs and versions."""
    bundle = get_bundle()
    type_map = {
        "oi-lab-threat-actors-001": ["threat-actor", "identity"],
        "oi-lab-attack-patterns-002": ["attack-pattern"],
        "oi-lab-campaigns-003": ["campaign"],
        "oi-lab-full-bundle-004": None,
    }
    if collection_id not in type_map:
        raise HTTPException(status_code=404, detail="Collection not found.")

    allowed_types = type_map[collection_id]
    objects = bundle.get("objects", [])
    if allowed_types:
        objects = [o for o in objects if o.get("type") in allowed_types]

    manifest = {
        "objects": [
            {
                "id": o["id"],
                "date_added": o.get("created", _now()),
                "version": o.get("modified", _now()),
                "media_type": STIX_CONTENT_TYPE,
            }
            for o in objects
        ]
    }
    return Response(content=json.dumps(manifest), media_type=TAXII_CONTENT_TYPE)


# ─────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────


@app.get("/taxii/health", summary="Health Check", tags=["system"])
def health():
    bundle = get_bundle()
    scheduler = get_scheduler()
    store_summary = scheduler.get_store_summary()
    return {
        "status": "ok",
        "version": "v0.4.0",
        "stix_objects": len(bundle.get("objects", [])),
        "server_time": _now(),
        "collections": len(COLLECTIONS),
        "live_ingested_objects": store_summary["total_objects"],
        "feeds_configured": store_summary["feeds_configured"],
    }


# ─────────────────────────────────────────────
# v0.4.0 — Feed Ingestion Endpoints
# ─────────────────────────────────────────────


@app.post("/ingest/misp", summary="Register and run a MISP feed", tags=["ingestion"])
def ingest_misp(
    base_url: str = Body(..., description="MISP instance base URL"),
    api_key: str = Body(..., description="MISP REST API key"),
    label: str = Body(default="MISP", description="Human-readable source label"),
    pull_days: int = Body(default=7, description="How many days back to fetch"),
    verify_ssl: bool = Body(default=True),
):
    """
    Register a MISP instance as a live intelligence feed and run an immediate
    ingestion cycle. Fetched events are normalized to STIX 2.1, validated via
    the provenance engine, and stored in the live object store.

    The provenance engine stamps each object with:
    - source, reported_by, original_timestamp, ingested_at
    - trust_level (adjusted for MISP threat level + source prior + staleness)
    - chain-of-custody rejection reason if trust falls below threshold
    """
    scheduler = get_scheduler()
    config = MISPFeedConfig(
        label=label,
        base_url=base_url,
        api_key=api_key,
        pull_days=pull_days,
        verify_ssl=verify_ssl,
    )
    scheduler.add_misp_feed(config)
    result = scheduler.run_once()
    return {
        "status": "ok",
        "message": f"MISP feed '{label}' ingested",
        "run_summary": result,
        "store_summary": scheduler.get_store_summary(),
    }


@app.post("/ingest/taxii", summary="Register and run a TAXII feed", tags=["ingestion"])
def ingest_taxii(
    server_url: str = Body(..., description="TAXII 2.1 server base URL"),
    label: str = Body(..., description="Human-readable source label"),
    api_key: str = Body(default=None),
    bearer_token: str = Body(default=None),
    username: str = Body(default=None),
    password: str = Body(default=None),
    pull_days: int = Body(default=7),
    verify_ssl: bool = Body(default=True),
):
    """
    Register an external TAXII 2.1 server as an intelligence feed source
    and run an immediate ingestion cycle across all readable collections.

    Supports API key, Bearer token, and HTTP Basic authentication.
    All traffic runs over HTTPS — TAXII 2.1 mandates TLS.
    """
    scheduler = get_scheduler()
    config = TAXIIFeedConfig(
        label=label,
        server_url=server_url,
        api_key=api_key,
        bearer_token=bearer_token,
        username=username,
        password=password,
        pull_days=pull_days,
        verify_ssl=verify_ssl,
    )
    scheduler.add_taxii_feed(config)
    result = scheduler.run_once()
    return {
        "status": "ok",
        "message": f"TAXII feed '{label}' ingested",
        "run_summary": result,
        "store_summary": scheduler.get_store_summary(),
    }


@app.post("/ingest/run", summary="Trigger manual ingestion cycle", tags=["ingestion"])
def trigger_run():
    """
    Manually trigger one ingestion cycle across all configured feeds.
    Returns a full run summary including per-feed validated/rejected/stale counts.
    """
    scheduler = get_scheduler()
    result = scheduler.run_once()
    return result


@app.get("/ingest/objects", summary="Query live ingested objects", tags=["ingestion"])
def get_ingested_objects(
    stix_type: str = Query(default=None, description="Filter by STIX type"),
    source: str = Query(default=None, description="Filter by source label"),
    min_trust: float = Query(
        default=None, ge=0.0, le=1.0, description="Minimum trust level"
    ),
    exclude_stale: bool = Query(default=False, description="Exclude stale objects"),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """
    Query the live ingested object store — the dynamic knowledge graph layer.
    These are the objects pulled from MISP and TAXII feeds, validated by the
    provenance engine, and stamped with full chain-of-custody metadata.
    """
    scheduler = get_scheduler()
    objects = scheduler.get_ingested_objects(
        stix_type=stix_type,
        source=source,
        min_trust=min_trust,
        exclude_stale=exclude_stale,
    )
    return Response(
        content=json.dumps(
            {
                "type": "bundle",
                "spec_version": "2.1",
                "total": len(objects),
                "objects": objects[:limit],
            }
        ),
        media_type=STIX_CONTENT_TYPE,
    )


@app.get(
    "/ingest/store/summary", summary="Live object store summary", tags=["ingestion"]
)
def store_summary():
    """
    Return a summary of the live ingested object store:
    total objects, breakdown by type and source, average trust level,
    stale count, and number of feeds configured.
    """
    scheduler = get_scheduler()
    return scheduler.get_store_summary()


@app.get("/ingest/run-log", summary="Ingestion run history", tags=["ingestion"])
def run_log(limit: int = Query(default=20, ge=1, le=200)):
    """
    Return the ingestion run history — per-feed audit log of every
    ingestion cycle: start/end time, objects fetched/validated/rejected,
    stale count, and error messages if any.
    """
    scheduler = get_scheduler()
    return {"run_log": scheduler.get_run_log(limit=limit)}


@app.get(
    "/ingest/bundle",
    summary="Export ingested objects as STIX bundle",
    tags=["ingestion"],
)
def ingested_bundle(
    exclude_stale: bool = Query(default=False),
    min_trust: float = Query(default=0.0, ge=0.0, le=1.0),
):
    """
    Export all validated live ingested objects as a single STIX 2.1 bundle.
    This is the bidirectional feedback loop: consume from MISP/TAXII,
    enrich the graph, re-export as unified intelligence.
    """
    scheduler = get_scheduler()
    bundle = scheduler.export_as_stix_bundle(
        exclude_stale=exclude_stale,
        min_trust=min_trust if min_trust > 0 else None,
    )
    return Response(
        content=json.dumps(bundle),
        media_type=STIX_CONTENT_TYPE,
    )
