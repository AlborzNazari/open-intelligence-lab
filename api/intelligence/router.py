from fastapi import APIRouter, HTTPException
from .service import analyze_entity
from .schemas import RiskResponse

router = APIRouter(prefix="/intelligence", tags=["Intelligence API"])

@router.get("/risk/{entity_id}", response_model=RiskResponse)
def get_risk(entity_id: str):
    try:
        result = analyze_entity(entity_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
