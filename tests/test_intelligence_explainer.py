"""
tests/test_intelligence_explainer.py — v0.6.0

Tests for IntelligenceExplainer: explanation structure,
type-specific fields, and risk verdict classification.
"""

import pytest
import networkx as nx
from core_engine.graph_builder import ThreatKnowledgeGraph
from core_engine.risk_analyzer import RiskAnalyzer
from core_engine.intelligence_explainer import IntelligenceExplainer


@pytest.fixture(scope="module")
def explainer():
    kg = ThreatKnowledgeGraph()
    g = kg.get_graph()
    RiskAnalyzer(g).compute_all_risks()
    return IntelligenceExplainer(g)


class TestExplainerStructure:
    def test_returns_dict(self, explainer):
        result = explainer.explain_entity("TA-001")
        assert isinstance(result, dict)

    def test_required_keys_present(self, explainer):
        result = explainer.explain_entity("TA-001")
        for key in ("entity_id", "name", "type", "risk_score", "explanation"):
            assert key in result, f"Missing key: {key}"

    def test_entity_id_matches_input(self, explainer):
        for eid in ("TA-001", "MA-001", "VUL-001"):
            result = explainer.explain_entity(eid)
            assert result["entity_id"] == eid

    def test_explanation_is_list(self, explainer):
        result = explainer.explain_entity("TA-001")
        assert isinstance(result["explanation"], list)

    def test_explanation_non_empty(self, explainer):
        result = explainer.explain_entity("TA-001")
        assert len(result["explanation"]) >= 1

    def test_risk_score_is_float(self, explainer):
        result = explainer.explain_entity("TA-001")
        assert isinstance(result["risk_score"], float)

    def test_risk_score_in_range(self, explainer):
        for eid in ("TA-001", "MA-001", "VUL-001", "SECTOR-001"):
            result = explainer.explain_entity(eid)
            assert 0.0 <= result["risk_score"] <= 1.0


class TestTypeSpecificContent:
    def test_threat_actor_has_origin_in_explanation(self, explainer):
        result = explainer.explain_entity("TA-001")
        full_text = " ".join(result["explanation"])
        assert "Origin" in full_text or "origin" in full_text

    def test_malware_has_type_in_explanation(self, explainer):
        # MA-001 is X-Agent, a malware
        result = explainer.explain_entity("MA-001")
        full_text = " ".join(result["explanation"])
        assert "Type" in full_text or "type" in full_text or "Platforms" in full_text

    def test_vulnerability_has_cvss_in_explanation(self, explainer):
        result = explainer.explain_entity("VUL-001")
        full_text = " ".join(result["explanation"])
        assert "CVSS" in full_text or "cvss" in full_text


class TestRiskVerdictClassification:
    def test_critical_verdict_for_high_score(self):
        g = nx.DiGraph()
        g.add_node("X", risk_score=0.95, entity_type="threat_actor", label="Crit")
        exp = IntelligenceExplainer(g)
        result = exp.explain_entity("X")
        full = " ".join(result["explanation"])
        assert "CRITICAL" in full

    def test_high_verdict_for_mid_score(self):
        g = nx.DiGraph()
        g.add_node("X", risk_score=0.75, entity_type="malware", label="High")
        exp = IntelligenceExplainer(g)
        result = exp.explain_entity("X")
        full = " ".join(result["explanation"])
        assert "HIGH" in full

    def test_moderate_verdict(self):
        g = nx.DiGraph()
        g.add_node("X", risk_score=0.5, entity_type="vulnerability", label="Mod")
        exp = IntelligenceExplainer(g)
        result = exp.explain_entity("X")
        full = " ".join(result["explanation"])
        assert "MODERATE" in full

    def test_low_verdict(self):
        g = nx.DiGraph()
        g.add_node("X", risk_score=0.2, entity_type="infrastructure", label="Low")
        exp = IntelligenceExplainer(g)
        result = exp.explain_entity("X")
        full = " ".join(result["explanation"])
        assert "LOW" in full
