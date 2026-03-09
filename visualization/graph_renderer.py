"""
demo.py — Open Intelligence Lab
Loads all 5 real datasets and runs the full intelligence pipeline.
"""

import json
import os
from core_engine.graph_builder import ThreatKnowledgeGraph
from core_engine.risk_analyzer import RiskAnalyzer
from core_engine.intelligence_explainer import IntelligenceExplainer
from core_engine.intelligence_entities import IntelligenceEntity
from visualization.graph_renderer import draw_threat_graph


DATASETS_DIR = os.path.join(os.path.dirname(__file__), "datasets")


def load_json(filename: str) -> list:
    path = os.path.join(DATASETS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("\n╔══════════════════════════════════════════════════════╗")
    print("║        OPEN INTELLIGENCE LAB  —  v0.1               ║")
    print("║        Ethical OSINT · Graph-Based Threat Intel      ║")
    print("╚══════════════════════════════════════════════════════╝\n")

    # ── LOAD DATASETS ─────────────────────────────────────────────────────────
    print("[1/5] Loading datasets...")
    threat_entities  = load_json("threat_entities.json")
    attack_patterns  = load_json("attack_patterns.json")
    relations        = load_json("relations.json")
    campaigns        = load_json("campaigns.json")
    mitre_mapping    = load_json("mitre_mapping.json")

    print(f"      ✓ threat_entities  → {len(threat_entities)} entities")
    print(f"      ✓ attack_patterns  → {len(attack_patterns)} patterns")
    print(f"      ✓ relations        → {len(relations)} edges")
    print(f"      ✓ campaigns        → {len(campaigns)} campaigns")
    print(f"      ✓ mitre_mapping    → {len(mitre_mapping)} mappings")

    # ── BUILD GRAPH ───────────────────────────────────────────────────────────
    print("\n[2/5] Building knowledge graph...")
    kg = ThreatKnowledgeGraph()

    # Add all entities from threat_entities.json
    for item in threat_entities:
        entity = IntelligenceEntity(
            id=item["entity_id"],
            entity_type=item["entity_type"],
            name=item["name"],
            risk_score=item.get("risk_score", 0.5),
            confidence_level=item.get("confidence", 0.5),
        )
        kg.add_entity(entity)

    # Add attack patterns as nodes
    for ap in attack_patterns:
        entity = IntelligenceEntity(
            id=ap["pattern_id"],
            entity_type="attack_pattern",
            name=ap["name"],
            risk_score=ap.get("severity_score", 0.5),
            confidence_level=ap.get("confidence", 0.7),
        )
        kg.add_entity(entity)

    # Add all relations as edges
    for rel in relations:
        kg.add_relationship(
            source_id=rel["source_id"],
            target_id=rel["target_id"],
            relation_type=rel["relation_type"],
            metadata={"confidence": rel.get("confidence", 0.7)},
        )

    graph = kg.get_graph()
    print(f"      ✓ Graph built → {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

    # ── RISK ANALYSIS ─────────────────────────────────────────────────────────
    print("\n[3/5] Running risk analysis...")
    risk_analyzer = RiskAnalyzer(graph)
    risk_analyzer.compute_all_risks()
    print("      ✓ Risk scores computed for all entities")

    # ── EXPLAINABILITY ────────────────────────────────────────────────────────
    print("\n[4/5] Generating intelligence explanations...")
    explainer = IntelligenceExplainer(graph)

    # Run explanations on all threat actors
    threat_actors = [e for e in threat_entities if e["entity_type"] == "threat_actor"]
    print(f"\n{'─'*60}")
    print(f"  {'ENTITY':<25} {'RISK':>6}  {'BAND':<10}  EXPLANATION")
    print(f"{'─'*60}")

    for actor in threat_actors:
        eid = actor["entity_id"]
        try:
            result = explainer.explain_entity(eid)
            score  = result["risk_score"]
            band   = "CRITICAL" if score >= 0.9 else "HIGH" if score >= 0.7 else "MEDIUM" if score >= 0.4 else "LOW"
            first_line = result["explanation"][0] if result["explanation"] else ""
            print(f"  {actor['name']:<25} {score:>6.2f}  {band:<10}  {first_line}")
        except Exception:
            print(f"  {actor['name']:<25}  —  (no risk data)")

    print(f"{'─'*60}")

    # ── CAMPAIGN SUMMARY ──────────────────────────────────────────────────────
    print(f"\n[5/5] Campaign intelligence summary...")
    print(f"\n  {'CAMPAIGN':<30} {'ADVERSARY':<15} {'OBJECTIVE'}")
    print(f"  {'─'*65}")
    for c in campaigns:
        name      = c.get("campaign_name", c.get("name", "Unknown"))[:28]
        adversary = c.get("adversary", c.get("attributed_to", "Unknown"))[:13]
        objective = c.get("objective", c.get("motivation", ""))[:35]
        print(f"  {name:<30} {adversary:<15} {objective}")

    # ── VISUALIZE ─────────────────────────────────────────────────────────────
    print("\n[✓] Launching interactive threat graph in browser...\n")
    draw_threat_graph(graph)


if __name__ == "__main__":
    main()
