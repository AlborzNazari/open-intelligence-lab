from core_engine.graph_builder import ThreatKnowledgeGraph
from core_engine.risk_analyzer import RiskAnalyzer
from core_engine.intelligence_explainer import IntelligenceExplainer
from core_engine.intelligence_entities import IntelligenceEntity
from visualization.graph_renderer import draw_threat_graph


def main():
    kg = ThreatKnowledgeGraph()

    org = IntelligenceEntity(id="org:1", entity_type="organization", name="Example Corp")
    domain = IntelligenceEntity(id="dom:1", entity_type="domain", name="example.com")
    incident = IntelligenceEntity(id="inc:1", entity_type="incident_category", name="Public Metadata Exposure")

    kg.add_entity(org)
    kg.add_entity(domain)
    kg.add_entity(incident)

    kg.add_relationship("org:1", "dom:1", "uses")
    kg.add_relationship("org:1", "inc:1", "associated_with")

    graph = kg.get_graph()
    risk_analyzer = RiskAnalyzer(graph)
    risk_analyzer.compute_all_risks()

    explainer = IntelligenceExplainer(graph)
    explanation = explainer.explain_entity("org:1")

    print("Risk Score:", explanation["risk_score"])
    print("Explanation:")
    for line in explanation["explanation"]:
        print("-", line)

    draw_threat_graph(graph)


if __name__ == "__main__":
    main()
