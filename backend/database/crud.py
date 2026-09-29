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
    metadata: Optional[Dict[str, Any]] = None
) -> KnowledgeChunkEntity:
    chunk = KnowledgeChunkEntity(
        document_id=document_id,
        chunk_text=chunk_text,
        chunk_index=chunk_index,
        metadata_json=json.dumps(metadata or {})
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
    comparison: str = ""
) -> InvestigationEntity:
    metadata = {
        "steps": steps or [],
        "comparison": comparison
    }
    inv = InvestigationEntity(
        claim=claim,
        classification=classification,
        explanation=explanation,
        confidence=confidence,
        recommendation=recommendation,
        human_verification_required=human_verification_required,
        created_at=datetime.utcnow(),
        metadata_json=json.dumps(metadata)
    )
    db.add(inv)
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
    is_stored_knowledge: bool = False
) -> EvidenceEntity:
    ev = EvidenceEntity(
        investigation_id=investigation_id,
        document_id=document_id,
        chunk_id=chunk_id,
        evidence_text=evidence_text,
        relevance_score=relevance_score,
        source=source,
        version=version,
        date=date,
        is_stored_knowledge=is_stored_knowledge
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def get_investigations(db: Session, skip: int = 0, limit: int = 100) -> List[InvestigationResponse]:
    invs = db.query(InvestigationEntity).order_by(desc(InvestigationEntity.created_at)).offset(skip).limit(limit).all()
    results = []
    for inv in invs:
        ev_items = [
            EvidenceItem(
                id=e.id,
                document_id=e.document_id,
                chunk_id=e.chunk_id,
                evidence_text=e.evidence_text,
                relevance_score=e.relevance_score,
                source=e.source,
                version=e.version,
                date=e.date,
                is_stored_knowledge=e.is_stored_knowledge
            )
            for e in inv.evidences
        ]
        meta = {}
        try:
            meta = json.loads(inv.metadata_json) if inv.metadata_json else {}
        except Exception:
            pass
        
        steps = [InvestigationStep(**s) for s in meta.get("steps", [])]
        results.append(InvestigationResponse(
            id=inv.id,
            claim=inv.claim,
            classification=inv.classification,
            explanation=inv.explanation,
            confidence=inv.confidence,
            recommendation=inv.recommendation,
            human_verification_required=inv.human_verification_required,
            created_at=inv.created_at,
            evidences=ev_items,
            steps=steps,
            comparison=meta.get("comparison", "")
        ))
    return results


def get_investigation_by_id(db: Session, inv_id: int) -> Optional[InvestigationResponse]:
    inv = db.query(InvestigationEntity).filter(InvestigationEntity.id == inv_id).first()
    if not inv:
        return None
    ev_items = [
        EvidenceItem(
            id=e.id,
            document_id=e.document_id,
            chunk_id=e.chunk_id,
            evidence_text=e.evidence_text,
            relevance_score=e.relevance_score,
            source=e.source,
            version=e.version,
            date=e.date,
            is_stored_knowledge=e.is_stored_knowledge
        )
        for e in inv.evidences
    ]
    meta = {}
    try:
        meta = json.loads(inv.metadata_json) if inv.metadata_json else {}
    except Exception:
        pass
    
    steps = [InvestigationStep(**s) for s in meta.get("steps", [])]
    return InvestigationResponse(
        id=inv.id,
        claim=inv.claim,
        classification=inv.classification,
        explanation=inv.explanation,
        confidence=inv.confidence,
        recommendation=inv.recommendation,
        human_verification_required=inv.human_verification_required,
        created_at=inv.created_at,
        evidences=ev_items,
        steps=steps,
        comparison=meta.get("comparison", "")
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
