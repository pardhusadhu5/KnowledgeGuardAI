from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict


class InvestigationState(TypedDict, total=False):
    claim: str
    expanded_queries: List[str]
    search_iteration: int
    retrieved_documents: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    source_metadata: List[Dict[str, Any]]
    additional_search_required: bool
    comparison: str
    classification: str  # CURRENT, OUTDATED, CONFLICTING, UNCERTAIN
    reasoning: str
    confidence: float
    recommendation: str
    human_verification_required: bool
    steps: List[Dict[str, Any]]
    error: Optional[str]
