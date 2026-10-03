import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from backend.models.entities import DocumentEntity, KnowledgeChunkEntity, InvestigationEntity, EvidenceEntity
from backend.models.schemas import DocumentResponse, InvestigationResponse, EvidenceItem, InvestigationStep


# Documents CRUD
def create_document(
    db: Session,
    filename: str,
    source: str = "Uploaded Document",
    version: str = "1.0",
    topic: str = "General",
    document_date: str = "",
    status: str = "ready"
) -> DocumentEntity:
    if not document_date:
        document_date = datetime.utcnow().strftime("%Y-%m-%d")
    doc = DocumentEntity(
        filename=filename,
        source=source,
        version=version,
        topic=topic,
        document_date=document_date,
        status=status,
        uploaded_at=datetime.utcnow()
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_documents(db: Session, skip: int = 0, limit: int = 100) -> List[DocumentResponse]:
    docs = db.query(DocumentEntity).order_by(desc(DocumentEntity.uploaded_at)).offset(skip).limit(limit).all()
    result = []
    for d in docs:
        chunk_count = db.query(func.count(KnowledgeChunkEntity.id)).filter(KnowledgeChunkEntity.document_id == d.id).scalar() or 0
        result.append(DocumentResponse(
            id=d.id,
            filename=d.filename,
            source=d.source,
            version=d.version,
            topic=d.topic,
            document_date=d.document_date,
            status=d.status,
            uploaded_at=d.uploaded_at,
            chunk_count=chunk_count
        ))
    return result


def get_document_by_id(db: Session, doc_id: int) -> Optional[DocumentEntity]:
    return db.query(DocumentEntity).filter(DocumentEntity.id == doc_id).first()


def delete_document(db: Session, doc_id: int) -> bool:
    doc = get_document_by_id(db, doc_id)
    if not doc:
        return False
    db.delete(doc)
    db.commit()
    return True


# Knowledge Chunks CRUD
def create_knowledge_chunk(
    db: Session,
    document_id: int,
    chunk_text: str,
    chunk_index: int = 0,
    page: int = 1,
    metadata: Optional[Dict[str, Any]] = None
) -> KnowledgeChunkEntity:
    if metadata is None:
        metadata = {}
    if "page" not in metadata:
        metadata["page"] = page
    chunk = KnowledgeChunkEntity(
        document_id=document_id,
        chunk_text=chunk_text,
        chunk_index=chunk_index,
        page=page,
        metadata_json=json.dumps(metadata)
    )
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return chunk


def get_chunks_for_document(db: Session, doc_id: int) -> List[KnowledgeChunkEntity]:
    return db.query(KnowledgeChunkEntity).filter(KnowledgeChunkEntity.document_id == doc_id).order_by(KnowledgeChunkEntity.chunk_index).all()


# Investigations CRUD
def create_investigation(
    db: Session,
    claim: str,
    classification: str,
    explanation: str,
    confidence: float,
    recommendation: str,
    human_verification_required: bool,
    steps: Optional[List[Dict[str, Any]]] = None,
    comparison: str = "",
    human_review_status: str = "Pending Review",
    execution_time_ms: float = 0.0,
    research_occurred: bool = False,
    retrieval_attempts: int = 1,
    unique_documents: int = 1,
    evidence_sufficient: bool = True,
    structured_explanation: Optional[Dict[str, Any]] = None
) -> InvestigationEntity:
    metadata = {
        "steps": steps or [],
        "comparison": comparison,
        "retrieval_attempts": retrieval_attempts,
        "unique_documents": unique_documents,
        "evidence_sufficient": evidence_sufficient,
        "structured_explanation": structured_explanation or {}
    }
    inv = InvestigationEntity(
        claim=claim,
        classification=classification,
        explanation=explanation,
        confidence=confidence,
        recommendation=recommendation,
        human_verification_required=human_verification_required,
        human_review_status=human_review_status,
        execution_time_ms=execution_time_ms,
        research_occurred=research_occurred,
        created_at=datetime.utcnow(),
        metadata_json=json.dumps(metadata)
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


def update_investigation_review_status(db: Session, inv_id: int, new_status: str) -> Optional[InvestigationEntity]:
    inv = db.query(InvestigationEntity).filter(InvestigationEntity.id == inv_id).first()
    if not inv:
        return None
    inv.human_review_status = new_status
    db.commit()
    db.refresh(inv)
    return inv


def add_evidence_to_investigation(
    db: Session,
    investigation_id: int,
    evidence_text: str,
    relevance_score: float = 0.0,
    document_id: Optional[int] = None,
    chunk_id: Optional[int] = None,
    source: str = "",
    version: str = "",
    date: str = "",
    page: int = 1,
    is_stored_knowledge: bool = False
) -> EvidenceEntity:
    # Foreign key safety for PostgreSQL: verify referenced IDs exist before linking
    valid_doc_id = None
    if document_id is not None:
        if db.query(DocumentEntity.id).filter(DocumentEntity.id == document_id).first():
            valid_doc_id = document_id
        else:
            logger.warning(f"Referenced document_id {document_id} not found in database; setting evidence document_id to NULL to prevent FK violation.")

    valid_chunk_id = None
    if chunk_id is not None:
        if db.query(KnowledgeChunkEntity.id).filter(KnowledgeChunkEntity.id == chunk_id).first():
            valid_chunk_id = chunk_id
        else:
            logger.warning(f"Referenced chunk_id {chunk_id} not found in database; setting evidence chunk_id to NULL to prevent FK violation.")

    ev = EvidenceEntity(
        investigation_id=investigation_id,
        document_id=valid_doc_id,
        chunk_id=valid_chunk_id,
        evidence_text=evidence_text,
        relevance_score=relevance_score,
        source=source,
        version=version,
        date=date,
        page=page,
        is_stored_knowledge=is_stored_knowledge
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def _parse_steps(raw_steps: Any) -> List[InvestigationStep]:
    """Safely normalizes and parses agent execution steps from JSON metadata."""
    if not isinstance(raw_steps, list):
        return []
    parsed = []
    for s in raw_steps:
        try:
            if isinstance(s, dict):
                step_name = (
                    s.get("step_name")
                    or s.get("name")
                    or (f"Step {s['step']}" if "step" in s else None)
                    or "Investigation Step"
                )
                desc = s.get("description") or s.get("desc") or ""
                status = s.get("status") or "completed"
                details = s.get("details") if isinstance(s.get("details"), dict) else None
                parsed.append(InvestigationStep(
                    step_name=str(step_name),
                    description=str(desc),
                    status=str(status),
                    details=details
                ))
            elif isinstance(s, str):
                parsed.append(InvestigationStep(
                    step_name="Agent Action",
                    description=str(s),
                    status="completed"
                ))
        except Exception:
            continue
    return parsed


def _parse_evidences(evidences: Any) -> List[EvidenceItem]:
    """Safely constructs EvidenceItem objects from ORM entities."""
    items = []
    for e in evidences:
        try:
            items.append(EvidenceItem(
                id=e.id,
                document_id=e.document_id,
                chunk_id=e.chunk_id,
                evidence_text=e.evidence_text or "",
                relevance_score=float(e.relevance_score or 0.0),
                source=e.source or "",
                version=e.version or "",
                date=e.date or "",
                page=int(getattr(e, "page", 1) or 1),
                is_stored_knowledge=bool(getattr(e, "is_stored_knowledge", False))
            ))
        except Exception:
            continue
    return items


def get_investigations(db: Session, skip: int = 0, limit: int = 100) -> List[InvestigationResponse]:
    invs = db.query(InvestigationEntity).order_by(desc(InvestigationEntity.created_at)).offset(skip).limit(limit).all()
    results = []
    for inv in invs:
        ev_items = _parse_evidences(inv.evidences)
        meta = {}
        try:
            meta = json.loads(inv.metadata_json) if inv.metadata_json else {}
        except Exception:
            pass
        
        steps = _parse_steps(meta.get("steps", []) if isinstance(meta, dict) else [])
        results.append(InvestigationResponse(
            id=inv.id,
            claim=inv.claim or "",
            classification=inv.classification or "UNCERTAIN",
            explanation=inv.explanation or "",
            confidence=float(inv.confidence or 0.0),
            recommendation=inv.recommendation or "",
            human_verification_required=bool(inv.human_verification_required),
            human_review_status=getattr(inv, "human_review_status", "Pending Review") or "Pending Review",
            execution_time_ms=float(getattr(inv, "execution_time_ms", 0.0) or 0.0),
            research_occurred=bool(getattr(inv, "research_occurred", False)),
            retrieval_attempts=int(meta.get("retrieval_attempts", 1) if isinstance(meta, dict) else 1),
            unique_documents=int(meta.get("unique_documents", len(set(e.document_id for e in inv.evidences if e.document_id)) or 1) if isinstance(meta, dict) else 1),
            evidence_sufficient=bool(meta.get("evidence_sufficient", True) if isinstance(meta, dict) else True),
            created_at=inv.created_at,
            evidences=ev_items,
            steps=steps,
            comparison=meta.get("comparison", "") if isinstance(meta, dict) else "",
            structured_explanation=meta.get("structured_explanation") if (isinstance(meta, dict) and isinstance(meta.get("structured_explanation"), dict)) else None
        ))
    return results


def get_investigation_by_id(db: Session, inv_id: int) -> Optional[InvestigationResponse]:
    inv = db.query(InvestigationEntity).filter(InvestigationEntity.id == inv_id).first()
    if not inv:
        return None
    ev_items = _parse_evidences(inv.evidences)
    meta = {}
    try:
        meta = json.loads(inv.metadata_json) if inv.metadata_json else {}
    except Exception:
        pass
    
    steps = _parse_steps(meta.get("steps", []) if isinstance(meta, dict) else [])
    return InvestigationResponse(
        id=inv.id,
        claim=inv.claim or "",
        classification=inv.classification or "UNCERTAIN",
        explanation=inv.explanation or "",
        confidence=float(inv.confidence or 0.0),
        recommendation=inv.recommendation or "",
        human_verification_required=bool(inv.human_verification_required),
        human_review_status=getattr(inv, "human_review_status", "Pending Review") or "Pending Review",
        execution_time_ms=float(getattr(inv, "execution_time_ms", 0.0) or 0.0),
        research_occurred=bool(getattr(inv, "research_occurred", False)),
        retrieval_attempts=int(meta.get("retrieval_attempts", 1) if isinstance(meta, dict) else 1),
        unique_documents=int(meta.get("unique_documents", len(set(e.document_id for e in inv.evidences if e.document_id)) or 1) if isinstance(meta, dict) else 1),
        evidence_sufficient=bool(meta.get("evidence_sufficient", True) if isinstance(meta, dict) else True),
        created_at=inv.created_at,
        evidences=ev_items,
        steps=steps,
        comparison=meta.get("comparison", "") if isinstance(meta, dict) else "",
        structured_explanation=meta.get("structured_explanation") if (isinstance(meta, dict) and isinstance(meta.get("structured_explanation"), dict)) else None
    )



# Dashboard Statistics CRUD
def get_dashboard_statistics(db: Session) -> Dict[str, Any]:
    total_docs = db.query(func.count(DocumentEntity.id)).scalar() or 0
    total_chunks = db.query(func.count(KnowledgeChunkEntity.id)).scalar() or 0
    total_invs = db.query(func.count(InvestigationEntity.id)).scalar() or 0

    current_count = db.query(func.count(InvestigationEntity.id)).filter(InvestigationEntity.classification == "CURRENT").scalar() or 0
    outdated_count = db.query(func.count(InvestigationEntity.id)).filter(InvestigationEntity.classification == "OUTDATED").scalar() or 0
    conflicting_count = db.query(func.count(InvestigationEntity.id)).filter(InvestigationEntity.classification == "CONFLICTING").scalar() or 0
    uncertain_count = db.query(func.count(InvestigationEntity.id)).filter(InvestigationEntity.classification == "UNCERTAIN").scalar() or 0
    requires_review = db.query(func.count(InvestigationEntity.id)).filter(InvestigationEntity.human_verification_required == True).scalar() or 0

    recent_invs = get_investigations(db, skip=0, limit=5)
    recent_docs = get_documents(db, skip=0, limit=5)

    return {
        "total_knowledge_items": total_chunks,
        "total_documents": total_docs,
        "total_investigations": total_invs,
        "current_count": current_count,
        "outdated_count": outdated_count,
        "conflicting_count": conflicting_count,
        "uncertain_count": uncertain_count,
        "requires_review_count": requires_review,
        "recent_investigations": [i.dict() for i in recent_invs],
        "recent_documents": [d.dict() for d in recent_docs],
        "status_distribution": {
            "CURRENT": current_count,
            "OUTDATED": outdated_count,
            "CONFLICTING": conflicting_count,
            "UNCERTAIN": uncertain_count,
        }
    }
