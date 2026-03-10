"""
api/intelligence/router.py  —  v0.2.0
All intelligence endpoints.  Mounted at /intelligence in main.py.
"""

from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.intelligence.service import analyze_entity, list_entities, get_graph_summary

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


# ─── 1. Analyze a single entity ───────────────────────────────────────────────

@router.get(
    "/analyze/{entity_id}",
    summary="Analyze entity risk",
    response_description="Risk score and human-readable explanation for the entity.",
)
def analyze(entity_id: str):
    """
    Compute and return the risk score + explainability output for a
    single entity identified by **entity_id**.

    Raises **404** if the entity is not present in the knowledge graph.
    """
    try:
        return analyze_entity(entity_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ─── 2. Search / filter entities ──────────────────────────────────────────────

@router.get(
    "/entities",
    summary="Search and filter entities",
    response_description="Paginated list of entities matching the given filters.",
)
def search_entities(
    query: Optional[str] = Query(
        default=None,
        description="Case-insensitive substring match on entity id or label.",
        example="apt",
    ),
    min_risk: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=1.0,
        description="Include only entities with risk_score ≥ this value.",
        example=0.5,
    ),
    max_risk: Optional[float] = Query(
        default=None,
        ge=0.0,
        le=1.0,
        description="Include only entities with risk_score ≤ this value.",
        example=0.9,
    ),
    entity_type: Optional[str] = Query(
        default=None,
        description="Exact match on the entity's 'type' attribute (e.g. 'threat_actor').",
        example="threat_actor",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Max number of results to return.",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Pagination offset.",
    ),
):
    """
    Return a filtered, paginated list of all entities in the knowledge graph.

    Results are sorted by **risk_score descending** so the most critical
    entities surface first.

    ### Filter examples
    - `/intelligence/entities?query=apt` — all entities whose id or label contains "apt"
    - `/intelligence/entities?min_risk=0.7` — high-risk entities only
    - `/intelligence/entities?entity_type=threat_actor&min_risk=0.5`
    - `/intelligence/entities?limit=10&offset=20` — page 3 of 10 results per page
    """
    return list_entities(
        query=query,
        min_risk=min_risk,
        max_risk=max_risk,
        entity_type=entity_type,
        limit=limit,
        offset=offset,
    )


# ─── 3. Graph summary (for dashboard health widget) ───────────────────────────

@router.get(
    "/graph/summary",
    summary="Knowledge graph summary",
    response_description="Node count, edge count, and aggregate risk statistics.",
)
def graph_summary():
    """
    Return high-level statistics about the loaded knowledge graph.
    Useful as a dashboard health endpoint and sanity-check after startup.
    """
    return get_graph_summary()


# ─── 4. List all entity ids (lightweight, no scores) ─────────────────────────

@router.get(
    "/entities/ids",
    summary="List all entity IDs",
    response_description="Flat list of every entity_id in the graph.",
)
def list_entity_ids():
    """
    Return every entity_id in the graph without scores.
    Useful for populating autocomplete / dropdown widgets in the dashboard.
    """
    result = list_entities(limit=200)
    return {"entity_ids": [e["entity_id"] for e in result["entities"]]}
