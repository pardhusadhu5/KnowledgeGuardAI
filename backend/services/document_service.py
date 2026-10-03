import os
import json
import time
import shutil
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.utils.config import settings, UPLOAD_DIR
from backend.utils.logger import get_logger
from backend.rag.document_loader import (
    extract_text_from_file,
    iter_pdf_page_batches,
    DEFAULT_PAGE_BATCH_SIZE,
    MAX_TOTAL_PAGES
)
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

        logger.info(f"[Diagnostic: File Received] '{filename}' ({len(file_bytes)} bytes)")

        # Ensure upload directory exists safely
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        safe_filename = Path(filename).name
        # Use collision-safe file path
        unique_prefix = f"doc_{int(time.time())}"
        dest_path = UPLOAD_DIR / f"{unique_prefix}_{safe_filename}"
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
        logger.info(f"[Diagnostic: Database Initialized] Document record created with ID={doc.id}, status='processing'")

        # Purge any stale vectors for this document ID in case of re-processing
        vector_store.delete_document_chunks(doc.id)

        try:
            suffix = dest_path.suffix.lower()
            global_chunk_idx = 0
            total_pages_count = 1

            if suffix == ".pdf":
                # Process PDF in page-batches to avoid memory spikes and Render timeouts
                total_batches_count = 0
                for batch in iter_pdf_page_batches(
                    dest_path,
                    batch_size=DEFAULT_PAGE_BATCH_SIZE,
                    max_total_pages=MAX_TOTAL_PAGES
                ):
                    b_idx = batch["batch_index"]
                    total_batches = batch["total_batches"]
                    start_page = batch["start_page"]
                    end_page = batch["end_page"]
                    total_pages_count = batch["total_pages"]
                    total_batches_count = total_batches

                    if b_idx == 1:
                        logger.info(f"Processing PDF: {total_pages_count} pages ({total_batches} batches)")

                    logger.info(f"Batch {b_idx}/{total_batches}: pages {start_page}–{end_page}")

                    batch_chunk_texts: List[str] = []
                    batch_chunk_ids: List[str] = []
                    batch_chunk_metas: List[Dict[str, Any]] = []

                    for page_item in batch["pages"]:
                        page_num = page_item["page_number"]
                        page_text = page_item["text"]
                        if not page_text:
                            continue

                        # Split page text into overlapping chunks
                        page_chunks = split_text_into_chunks(page_text, chunk_size=380, chunk_overlap=50)

                        for local_c_idx, c_text in enumerate(page_chunks):
                            chunk_id_str = f"doc_{doc.id}_p{page_num}_c{local_c_idx}"

                            # Persist chunk to relational database with page number and provenance
                            create_knowledge_chunk(
                                db=db,
                                document_id=doc.id,
                                chunk_text=c_text,
                                chunk_index=global_chunk_idx,
                                page=page_num,
                                metadata={
                                    "source": doc.source,
                                    "version": doc.version,
                                    "date": doc.document_date,
                                    "topic": doc.topic,
                                    "filename": doc.filename,
                                    "page": page_num,
                                    "chunk_id_str": chunk_id_str
                                }
                            )

                            # Accumulate for batch ChromaDB insertion
                            batch_chunk_texts.append(c_text)
                            batch_chunk_ids.append(chunk_id_str)
                            batch_chunk_metas.append({
                                "document_id": doc.id,
                                "chunk_index": global_chunk_idx,
                                "page": page_num,
                                "source": doc.source,
                                "version": doc.version,
                                "topic": doc.topic,
                                "document_date": doc.document_date,
                                "filename": doc.filename,
                            })
                            global_chunk_idx += 1

                    # Index batch vector embeddings into ChromaDB
                    if batch_chunk_texts:
                        logger.info(f"Indexing pages {start_page}–{end_page}... ({len(batch_chunk_texts)} chunks)")
                        vector_store.add_chunks_with_metadata(
                            chunk_ids=batch_chunk_ids,
                            chunks=batch_chunk_texts,
                            metadatas=batch_chunk_metas
                        )

                if global_chunk_idx == 0:
                    raise ValueError("No readable text chunks could be extracted from PDF document.")

                logger.info(f"PDF processing completed: {total_pages_count} pages processed, {global_chunk_idx} total chunks generated and indexed.")

            elif suffix in [".txt", ".md", ".json", ".csv"]:
                # Process plain text documents
                cleaned_text, doc_type = extract_text_from_file(dest_path)
                chunks = split_text_into_chunks(cleaned_text, chunk_size=380, chunk_overlap=50)
                if not chunks:
                    raise ValueError("No readable text chunks could be extracted from document.")

                chunk_ids = []
                chunk_metas = []
                for idx, chunk_text in enumerate(chunks):
                    cid = f"doc_{doc.id}_p1_c{idx}"
                    create_knowledge_chunk(
                        db=db,
                        document_id=doc.id,
                        chunk_text=chunk_text,
                        chunk_index=idx,
                        page=1,
                        metadata={
                            "source": doc.source,
                            "version": doc.version,
                            "date": doc.document_date,
                            "topic": doc.topic,
                            "filename": doc.filename,
                            "page": 1,
                            "chunk_id_str": cid
                        }
                    )
                    chunk_ids.append(cid)
                    chunk_metas.append({
                        "document_id": doc.id,
                        "chunk_index": idx,
                        "page": 1,
                        "source": doc.source,
                        "version": doc.version,
                        "topic": doc.topic,
                        "document_date": doc.document_date,
                        "filename": doc.filename,
                    })

                vector_store.add_chunks_with_metadata(
                    chunk_ids=chunk_ids,
                    chunks=chunks,
                    metadatas=chunk_metas
                )
                global_chunk_idx = len(chunks)
                logger.info(f"Text document processing completed: {global_chunk_idx} chunks indexed.")

            else:
                raise ValueError(f"Unsupported file format: {suffix}. Only PDF and TXT documents are supported.")

            # Mark document record as ready
            doc.status = "ready"
            db.commit()
            db.refresh(doc)
            logger.info(f"[Diagnostic: Success] Successfully processed and indexed document '{safe_filename}' (id={doc.id}, total_chunks={global_chunk_idx})")
            return doc

        except Exception as e:
            logger.error(f"[Diagnostic: Failure] Error processing document '{safe_filename}': {e}", exc_info=True)
            doc.status = "error"
            db.commit()
            raise
        finally:
            # Safe cleanup of temporary upload file
            try:
                if dest_path.exists():
                    dest_path.unlink()
            except Exception:
                pass

    def remove_document(self, doc_id: int, db: Session) -> bool:
        doc = get_document_by_id(db, doc_id)
        if not doc:
            return False
        
        # Remove from vector store
        vector_store.delete_document_chunks(doc_id)
        
        # Remove file from uploads if exists
        try:
            upload_path = Path(settings.UPLOAD_DIR)
            file_path = upload_path / doc.filename
            if file_path.exists():
                file_path.unlink()
            for f in upload_path.glob(f"*_{doc.filename}"):
                try:
                    f.unlink()
                except Exception:
                    pass
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
                    "page": getattr(c, "page", 1) or 1,
                    "chunk_text": c.chunk_text,
                    "metadata": json.loads(c.metadata_json) if c.metadata_json else {"page": getattr(c, "page", 1) or 1}
                }
                for c in chunks
            ]
        }


document_service = DocumentService()
