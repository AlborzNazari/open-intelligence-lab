from __future__ import annotations
from typing import Dict, Any
import networkx as nx


class RiskAnalyzer:
    def __init__(self, graph: nx.DiGraph) -> None:
        self.graph = graph

    def compute_entity_risk(self, node_id: str) -> float:
        node = self.graph.nodes[node_id]
        base = node.get("risk_score", 0.0)

        degree_factor = self.graph.degree(node_id) / 10.0
        incident_neighbors = sum(
            1 for _, nbr in self.graph.edges(node_id)
            if self.graph.nodes[nbr].get("entity_type") == "incident_category"
        )
        incident_factor = incident_neighbors * 0.1

        risk = min(1.0, base + degree_factor + incident_factor)
        self.graph.nodes[node_id]["risk_score"] = risk
        return risk

    def compute_all_risks(self) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        for node_id in self.graph.nodes:
            scores[node_id] = self.compute_entity_risk(node_id)
        return scores
