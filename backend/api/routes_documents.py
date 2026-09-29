from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.database.crud import get_documents
from backend.models.schemas import DocumentResponse, DocumentDetailResponse
from backend.services.document_service import document_service
from backend.utils.logger import get_logger

logger = get_logger("routes_documents")
router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    source: str = Form("Uploaded Document"),
    version: str = Form("1.0"),
    topic: str = Form("General"),
    document_date: str = Form(""),
    db: Session = Depends(get_db)
):
    """Uploads and ingests a PDF or TXT document into knowledge base & vector store."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    suffix = file.filename.split(".")[-1].lower()
    if suffix not in ["pdf", "txt", "md", "json"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: .{suffix}. Supported formats: PDF, TXT."
        )

    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        doc_entity = document_service.process_and_save_upload(
            file_bytes=content,
            filename=file.filename,
            source=source,
            version=version,
            topic=topic,
            document_date=document_date,
            db=db
        )
        return DocumentResponse(
            id=doc_entity.id,
            filename=doc_entity.filename,
            source=doc_entity.source,
            version=doc_entity.version,
            topic=doc_entity.topic,
            document_date=doc_entity.document_date,
            status=doc_entity.status,
            uploaded_at=doc_entity.uploaded_at,
            chunk_count=len(doc_entity.chunks)
        )
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to process document {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal document ingestion error: {str(e)}")


@router.get("", response_model=List[DocumentResponse])
def list_documents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lists all stored documents with their chunk counts and ingestion metadata."""
    return get_documents(db, skip=skip, limit=limit)


@router.get("/{doc_id}", response_model=DocumentDetailResponse)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    """Retrieves document metadata along with all extracted knowledge chunks."""
    details = document_service.get_document_details(doc_id, db)
    if not details:
        raise HTTPException(status_code=404, detail=f"Document #{doc_id} not found.")
    return details


@router.delete("/{doc_id}", status_code=status.HTTP_200_OK)
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """Deletes a document from the database and deletes its embeddings from ChromaDB."""
    success = document_service.remove_document(doc_id, db)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document #{doc_id} not found.")
    return {"message": f"Document #{doc_id} and its vector chunks deleted successfully."}
