from __future__ import annotations
from typing import Dict, Any, List
import networkx as nx


class IntelligenceExplainer:
    def __init__(self, graph: nx.DiGraph) -> None:
        self.graph = graph

    def explain_entity(self, node_id: str) -> Dict[str, Any]:
        node = self.graph.nodes[node_id]
        risk_score = node.get("risk_score", 0.0)

        neighbors = list(self.graph.neighbors(node_id))
        incident_neighbors = [
            n for n in neighbors
            if self.graph.nodes[n].get("entity_type") == "incident_category"
        ]

        explanation_lines: List[str] = []

        explanation_lines.append(
            f"Entity '{node.get('name')}' has degree {self.graph.degree(node_id)} in the threat graph."
        )

        if incident_neighbors:
            explanation_lines.append(
                f"Connected to {len(incident_neighbors)} incident categories: "
                + ", ".join(self.graph.nodes[n].get("name", n) for n in incident_neighbors)
            )

        if risk_score > 0.7:
            explanation_lines.append("Overall risk is high based on connectivity and incident associations.")
        elif risk_score > 0.4:
            explanation_lines.append("Overall risk is moderate with some notable incident associations.")
        else:
            explanation_lines.append("Overall risk is currently low based on available graph signals.")

        return {
            "entity_id": node_id,
            "name": node.get("name"),
            "risk_score": risk_score,
            "explanation": explanation_lines,
        }
  
