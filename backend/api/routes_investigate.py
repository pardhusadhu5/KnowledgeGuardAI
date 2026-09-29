from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.crud import get_investigations, get_investigation_by_id
from backend.models.schemas import InvestigateRequest, InvestigationResponse
from backend.services.investigation_service import investigation_service
from backend.utils.logger import get_logger

logger = get_logger("routes_investigate")
router = APIRouter(tags=["Investigation"])


@router.post("/investigate", response_model=InvestigationResponse, status_code=status.HTTP_200_OK)
def investigate_claim(req: InvestigateRequest, db: Session = Depends(get_db)):
    """
    Executes the multi-step Knowledge Investigator Agent via LangGraph.
    Retrieves evidence from ChromaDB, evaluates claim truthfulness, performs LLM reasoning,
    and returns a structured verdict: CURRENT, OUTDATED, CONFLICTING, or UNCERTAIN.
    """
    claim = req.claim.strip()
    if not claim:
        raise HTTPException(status_code=400, detail="Claim cannot be empty.")

    try:
        result = investigation_service.investigate_claim(claim=claim, db=db)
        return result
    except Exception as e:
        logger.error(f"Investigation execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Investigation workflow error: {str(e)}")


@router.get("/investigations", response_model=List[InvestigationResponse])
def list_investigations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieves all past investigations, classifications, and evidence links."""
    return get_investigations(db, skip=skip, limit=limit)


@router.get("/investigations/{inv_id}", response_model=InvestigationResponse)
def get_investigation(inv_id: int, db: Session = Depends(get_db)):
    """Retrieves details of a specific investigation including all evidence items and agent steps."""
    result = get_investigation_by_id(db, inv_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Investigation #{inv_id} not found.")
    return result
