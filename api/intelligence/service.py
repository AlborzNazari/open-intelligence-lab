"""
api/intelligence/service.py  —  v0.4.0
"""
from __future__ import annotations
from functools import lru_cache
from typing import Any

from core_engine.graph_builder import ThreatKnowledgeGraph
from core_engine.risk_analyzer import RiskAnalyzer
from core_engine.intelligence_explainer import IntelligenceExplainer


@lru_cache(maxsize=1)
def _get_graph():
    kg = ThreatKnowledgeGraph()
    return kg.get_graph()


@lru_cache(maxsize=1)
def _get_analyzer() -> RiskAnalyzer:
    analyzer = RiskAnalyzer(_get_graph())
    analyzer.compute_all_risks()
    return analyzer


def analyze_entity(entity_id: str) -> dict[str, Any]:
    graph = _get_graph()
    if entity_id not in graph.nodes:
        raise KeyError(f"Entity '{entity_id}' not found in the knowledge graph.")
    _get_analyzer()
    explainer = IntelligenceExplainer(graph)
    return explainer.explain_entity(entity_id)


def list_entities(
    query: str | None = None,
    min_risk: float | None = None,
    max_risk: float | None = None,
    entity_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    graph = _get_graph()
    _get_analyzer()
    limit = min(limit, 200)
    results = []
    for node_id, attrs in graph.nodes(data=True):
        risk_score = attrs.get("risk_score", 0.0)
        if query:
            label = attrs.get("label", node_id)
            if query.lower() not in node_id.lower() and query.lower() not in label.lower():
                continue
        if min_risk is not None and risk_score < min_risk:
            continue
        if max_risk is not None and risk_score > max_risk:
            continue
        if entity_type is not None:
            if attrs.get("type", "").lower() != entity_type.lower():
                continue
        results.append({
            "entity_id": node_id,
            "label": attrs.get("label", node_id),
            "type": attrs.get("type", "unknown"),
            "risk_score": risk_score,
        })
    results.sort(key=lambda x: x["risk_score"], reverse=True)
    total = len(results)
    return {"total": total, "offset": offset, "limit": limit, "entities": results[offset:offset+limit]}


def get_graph_summary() -> dict[str, Any]:
    graph = _get_graph()
    _get_analyzer()
    risk_scores = [attrs.get("risk_score", 0.0) for _, attrs in graph.nodes(data=True)]
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "avg_risk_score": round(sum(risk_scores)/len(risk_scores), 4) if risk_scores else 0.0,
        "max_risk_score": round(max(risk_scores), 4) if risk_scores else 0.0,
        "min_risk_score": round(min(risk_scores), 4) if risk_scores else 0.0,
    }


def get_graph_edges() -> dict[str, Any]:
    """Return all edges from the knowledge graph — used by the dashboard graph tab."""
    graph = _get_graph()
    edges = []
    for src, dst, data in graph.edges(data=True):
        edges.append({
            "source": src,
            "target": dst,
            "relation_type": data.get("relation_type", "related_to"),
            "confidence": data.get("confidence", 0.0),
        })
    return {"edge_count": len(edges), "edges": edges}
