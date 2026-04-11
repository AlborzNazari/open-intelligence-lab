"""
tests/test_risk_analyzer.py — v0.6.0

Tests for RiskAnalyzer: score computation, graph mutation,
boundary conditions, and all-risks bulk operation.
"""

import pytest
import networkx as nx
from core_engine.graph_builder import ThreatKnowledgeGraph
from core_engine.risk_analyzer import RiskAnalyzer


@pytest.fixture(scope="module")
def analyzed_graph():
    """Graph with risk scores already computed."""
    kg = ThreatKnowledgeGraph()
    g = kg.get_graph()
    analyzer = RiskAnalyzer(g)
    analyzer.compute_all_risks()
    return g


@pytest.fixture
def minimal_graph():
    """
    A controlled 3-node graph for deterministic unit testing.
    Avoids depending on dataset changes.
    """
    g = nx.DiGraph()
    g.add_node("A", risk_score=0.5, entity_type="threat_actor", label="Actor A")
    g.add_node("B", risk_score=0.3, entity_type="malware", label="Malware B")
    g.add_node("C", risk_score=0.2, entity_type="target_sector", label="Sector C")
    g.add_edge("A", "B", relation_type="uses", confidence=0.9)
    g.add_edge("A", "C", relation_type="targets", confidence=0.8)
    return g


class TestComputeEntityRisk:
    def test_returns_float(self, minimal_graph):
        analyzer = RiskAnalyzer(minimal_graph)
        result = analyzer.compute_entity_risk("A")
        assert isinstance(result, float)

    def test_result_capped_at_one(self, minimal_graph):
        # Give A an extreme base so it would exceed 1.0 without capping
        minimal_graph.nodes["A"]["risk_score"] = 0.99
        analyzer = RiskAnalyzer(minimal_graph)
        result = analyzer.compute_entity_risk("A")
        assert result <= 1.0

    def test_isolated_node_keeps_base_score(self):
        g = nx.DiGraph()
        g.add_node("X", risk_score=0.4, entity_type="vulnerability", label="X")
        analyzer = RiskAnalyzer(g)
        result = analyzer.compute_entity_risk("X")
        # isolated node: degree_factor=0, incident_factor=0 → result == base
        assert result == pytest.approx(0.4, abs=1e-9)

    def test_score_written_back_to_node(self, minimal_graph):
        g = nx.DiGraph()
        g.add_node("Y", risk_score=0.3, entity_type="malware", label="Y")
        analyzer = RiskAnalyzer(g)
        computed = analyzer.compute_entity_risk("Y")
        assert g.nodes["Y"]["risk_score"] == computed


class TestComputeAllRisks:
    def test_returns_dict(self, minimal_graph):
        analyzer = RiskAnalyzer(minimal_graph)
        result = analyzer.compute_all_risks()
        assert isinstance(result, dict)

    def test_all_nodes_covered(self, minimal_graph):
        analyzer = RiskAnalyzer(minimal_graph)
        result = analyzer.compute_all_risks()
        for node in minimal_graph.nodes:
            assert node in result

    def test_all_scores_in_range(self, analyzed_graph):
        for node_id, attrs in analyzed_graph.nodes(data=True):
            score = attrs.get("risk_score", 0.0)
            assert 0.0 <= score <= 1.0, (
                f"{node_id} risk_score={score} out of [0,1] after compute_all_risks"
            )

    def test_high_connectivity_increases_risk(self):
        """Node with more edges should get higher risk than isolated peer."""
        g = nx.DiGraph()
        g.add_node("hub", risk_score=0.5, entity_type="threat_actor", label="Hub")
        g.add_node("leaf", risk_score=0.5, entity_type="threat_actor", label="Leaf")
        # Give hub 5 outgoing edges
        for i in range(5):
            target = f"T{i}"
            g.add_node(target, risk_score=0.1, entity_type="malware", label=target)
            g.add_edge("hub", target, relation_type="uses", confidence=0.8)

        analyzer = RiskAnalyzer(g)
        analyzer.compute_all_risks()
        assert g.nodes["hub"]["risk_score"] > g.nodes["leaf"]["risk_score"]
