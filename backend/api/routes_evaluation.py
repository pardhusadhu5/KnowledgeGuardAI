from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.crud import update_investigation_review_status, get_investigation_by_id
from backend.models.schemas import (
    EvaluationSummary,
    EvaluationResultItem,
    EvaluationRunResponse,
    ConfusionMatrixData,
    ReviewStatusUpdateRequest,
    InvestigationResponse
)
from backend.services.evaluation_service import evaluation_service
from backend.utils.logger import get_logger

logger = get_logger("routes_evaluation")
router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.post("/run", response_model=EvaluationRunResponse, status_code=status.HTTP_200_OK)
def run_evaluation_benchmark(db: Session = Depends(get_db)):
    """
    Executes the automated evaluation benchmark over the structured evaluation dataset.
    Runs each test case through the existing LangGraph Agent & Generative LLM pipeline,
    computes quantitative metrics (Accuracy, Precision, Recall, F1, Confusion Matrix),
    and persists the latest evaluation run.
    """
    try:
        response = evaluation_service.run_evaluation(db=db)
        return response
    except Exception as e:
        logger.error(f"Evaluation benchmark failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get("/summary", response_model=EvaluationSummary)
def get_evaluation_summary(db: Session = Depends(get_db)):
    """Retrieves the summary metrics of the latest evaluation run."""
    cached = evaluation_service.get_latest_data()
    if cached:
        return cached.summary
    # If no run has occurred yet, return an empty template
    return evaluation_service.calculate_metrics([])


@router.get("/results", response_model=List[EvaluationResultItem])
def get_evaluation_results():
    """Retrieves detailed per-case results of the latest evaluation run."""
    cached = evaluation_service.get_latest_data()
    if cached:
        return cached.results
    return []


@router.get("/confusion-matrix", response_model=ConfusionMatrixData)
def get_confusion_matrix():
    """Retrieves the 4x4 confusion matrix of the latest evaluation run."""
    cached = evaluation_service.get_latest_data()
    if cached:
        return cached.summary.confusion_matrix
    return ConfusionMatrixData(labels=["CURRENT", "OUTDATED", "CONFLICTING", "UNCERTAIN"], matrix=[[0]*4 for _ in range(4)])


@router.get("/export")
def export_evaluation_report():
    """Exports a formatted Markdown/Text report of the latest evaluation run."""
    content = evaluation_service.export_report_markdown()
    return Response(
        content=content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": "attachment; filename=KnowledgeGuard_Evaluation_Report.md"
        }
    )


# Review status update route
review_router = APIRouter(tags=["Investigation"])

@review_router.patch("/investigations/{inv_id}/review-status", response_model=InvestigationResponse)
def update_review_status(inv_id: int, req: ReviewStatusUpdateRequest, db: Session = Depends(get_db)):
    """Allows an operator to update human verification status (Pending Review, Reviewed, Accepted, Rejected)."""
    updated = update_investigation_review_status(db=db, inv_id=inv_id, new_status=req.status)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Investigation #{inv_id} not found.")
    return get_investigation_by_id(db=db, inv_id=inv_id)
