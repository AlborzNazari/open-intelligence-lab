"""
taxii_server.py — Open Intelligence Lab v0.3.0
TAXII 2.1 Server (FastAPI-based)

Exposes Open Intelligence Lab's STIX 2.1 bundles via a TAXII 2.1-compliant REST API.
Platforms like Splunk, Sentinel, OpenCTI, and QRadar can poll this server
as a native TAXII feed — no custom integration needed on their end.

TAXII 2.1 spec: https://docs.oasis-open.org/cti/taxii/v2.1/os/taxii-v2.1-os.html

Author: Alborz Nazari
License: MIT
"""

from fastapi import FastAPI, Response, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from datetime import datetime, timezone
from stix_exporter import load_datasets, build_stix_bundle, _now

# ─────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────

app = FastAPI(
    title="Open Intelligence Lab — TAXII 2.1 Server",
    description="TAXII 2.1 endpoint serving STIX 2.1 threat intelligence from Open Intelligence Lab.",
    version="0.3.0",
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
        _bundle_cache = build_stix_bundle(entities, attack_patterns, relations, campaigns)
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
        content=json.dumps({
            "title": "Open Intelligence Lab TAXII 2.1 Server",
            "description": "Serving STIX 2.1 threat intelligence from Open Intelligence Lab.",
            "contact": "github.com/AlborzNazari/open-intelligence-lab",
            "default": "/taxii/api-root/",
            "api_roots": ["/taxii/api-root/"],
        }),
        media_type=TAXII_CONTENT_TYPE,
    )


@app.get("/taxii/api-root/", summary="API Root")
def api_root():
    """TAXII 2.1 API Root — lists collections and server version."""
    return Response(
        content=json.dumps({
            "title": "OI Lab API Root",
            "versions": ["application/taxii+json;version=2.1"],
            "max_content_length": 104857600,  # 100MB
        }),
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
        raise HTTPException(status_code=404, detail=f"Collection '{collection_id}' not found.")
    return Response(content=json.dumps(collection), media_type=TAXII_CONTENT_TYPE)


@app.get("/taxii/api-root/collections/{collection_id}/objects/", summary="Get STIX Objects")
def get_objects(
    collection_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Max objects to return"),
    added_after: str = Query(default=None, description="ISO 8601 timestamp filter"),
    match_type: list[str] = Query(default=None, alias="match[type]", description="Filter by STIX type"),
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
        raise HTTPException(status_code=404, detail=f"Collection '{collection_id}' not found.")

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


@app.get("/taxii/api-root/collections/{collection_id}/manifest/", summary="Collection Manifest")
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
    return {
        "status": "ok",
        "version": "v0.3.0",
        "stix_objects": len(bundle.get("objects", [])),
        "server_time": _now(),
        "collections": len(COLLECTIONS),
    }
