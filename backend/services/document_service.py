import os
import shutil
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.utils.config import settings, UPLOAD_DIR
from backend.utils.logger import get_logger
from backend.rag.document_loader import extract_text_from_file
from backend.rag.text_splitter import split_text_into_chunks
from backend.rag.vector_store import vector_store
from backend.database.crud import (
    create_document,
    create_knowledge_chunk,
    get_document_by_id,
    delete_document as crud_delete_document,
    get_chunks_for_document
)
from backend.models.entities import DocumentEntity

logger = get_logger("document_service")


class DocumentService:
    def process_and_save_upload(
        self,
        file_bytes: bytes,
        filename: str,
        source: str,
        version: str,
        topic: str,
        document_date: str,
        db: Session
    ) -> DocumentEntity:
        if not file_bytes:
            raise ValueError("Uploaded file is empty.")

        # Save to disk
        safe_filename = Path(filename).name
        dest_path = UPLOAD_DIR / safe_filename
        with open(dest_path, "wb") as f:
            f.write(file_bytes)

        # 1. Create DB record with status "processing"
        doc = create_document(
            db=db,
            filename=safe_filename,
            source=source or safe_filename,
            version=version or "1.0",
            topic=topic or "General",
            document_date=document_date,
            status="processing"
        )

        try:
            # 2. Extract & clean text
            cleaned_text, doc_type = extract_text_from_file(dest_path)
            
            # 3. Split into chunks
            chunks = split_text_into_chunks(cleaned_text, chunk_size=380, chunk_overlap=50)
            if not chunks:
                raise ValueError("No readable text chunks could be extracted from document.")

            # 4. Save chunks in DB
            for idx, chunk_text in enumerate(chunks):
                create_knowledge_chunk(
                    db=db,
                    document_id=doc.id,
                    chunk_text=chunk_text,
                    chunk_index=idx,
                    metadata={
                        "source": doc.source,
                        "version": doc.version,
                        "date": doc.document_date,
                        "topic": doc.topic,
                        "filename": doc.filename
                    }
                )

            # 5. Index into ChromaDB vector store
            vector_store.add_chunks(
                document_id=doc.id,
                chunks=chunks,
                base_metadata={
                    "source": doc.source,
                    "version": doc.version,
                    "topic": doc.topic,
                    "document_date": doc.document_date,
                    "filename": doc.filename
                }
            )

            # 6. Mark ready
            doc.status = "ready"
            db.commit()
            db.refresh(doc)
            logger.info(f"Successfully processed document '{safe_filename}' (id={doc.id}, chunks={len(chunks)})")
            return doc

        except Exception as e:
            logger.error(f"Error processing document '{safe_filename}': {e}")
            doc.status = "error"
            db.commit()
            raise

    def remove_document(self, doc_id: int, db: Session) -> bool:
        doc = get_document_by_id(db, doc_id)
        if not doc:
            return False
        
        # Remove from vector store
        vector_store.delete_document_chunks(doc_id)
        
        # Remove file from uploads if exists
        try:
            file_path = UPLOAD_DIR / doc.filename
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.warning(f"Could not delete physical file for doc {doc_id}: {e}")

        # Delete from SQLite
        return crud_delete_document(db, doc_id)

    def get_document_details(self, doc_id: int, db: Session) -> Dict[str, Any]:
        doc = get_document_by_id(db, doc_id)
        if not doc:
            return None
        chunks = get_chunks_for_document(db, doc_id)
        return {
            "id": doc.id,
            "filename": doc.filename,
            "source": doc.source,
            "version": doc.version,
            "topic": doc.topic,
            "document_date": doc.document_date,
            "status": doc.status,
            "uploaded_at": doc.uploaded_at,
            "chunk_count": len(chunks),
            "chunks": [
                {
                    "id": c.id,
                    "chunk_index": c.chunk_index,
                    "chunk_text": c.chunk_text
                }
                for c in chunks
            ]
        }


document_service = DocumentService()
