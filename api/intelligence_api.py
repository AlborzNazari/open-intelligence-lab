from fastapi import FastAPI
from pydantic import BaseModel
import networkx as nx

from core_engine.graph_builder import ThreatKnowledgeGraph
from core_engine.risk_analyzer import RiskAnalyzer
from core_engine.intelligence_explainer import IntelligenceExplainer
from core_engine.intelligence_entities import IntelligenceEntity


app = FastAPI(title="Open Intelligence Lab API")

# Demo in-memory graph
kg = ThreatKnowledgeGraph()
org = IntelligenceEntity(id="org:1", entity_type="organization", name="Example Corp")
incident = IntelligenceEntity(id="inc:1", entity_type="incident_category", name="Public Metadata Exposure")
kg.add_entity(org)
kg.add_entity(incident)
kg.add_relationship("org:1", "inc:1", "associated_with")

risk_analyzer = RiskAnalyzer(kg.get_graph())
risk_analyzer.compute_all_risks()
explainer = IntelligenceExplainer(kg.get_graph())


class EntityExplanation(BaseModel):
    entity_id: str
    name: str | None
    risk_score: float
    explanation: list[str]


@app.get("/entities/{entity_id}/explanation", response_model=EntityExplanation)
def get_entity_explanation(entity_id: str):
    result = explainer.explain_entity(entity_id)
    return EntityExplanation(**result)
