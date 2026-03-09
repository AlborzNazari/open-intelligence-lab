from core_engine.graph_builder import ThreatKnowledgeGraph
from core_engine.risk_analyzer import RiskAnalyzer
from core_engine.intelligence_explainer import IntelligenceExplainer

def analyze_entity(entity_id: str):
    # Build graph
    kg = ThreatKnowledgeGraph()
    graph = kg.get_graph()

    # Compute risk
    analyzer = RiskAnalyzer(graph)
    analyzer.compute_all_risks()

    # Explain result
    explainer = IntelligenceExplainer(graph)
    explanation = explainer.explain_entity(entity_id)

    return {
        "entity_id": entity_id,
        "risk_score": explanation["risk_score"],
        "explanation": explanation["explanation"]
    }
