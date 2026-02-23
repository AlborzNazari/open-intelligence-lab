from core_engine.graph_builder import GraphBuilder
from core_engine.risk_analyzer import RiskAnalyzer
from core_engine.explainability import ExplainabilityEngine

def analyze_entity(entity_id: str):
    # Build graph
    builder = GraphBuilder()
    graph = builder.build_graph_from_dataset("datasets/attack_patterns")

    # Compute risk
    analyzer = RiskAnalyzer()
    risk_score = analyzer.compute_entity_risk(graph, entity_id)

    # Explain result
    explainer = ExplainabilityEngine()
    explanation = explainer.explain_entity_risk(graph, entity_id)

    return {
        "entity_id": entity_id,
        "risk_score": risk_score,
        "explanation": explanation
    }
