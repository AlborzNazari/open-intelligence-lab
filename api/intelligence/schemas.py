"""
api/intelligence/schemas.py  —  v0.6.1
Pydantic response models for Open Intelligence Lab API.
"""

from pydantic import BaseModel


class RiskResponse(BaseModel):
    entity_id: str
    risk_score: float
    explanation: str | None = None
    api_version: str = "0.6.1"
