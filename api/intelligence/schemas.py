from pydantic import BaseModel

class RiskResponse(BaseModel):
    entity_id: str
    risk_score: float
    explanation: str | None = None
