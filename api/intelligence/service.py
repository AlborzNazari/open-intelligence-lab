"""
api/service.py  —  v0.2.0
Loads the real datasets ONCE at startup via a module-level singleton.
All endpoints share the same graph + analyzer instance.
"""

from __future__ import annotations
from functools import lru_cache
from typing import Any

from core_engine.graph_builder import ThreatKnowledgeGraph
from core_engine.risk_analyzer import RiskAnalyzer
from core_engine.intelligence_explainer import IntelligenceExplainer


# ─── Singleton helpers ────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_graph():
    """Build the knowledge graph once and cache it for the process lifetime."""
    kg = ThreatKnowledgeGraph()
    return kg.get_graph()


@lru_cache(maxsize=1)
def _get_analyzer() -> RiskAnalyzer:
    """Build and pre-compute the risk analyzer once."""
    analyzer = RiskAnalyzer(_get_graph())
    analyzer.compute_all_risks()
    return analyzer


# ─── Public service functions ─────────────────────────────────────────────────

def analyze_entity(entity_id: str) -> dict[str, Any]:
    """
    Return risk score + explanation for a single entity.
    Raises KeyError if entity_id is not found in the graph.
    """
    graph = _get_graph()

    if entity_id not in graph.nodes:
        raise KeyError(f"Entity '{entity_id}' not found in the knowledge graph.")

    _get_analyzer()  # ensure risks are pre-computed

    explainer = IntelligenceExplainer(graph)
    explanation = explainer.explain_entity(entity_id)

    return {
        "entity_id": entity_id,
        "risk_score": explanation["risk_score"],
        "explanation": explanation["explanation"],
    }


def list_entities(
    query: str | None = None,
    min_risk: float | None = None,
    max_risk: float | None = None,
    entity_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Return a filtered, paginated list of entities with their risk scores.

    Parameters
    ----------
    query       : case-insensitive substring match on entity id or label
    min_risk    : include only entities with risk_score >= min_risk
    max_risk    : include only entities with risk_score <= max_risk
    entity_type : match the 'type' node attribute exactly
    limit       : max results to return (default 50, max 200)
    offset      : pagination offset
    """
    graph = _get_graph()
    _get_analyzer()  # ensure risks are pre-computed

    limit = min(limit, 200)

    results: list[dict[str, Any]] = []

    for node_id, attrs in graph.nodes(data=True):
        risk_score: float = attrs.get("risk_score", 0.0)

        # ── filters ──────────────────────────────────────────────────────────
        if query:
            label: str = attrs.get("label", node_id)
            if (
                query.lower() not in node_id.lower()
                and query.lower() not in label.lower()
            ):
                continue

        if min_risk is not None and risk_score < min_risk:
            continue

        if max_risk is not None and risk_score > max_risk:
            continue

        if entity_type is not None:
            if attrs.get("type", "").lower() != entity_type.lower():
                continue

        results.append(
            {
                "entity_id": node_id,
                "label": attrs.get("label", node_id),
                "type": attrs.get("type", "unknown"),
                "risk_score": risk_score,
            }
        )

    # Sort by risk score descending so highest-risk entities come first
    results.sort(key=lambda x: x["risk_score"], reverse=True)

    total = len(results)
    page = results[offset : offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "entities": page,
    }


def get_graph_summary() -> dict[str, Any]:
    """
    Return a high-level summary of the loaded graph — useful for the
    dashboard health-check and the /graph/summary endpoint.
    """
    graph = _get_graph()
    _get_analyzer()

    risk_scores = [
        attrs.get("risk_score", 0.0)
        for _, attrs in graph.nodes(data=True)
    ]

    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "avg_risk_score": round(sum(risk_scores) / len(risk_scores), 4) if risk_scores else 0.0,
        "max_risk_score": round(max(risk_scores), 4) if risk_scores else 0.0,
        "min_risk_score": round(min(risk_scores), 4) if risk_scores else 0.0,
    }
