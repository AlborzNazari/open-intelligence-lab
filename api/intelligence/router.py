"""
api/intelligence/router.py  —  v0.4.0

Enriched Swagger UI:
- /analyze/{entity_id}  — dropdown of all known entity IDs with examples
- /entities             — full filter controls with type enum, risk range, search
- /graph/summary        — graph-level stats
- /graph/edges          — all edges for visualization
- /entities/ids         — bare ID list for programmatic use
"""

from __future__ import annotations
from typing import Optional, Literal
from fastapi import APIRouter, HTTPException, Query, Path
from api.intelligence.service import (
    analyze_entity,
    list_entities,
    get_graph_summary,
    get_graph_edges,
)

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])

# ── All known entity IDs — shown as examples in Swagger UI ───────────────────
_ENTITY_EXAMPLES = {
    "APT28 (Threat Actor)": {
        "summary": "APT28 — Russian GRU nation-state actor",
        "value": "TA-001",
    },
    "APT29 (Threat Actor)": {
        "summary": "APT29 — SVR espionage group (Cozy Bear)",
        "value": "TA-002",
    },
    "APT41 (Threat Actor)": {
        "summary": "APT41 — Chinese dual espionage + cybercrime",
        "value": "TA-003",
    },
    "Lazarus Group (Threat Actor)": {
        "summary": "Lazarus Group — North Korean state actor",
        "value": "TA-004",
    },
    "LockBit (Threat Actor)": {
        "summary": "LockBit — RaaS ransomware group",
        "value": "TA-005",
    },
    "Cl0p (Threat Actor)": {
        "summary": "Cl0p — financially motivated ransomware",
        "value": "TA-006",
    },
    "KillNet (Threat Actor)": {
        "summary": "KillNet — pro-Russian hacktivist DDoS collective",
        "value": "TA-007",
    },
    "X-Agent (Malware)": {
        "summary": "X-Agent — APT28 modular spyware",
        "value": "MA-001",
    },
    "SUNBURST (Malware)": {
        "summary": "SUNBURST — SolarWinds supply-chain backdoor",
        "value": "MA-003",
    },
    "LockBit Ransomware (Malware)": {
        "summary": "LockBit Ransomware — polymorphic encryptor",
        "value": "MA-007",
    },
    "APT28 C2 Cluster (Infrastructure)": {
        "summary": "APT28 Primary C2 Cluster",
        "value": "INF-001",
    },
    "CVE-2023-34362 (Vulnerability)": {
        "summary": "MOVEit Transfer critical SQLi — CVSS 9.8",
        "value": "VUL-001",
    },
    "CVE-2024-3400 (Vulnerability)": {
        "summary": "PAN-OS command injection zero-day — CVSS 10.0",
        "value": "VUL-002",
    },
    "Healthcare Sector": {
        "summary": "Healthcare — high-value ransomware target sector",
        "value": "SECTOR-001",
    },
    "Financial Services Sector": {
        "summary": "Financial Services — espionage + fraud target",
        "value": "SECTOR-002",
    },
    "Government & Defense Sector": {
        "summary": "Government & Defense — primary nation-state target",
        "value": "SECTOR-003",
    },
}


@router.get(
    "/analyze/{entity_id}",
    summary="Analyze a threat entity",
    description=(
        "Returns a full risk analysis for a single entity: risk score, "
        "MITRE ATT&CK technique mapping, CIA triad impact, connected neighbors, "
        "and a plain-language explanation.\n\n"
        "**Select an example from the dropdown** or type any entity ID directly "
        "(e.g. `TA-001`, `MA-003`, `VUL-001`, `INF-001`, `SECTOR-002`)."
    ),
    response_description="Full entity risk analysis with graph context and plain-language explanation",
    responses={
        200: {"description": "Successful analysis"},
        404: {"description": "Entity ID not found in the knowledge graph"},
    },
)
def analyze(
    entity_id: str = Path(
        ...,
        title="Entity ID",
        description=(
            "Unique identifier for the threat entity. "
            "Format: `TA-###` (threat actor), `MA-###` (malware), "
            "`INF-###` (infrastructure), `VUL-###` (vulnerability), "
            "`SECTOR-###` (target sector)."
        ),
        openapi_examples=_ENTITY_EXAMPLES,
    ),
):
    try:
        return analyze_entity(entity_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Entity '{entity_id}' not found. "
                f"Use /intelligence/entities/ids to list all valid IDs."
            ),
        )


@router.get(
    "/entities",
    summary="Search and filter entities",
    description=(
        "Returns a paginated list of all threat entities in the knowledge graph. "
        "Supports free-text search, risk score range filtering, and entity type filtering.\n\n"
        "**Entity types:** `threat_actor` · `malware` · `infrastructure` · "
        "`vulnerability` · `target_sector`\n\n"
        "Results sorted by risk score descending."
    ),
)
def search_entities(
    query: Optional[str] = Query(
        default=None,
        title="Search query",
        description="Free-text search across entity ID and name (case-insensitive). Example: `APT28`, `ransomware`, `CVE`",
        openapi_examples={
            "Search APT28": {"value": "APT28"},
            "Search ransomware": {"value": "ransomware"},
            "Search CVE vulnerabilities": {"value": "CVE"},
            "Search LockBit": {"value": "LockBit"},
        },
    ),
    entity_type: Optional[
        Literal[
            "threat_actor",
            "malware",
            "infrastructure",
            "vulnerability",
            "target_sector",
        ]
    ] = Query(
        default=None,
        title="Entity type",
        description="Filter by entity type. Leave blank to return all types.",
    ),
    min_risk: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=1.0,
        title="Minimum risk score",
        description="Only return entities with risk_score >= this value (0.0–1.0).",
        openapi_examples={
            "High risk only (>= 0.8)": {"value": 0.8},
            "Medium and above (>= 0.5)": {"value": 0.5},
            "Any risk (>= 0.0)": {"value": 0.0},
        },
    ),
    max_risk: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=1.0,
        title="Maximum risk score",
        description="Only return entities with risk_score <= this value (0.0–1.0).",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        title="Result limit",
        description="Maximum number of entities to return (1–200).",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        title="Pagination offset",
        description="Number of results to skip for pagination.",
    ),
):
    return list_entities(
        query=query,
        min_risk=min_risk,
        max_risk=max_risk,
        entity_type=entity_type,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/graph/summary",
    summary="Knowledge graph statistics",
    description=(
        "Returns aggregate statistics for the full threat knowledge graph: "
        "node count, edge count, and risk score distribution across all entities."
    ),
)
def graph_summary():
    return get_graph_summary()


@router.get(
    "/graph/edges",
    summary="All graph relationships",
    description=(
        "Returns every directed edge in the knowledge graph with relation type "
        "and confidence score. Used by the Visual Lab force-directed graph renderer."
    ),
)
def graph_edges():
    return get_graph_edges()


@router.get(
    "/entities/ids",
    summary="List all entity IDs",
    description=(
        "Returns a flat list of all entity IDs currently in the knowledge graph. "
        "Useful for programmatic enumeration. "
        "For human-readable details with filtering, use `/entities` instead."
    ),
)
def list_entity_ids():
    result = list_entities(limit=200)
    return {
        "count": len(result["entities"]),
        "entity_ids": [e["entity_id"] for e in result["entities"]],
        "hint": "Pass any of these to /intelligence/analyze/{entity_id}",
    }
