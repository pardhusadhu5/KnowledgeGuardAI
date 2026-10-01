from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


# Document Schemas
class DocumentBase(BaseModel):
    filename: str
    source: str = "Uploaded Document"
    version: str = "1.0"
    topic: str = "General"
    document_date: str = ""
    status: str = "ready"


class DocumentResponse(DocumentBase):
    id: int
    uploaded_at: datetime
    chunk_count: int = 0

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    chunks: List[Dict[str, Any]] = []


# Investigation Schemas
class InvestigateRequest(BaseModel):
    claim: str = Field(..., min_length=3, description="Claim or statement to investigate")


class EvidenceItem(BaseModel):
    id: Optional[int] = None
    document_id: Optional[int] = None
    chunk_id: Optional[int] = None
    evidence_text: str
    relevance_score: float = 0.0
    source: str = ""
    version: str = ""
    date: str = ""
    is_stored_knowledge: bool = False


class InvestigationStep(BaseModel):
    step_name: str
    description: str
    status: str = "completed"  # pending, running, completed, skipped
    details: Optional[Dict[str, Any]] = None


class InvestigationResponse(BaseModel):
    id: int
    claim: str
    classification: str  # CURRENT, OUTDATED, CONFLICTING, UNCERTAIN
    explanation: str
    confidence: float
    recommendation: str
    human_verification_required: bool
    human_review_status: str = "Pending Review"  # Pending Review, Reviewed, Accepted, Rejected
    execution_time_ms: float = 0.0
    research_occurred: bool = False
    retrieval_attempts: int = 1
    unique_documents: int = 1
    evidence_sufficient: bool = True
    created_at: datetime
    evidences: List[EvidenceItem] = []
    steps: List[InvestigationStep] = []
    comparison: Optional[str] = ""
    structured_explanation: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ReviewStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(Pending Review|Reviewed|Accepted|Rejected)$")


# Evaluation Schemas
class ClassMetric(BaseModel):
    verdict: str
    precision: float
    recall: float
    f1_score: float
    support: int


class ConfusionMatrixData(BaseModel):
    labels: List[str]
    matrix: List[List[int]]


class EvaluationResultItem(BaseModel):
    id: str
    claim: str
    expected_verdict: str
    predicted_verdict: str
    confidence: float
    is_correct: bool
    evidence_count: int
    research_occurred: bool
    execution_time_ms: float
    reason: Optional[str] = ""
    explanation: Optional[str] = ""
    retrieved_documents: List[str] = []


class EvaluationSummary(BaseModel):
    total_test_cases: int
    correct_predictions: int
    incorrect_predictions: int
    overall_accuracy: float
    average_confidence: float
    average_execution_time_ms: float
    total_researches_triggered: int
    class_metrics: List[ClassMetric] = []
    confusion_matrix: ConfusionMatrixData
    last_run_timestamp: Optional[str] = None


class EvaluationRunResponse(BaseModel):
    summary: EvaluationSummary
    results: List[EvaluationResultItem] = []


class DashboardStats(BaseModel):
    total_knowledge_items: int
    total_documents: int
    total_investigations: int
    current_count: int
    outdated_count: int
    conflicting_count: int
    uncertain_count: int
    requires_review_count: int
    recent_investigations: List[InvestigationResponse] = []
    recent_documents: List[DocumentResponse] = []
    status_distribution: Dict[str, int] = {}
