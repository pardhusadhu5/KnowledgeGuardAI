import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.crud import get_dashboard_statistics
from backend.models.schemas import DashboardStats
from backend.services.document_service import document_service
from backend.utils.config import SAMPLE_DOCS_DIR
from backend.utils.logger import get_logger

logger = get_logger("routes_dashboard")
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    """Computes and returns real-time dynamic statistics directly from the database."""
    stats = get_dashboard_statistics(db)
    return stats


@router.post("/seed-samples", status_code=status.HTTP_200_OK)
def seed_sample_documents(db: Session = Depends(get_db)):
    """
    Ingests official sample documents for the four evaluation scenarios:
    1. Outdated API v2 vs v3
    2. Supported Python 3.12 (Current)
    3. Conflicting Auth Policies (API Key vs OAuth 2.0)
    4. Uncertain / Incomplete Document Knowledge
    """
    if not SAMPLE_DOCS_DIR.exists():
        raise HTTPException(status_code=404, detail="Sample documents directory not found.")

    sample_files = list(SAMPLE_DOCS_DIR.glob("*.*"))
    if not sample_files:
        raise HTTPException(status_code=404, detail="No sample documents found to seed.")

    seeded = []
    for file_path in sample_files:
        if file_path.suffix.lower() not in [".txt", ".pdf", ".md"]:
            continue
        try:
            with open(file_path, "rb") as f:
                content = f.read()

            # Infer metadata from filename
            name = file_path.stem.lower()
            source = file_path.name
            version = "1.0"
            date = "2024-01-15"
            topic = "General"

            if "v2" in name:
                version = "2.0"
                date = "2024-03-01"
                topic = "API Architecture"
            elif "v3" in name:
                version = "3.0"
                date = "2026-02-15"
                topic = "API Architecture"
            elif "database" in name:
                topic = "Database & Storage"
                if "2026" in name or "migration" in name:
                    version = "3.1"
                    date = "2026-01-10"
                else:
                    version = "1.0"
                    date = "2023-04-15"
            elif "session" in name or "timeout" in name:
                topic = "Session Management"
                if "sec" in name:
                    version = "Sec-Policy-4"
                    date = "2025-09-01"
                else:
                    version = "Ops-Standard-2"
                    date = "2025-09-15"
            elif "container" in name or "k8s" in name:
                topic = "DevOps & Infrastructure"
                version = "2026.1"
                date = "2026-02-01"
            elif "backup" in name or "retention" in name:
                topic = "Cloud Operations"
                version = "2.4"
                date = "2026-01-05"
            elif "python" in name:
                topic = "Runtime Environment"
                if "update" in name or "2026" in name:
                    version = "2026.1"
                    date = "2026-01-20"
                else:
                    version = "2024.1"
                    date = "2024-10-10"
            elif "auth" in name or "security" in name:
                topic = "Security & Authentication"
                if "alpha" in name or "auth_a" in name or name.endswith("_a"):
                    version = "Policy-A"
                    date = "2025-06-01"
                else:
                    version = "Policy-B"
                    date = "2025-08-10"
            elif "network" in name or "quantum" in name:
                topic = "Infrastructure"
                version = "Draft-0.1"
                date = "2023-11-05"

            # Remove existing document with same filename to avoid redundant duplicate chunks
            from backend.models.entities import DocumentEntity
            existing_doc = db.query(DocumentEntity).filter(DocumentEntity.filename == file_path.name).first()
            if existing_doc:
                document_service.remove_document(existing_doc.id, db)

            doc = document_service.process_and_save_upload(
                file_bytes=content,
                filename=file_path.name,
                source=f"Enterprise Docs: {source}",
                version=version,
                topic=topic,
                document_date=date,
                db=db
            )
            seeded.append(doc.filename)
        except Exception as e:
            logger.warning(f"Could not seed {file_path.name}: {e}")

    return {
        "message": f"Successfully ingested {len(seeded)} sample documents into knowledge base.",
        "seeded_documents": seeded
    }
