from __future__ import annotations
from typing import Dict, Any, List
import networkx as nx


class IntelligenceExplainer:
    def __init__(self, graph: nx.DiGraph) -> None:
        self.graph = graph

    def explain_entity(self, node_id: str) -> Dict[str, Any]:
        node = self.graph.nodes[node_id]
        risk_score = node.get("risk_score", 0.0)
        name = node.get("label") or node.get("name") or node_id
        entity_type = node.get("type") or node.get("entity_type") or "unknown"

        neighbors = list(self.graph.neighbors(node_id))
        predecessors = list(self.graph.predecessors(node_id))

        explanation_lines: List[str] = []

        # Line 1 — identity
        explanation_lines.append(
            f"'{name}' is a {entity_type.replace('_', ' ')} with {self.graph.degree(node_id)} "
            f"connections in the threat graph ({len(predecessors)} incoming, {len(neighbors)} outgoing)."
        )

        # Line 2 — outgoing relationships (what this entity does/uses/targets)
        if neighbors:
            neighbor_summaries = []
            for n in neighbors[:5]:
                edge_data = self.graph.edges[node_id, n]
                rel = edge_data.get("relation_type", "related to")
                n_name = self.graph.nodes[n].get("label") or self.graph.nodes[n].get("name") or n
                neighbor_summaries.append(f"{rel} {n_name}")
            explanation_lines.append(
                "Outgoing relations: " + "; ".join(neighbor_summaries) +
                (f" (and {len(neighbors)-5} more)" if len(neighbors) > 5 else "")
            )

        # Line 3 — incoming relationships (who uses/targets this entity)
        if predecessors:
            pred_names = [
                self.graph.nodes[p].get("label") or self.graph.nodes[p].get("name") or p
                for p in predecessors[:4]
            ]
            explanation_lines.append(
                f"Referenced by: {', '.join(pred_names)}" +
                (f" and {len(predecessors)-4} others" if len(predecessors) > 4 else "")
            )

        # Line 4 — type-specific context
        if entity_type == "threat_actor":
            motivation = node.get("motivation", [])
            origin = node.get("origin_country", "unknown")
            since = node.get("active_since", "unknown")
            if motivation or origin:
                explanation_lines.append(
                    f"Origin: {origin} | Active since: {since} | "
                    f"Motivation: {', '.join(motivation) if motivation else 'unknown'}"
                )
            sectors = node.get("target_sectors", [])
            if sectors:
                explanation_lines.append(f"Known target sectors: {', '.join(sectors[:5])}")

        elif entity_type == "malware":
            mtype = node.get("malware_type", "unknown")
            caps = node.get("capabilities", [])
            platforms = node.get("platforms", [])
            explanation_lines.append(
                f"Type: {mtype} | Platforms: {', '.join(platforms[:3]) if platforms else 'unknown'}"
            )
            if caps:
                explanation_lines.append(f"Capabilities: {', '.join(caps[:4])}")

        elif entity_type == "vulnerability":
            cvss = node.get("cvss_score", "unknown")
            product = node.get("affected_product", "unknown")
            status = node.get("exploitation_status", "unknown")
            explanation_lines.append(
                f"Affected product: {product} | CVSS: {cvss} | Status: {status}"
            )

        elif entity_type == "attack_pattern":
            category = node.get("category", "unknown")
            mitre = node.get("mitre_ref", "")
            explanation_lines.append(
                f"Category: {category}" + (f" | MITRE: {mitre}" if mitre else "")
            )

        elif entity_type == "target_sector":
            primary_risk = node.get("primary_risk", "")
            if primary_risk:
                explanation_lines.append(f"Primary risk: {primary_risk}")

        # Line final — risk verdict
        if risk_score >= 0.9:
            explanation_lines.append(
                f"CRITICAL risk ({risk_score:.3f}) — among the highest-risk entities in this graph."
            )
        elif risk_score >= 0.7:
            explanation_lines.append(
                f"HIGH risk ({risk_score:.3f}) — significant threat based on connectivity and profile."
            )
        elif risk_score >= 0.4:
            explanation_lines.append(
                f"MODERATE risk ({risk_score:.3f}) — notable presence but limited connections."
            )
        else:
            explanation_lines.append(
                f"LOW risk ({risk_score:.3f}) — limited threat signal in current graph."
            )

        return {
            "entity_id": node_id,
            "name": name,
            "type": entity_type,
            "risk_score": risk_score,
            "explanation": explanation_lines,
        }
