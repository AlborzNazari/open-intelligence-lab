from dataclasses import dataclass
from typing import Literal


EntityType = Literal[
    "organization",
    "domain",
    "incident_category",
]


@dataclass
class IntelligenceEntity:
    id: str
    entity_type: EntityType
    name: str
    risk_score: float = 0.0
    confidence_level: float = 0.0
