from dataclasses import dataclass
from typing import Literal


# Entity types as they actually appear in datasets/threat_entities.json and as
# the graph builder stores them. Keep this list in sync with the data.
EntityType = Literal[
    "threat_actor",
    "malware",
    "infrastructure",
    "vulnerability",
    "target_sector",
    "attack_pattern",
]


@dataclass
class IntelligenceEntity:
    """A typed value object for building the graph programmatically.

    The live pipeline loads entities straight from JSON; this class exists for
    the programmatic construction API (ThreatKnowledgeGraph.add_entity).
    """

    id: str
    entity_type: EntityType
    name: str
    risk_score: float = 0.0
    confidence_level: float = 0.0
