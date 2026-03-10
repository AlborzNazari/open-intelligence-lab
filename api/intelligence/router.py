"""
api/intelligence/router.py  —  v0.2.0
"""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from api.intelligence.service import (
    analyze_entity, list_entities, get_graph_summary, get_graph_edges
)

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])


@router.get("/analyze/{entity_id}")
def analyze(entity_id: str):
    try:
        return analyze_entity(entity_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/entities")
def search_entities(
    query: Optional[str] = Query(default=None),
    min_risk: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    max_risk: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    entity_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    return list_entities(query=query, min_risk=min_risk, max_risk=max_risk,
                         entity_type=entity_type, limit=limit, offset=offset)


@router.get("/graph/summary")
def graph_summary():
    return get_graph_summary()


@router.get("/graph/edges")
def graph_edges():
    """Return all edges — used by the dashboard graph visualization."""
    return get_graph_edges()


@router.get("/entities/ids")
def list_entity_ids():
    result = list_entities(limit=200)
    return {"entity_ids": [e["entity_id"] for e in result["entities"]]}
