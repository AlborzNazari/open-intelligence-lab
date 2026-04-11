"""
tests/test_graph_builder.py — v0.6.0

Tests for ThreatKnowledgeGraph: dataset loading, node/edge counts,
node attribute integrity, and relationship correctness.
"""

import pytest
import networkx as nx
from core_engine.graph_builder import ThreatKnowledgeGraph


@pytest.fixture(scope="module")
def graph():
    """Build the graph once per module — datasets are static."""
    kg = ThreatKnowledgeGraph()
    return kg.get_graph()


class TestGraphLoading:
    def test_returns_digraph(self, graph):
        assert isinstance(graph, nx.DiGraph)

    def test_node_count_positive(self, graph):
        assert graph.number_of_nodes() > 0

    def test_edge_count_positive(self, graph):
        assert graph.number_of_edges() > 0

    def test_known_threat_actors_present(self, graph):
        for ta_id in ("TA-001", "TA-002", "TA-003", "TA-004"):
            assert ta_id in graph.nodes, f"Expected threat actor {ta_id} in graph"

    def test_known_malware_present(self, graph):
        for ma_id in ("MA-001", "MA-003", "MA-007"):
            assert ma_id in graph.nodes, f"Expected malware {ma_id} in graph"

    def test_known_vulnerabilities_present(self, graph):
        for v_id in ("VUL-001", "VUL-002"):
            assert v_id in graph.nodes, f"Expected vulnerability {v_id} in graph"

    def test_threat_actor_has_label(self, graph):
        attrs = graph.nodes["TA-001"]
        assert "label" in attrs
        assert attrs["label"]  # non-empty

    def test_threat_actor_type_field(self, graph):
        attrs = graph.nodes["TA-001"]
        assert attrs.get("type") == "threat_actor"

    def test_risk_score_is_float(self, graph):
        for node_id, attrs in graph.nodes(data=True):
            score = attrs.get("risk_score", 0.0)
            assert isinstance(score, float), f"{node_id} risk_score is not float"

    def test_risk_score_in_range(self, graph):
        for node_id, attrs in graph.nodes(data=True):
            score = attrs.get("risk_score", 0.0)
            assert 0.0 <= score <= 1.0, (
                f"{node_id} risk_score={score} outside [0, 1]"
            )

    def test_edges_have_relation_type(self, graph):
        for src, dst, data in graph.edges(data=True):
            assert "relation_type" in data, (
                f"Edge {src}→{dst} missing relation_type"
            )

    def test_edges_have_confidence(self, graph):
        for src, dst, data in graph.edges(data=True):
            conf = data.get("confidence", None)
            assert conf is not None, f"Edge {src}→{dst} missing confidence"
            assert 0.0 <= conf <= 1.0, (
                f"Edge {src}→{dst} confidence={conf} outside [0, 1]"
            )

    def test_apt28_uses_xagent(self, graph):
        """Known relation: APT28 (TA-001) uses X-Agent (MA-001)."""
        assert graph.has_edge("TA-001", "MA-001"), (
            "Expected TA-001 → MA-001 'uses' edge"
        )
        edge = graph.edges["TA-001", "MA-001"]
        assert edge.get("relation_type") == "uses"

    def test_no_self_loops(self, graph):
        loops = list(nx.selfloop_edges(graph))
        assert len(loops) == 0, f"Unexpected self-loops: {loops}"

    def test_add_entity_api(self):
        """Manual add_entity API still works for programmatic use."""
        from core_engine.intelligence_entities import IntelligenceEntity

        kg = ThreatKnowledgeGraph()
        g = kg.get_graph()
        before = g.number_of_nodes()

        entity = IntelligenceEntity(
            id="TEST-001",
            entity_type="organization",
            name="Test Org",
            risk_score=0.5,
            confidence_level=0.8,
        )
        kg.add_entity(entity)
        assert g.number_of_nodes() == before + 1
        assert g.nodes["TEST-001"]["label"] == "Test Org"
