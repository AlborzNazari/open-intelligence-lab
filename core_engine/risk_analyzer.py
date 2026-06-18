from __future__ import annotations
from typing import Dict, Any
import networkx as nx


class RiskAnalyzer:
    def __init__(self, graph: nx.DiGraph) -> None:
        self.graph = graph

    def compute_entity_risk(self, node_id: str) -> float:
        # Risk = base score from the dataset, raised by how connected the entity
        # is in the graph (more relationships => more central => higher risk),
        # capped at 1.0. Degree is scaled by 10 so a node needs ~10 connections
        # to add a full point before capping.
        node = self.graph.nodes[node_id]
        base = node.get("risk_score", 0.0)

        degree_factor = self.graph.degree(node_id) / 10.0

        risk = min(1.0, base + degree_factor)
        self.graph.nodes[node_id]["risk_score"] = risk
        return risk

    def compute_all_risks(self) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        for node_id in self.graph.nodes:
            scores[node_id] = self.compute_entity_risk(node_id)
        return scores
