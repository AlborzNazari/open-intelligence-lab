"""
tests/test_service.py — v0.6.0

Tests for api/intelligence/service.py:
list_entities, analyze_entity, get_graph_summary, get_graph_edges.
Uses fresh (non-cached) calls — lru_cache is module-level so
tests share the cached graph, which is correct behavior.
"""

import pytest
from api.intelligence.service import (
    analyze_entity,
    list_entities,
    get_graph_summary,
    get_graph_edges,
)


class TestListEntities:
    def test_returns_dict_with_required_keys(self):
        result = list_entities()
        for key in ("total", "offset", "limit", "entities"):
            assert key in result

    def test_entities_is_list(self):
        result = list_entities()
        assert isinstance(result["entities"], list)

    def test_default_limit_respected(self):
        result = list_entities(limit=10)
        assert len(result["entities"]) <= 10

    def test_entity_has_required_fields(self):
        result = list_entities(limit=5)
        for entity in result["entities"]:
            for field in ("entity_id", "label", "type", "risk_score"):
                assert field in entity

    def test_sorted_by_risk_score_descending(self):
        result = list_entities(limit=50)
        scores = [e["risk_score"] for e in result["entities"]]
        assert scores == sorted(scores, reverse=True)

    def test_query_filter_apt28(self):
        result = list_entities(query="APT28")
        assert result["total"] >= 1
        for e in result["entities"]:
            assert "APT28" in e["label"] or "APT28" in e["entity_id"]

    def test_query_filter_no_match(self):
        result = list_entities(query="ZZZNONEXISTENTZZZ")
        assert result["total"] == 0

    def test_entity_type_filter(self):
        result = list_entities(entity_type="threat_actor", limit=50)
        for e in result["entities"]:
            assert e["type"] == "threat_actor"

    def test_min_risk_filter(self):
        result = list_entities(min_risk=0.9, limit=50)
        for e in result["entities"]:
            assert e["risk_score"] >= 0.9

    def test_max_risk_filter(self):
        result = list_entities(max_risk=0.6, limit=50)
        for e in result["entities"]:
            assert e["risk_score"] <= 0.6

    def test_offset_pagination(self):
        all_results = list_entities(limit=50)
        if all_results["total"] >= 2:
            page1 = list_entities(limit=1, offset=0)
            page2 = list_entities(limit=1, offset=1)
            assert page1["entities"][0]["entity_id"] != page2["entities"][0]["entity_id"]

    def test_limit_max_cap_at_200(self):
        result = list_entities(limit=9999)
        assert result["limit"] <= 200


class TestAnalyzeEntity:
    def test_known_entity_returns_dict(self):
        result = analyze_entity("TA-001")
        assert isinstance(result, dict)

    def test_known_entity_correct_id(self):
        result = analyze_entity("TA-001")
        assert result["entity_id"] == "TA-001"

    def test_known_malware(self):
        result = analyze_entity("MA-001")
        assert result["type"] == "malware"

    def test_known_vulnerability(self):
        result = analyze_entity("VUL-001")
        assert result["entity_id"] == "VUL-001"

    def test_unknown_entity_raises_key_error(self):
        with pytest.raises(KeyError):
            analyze_entity("NONEXISTENT-9999")

    def test_risk_score_in_valid_range(self):
        result = analyze_entity("TA-001")
        assert 0.0 <= result["risk_score"] <= 1.0

    def test_explanation_is_list_of_strings(self):
        result = analyze_entity("TA-001")
        assert isinstance(result["explanation"], list)
        assert all(isinstance(s, str) for s in result["explanation"])


class TestGetGraphSummary:
    def test_returns_dict(self):
        result = get_graph_summary()
        assert isinstance(result, dict)

    def test_required_keys(self):
        result = get_graph_summary()
        for key in ("node_count", "edge_count", "avg_risk_score", "max_risk_score", "min_risk_score"):
            assert key in result

    def test_node_count_positive(self):
        result = get_graph_summary()
        assert result["node_count"] > 0

    def test_edge_count_positive(self):
        result = get_graph_summary()
        assert result["edge_count"] > 0

    def test_avg_risk_in_range(self):
        result = get_graph_summary()
        assert 0.0 <= result["avg_risk_score"] <= 1.0

    def test_max_gte_avg_gte_min(self):
        result = get_graph_summary()
        assert result["min_risk_score"] <= result["avg_risk_score"] <= result["max_risk_score"]


class TestGetGraphEdges:
    def test_returns_dict(self):
        result = get_graph_edges()
        assert isinstance(result, dict)

    def test_edge_count_key_present(self):
        result = get_graph_edges()
        assert "edge_count" in result

    def test_edges_key_is_list(self):
        result = get_graph_edges()
        assert isinstance(result["edges"], list)

    def test_edge_count_matches_list_length(self):
        result = get_graph_edges()
        assert result["edge_count"] == len(result["edges"])

    def test_each_edge_has_required_fields(self):
        result = get_graph_edges()
        for edge in result["edges"]:
            for field in ("source", "target", "relation_type", "confidence"):
                assert field in edge, f"Edge missing field: {field}"

    def test_edge_confidence_in_range(self):
        result = get_graph_edges()
        for edge in result["edges"]:
            assert 0.0 <= edge["confidence"] <= 1.0
