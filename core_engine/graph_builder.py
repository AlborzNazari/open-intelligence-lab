import networkx as nx
from typing import Dict, Any, Iterable, Tuple
from .intelligence_entities import IntelligenceEntity


class ThreatKnowledgeGraph:
    def __init__(self) -> None:
        self.graph = nx.DiGraph()

    def add_entity(self, entity: IntelligenceEntity) -> None:
        self.graph.add_node(
            entity.id,
            entity_type=entity.entity_type,
            name=entity.name,
            risk_score=entity.risk_score,
            confidence_level=entity.confidence_level,
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
