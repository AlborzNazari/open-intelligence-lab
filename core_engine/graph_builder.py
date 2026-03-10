"""
core_engine/graph_builder.py  —  v0.2.0
Now loads all JSON datasets at construction time.
"""

import json
import os
import networkx as nx
from typing import Dict, Any, Iterable, Tuple
from .intelligence_entities import IntelligenceEntity

# Path to datasets/ folder — resolve relative to this file
DATASETS_DIR = os.path.join(os.path.dirname(__file__), "..", "datasets")


def _load_json(filename: str) -> list:
    path = os.path.join(DATASETS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class ThreatKnowledgeGraph:
    def __init__(self) -> None:
        self.graph = nx.DiGraph()
        self._load_datasets()

    # ── Dataset loading ────────────────────────────────────────────────────────

    def _load_datasets(self) -> None:
        """Load all JSON datasets and populate the graph."""
        self._load_entities(_load_json("threat_entities.json"))
        self._load_attack_patterns(_load_json("attack_patterns.json"))
        self._load_relations(_load_json("relations.json"))

    def _load_entities(self, entities: list) -> None:
        for e in entities:
            node_id = e.get("entity_id") or e.get("id")
            self.graph.add_node(
                node_id,
                label=e.get("name", node_id),
                type=e.get("entity_type", "unknown"),
                risk_score=float(e.get("risk_score", 0.0)),
                confidence=float(e.get("confidence", e.get("confidence_level", 0.0))),
                **{k: v for k, v in e.items()
                   if k not in ("entity_id", "id", "name", "entity_type",
                                "risk_score", "confidence", "confidence_level")},
            )

    def _load_attack_patterns(self, patterns: list) -> None:
        for p in patterns:
            node_id = p.get("pattern_id")
            self.graph.add_node(
                node_id,
                label=p.get("pattern_name", node_id),
                type="attack_pattern",
                risk_score=float(p.get("risk_level", 0.0)),
                confidence=1.0,
                **{k: v for k, v in p.items()
                   if k not in ("pattern_id", "pattern_name", "risk_level")},
            )

    def _load_relations(self, relations: list) -> None:
        for r in relations:
            src = r.get("source_id")
            dst = r.get("target_id")
            rel_type = r.get("relation_type", "related_to")
            if src in self.graph.nodes and dst in self.graph.nodes:
                self.graph.add_edge(
                    src, dst,
                    relation_type=rel_type,
                    confidence=float(r.get("confidence", 0.0)),
                    description=r.get("description", ""),
                )

    # ── Manual construction API (kept for compatibility) ───────────────────────

    def add_entity(self, entity: IntelligenceEntity) -> None:
        self.graph.add_node(
            entity.id,
            label=entity.name,
            type=entity.entity_type,
            risk_score=entity.risk_score,
            confidence=entity.confidence_level,
        )

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        metadata = metadata or {}
        self.graph.add_edge(source_id, target_id, relation_type=relation_type, **metadata)

    def load_from_iterables(
        self,
        entities: Iterable[IntelligenceEntity],
        relations: Iterable[Tuple[str, str, str]],
    ) -> None:
        for e in entities:
            self.add_entity(e)
        for src, rel, dst in relations:
            self.add_relationship(src, dst, rel)

    def get_graph(self) -> nx.DiGraph:
        return self.graph
