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
    created_at: datetime
    evidences: List[EvidenceItem] = []
    steps: List[InvestigationStep] = []
    comparison: Optional[str] = ""

    class Config:
        from_attributes = True


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
