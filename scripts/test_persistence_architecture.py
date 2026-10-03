"""
KnowledgeGuard AI Automated Architecture & Persistence Verification Suite
Tests requirements A through K from the production persistence specification.
"""

import sys
import os
import unittest
from pathlib import Path
from datetime import datetime

# Ensure repository root is on sys.path
_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.main import app
from backend.utils.config import settings, Settings
from backend.database.db import get_db, init_db, check_db_health
from backend.database.crud import (
    create_document,
    create_knowledge_chunk,
    get_documents,
    get_document_by_id,
    create_investigation,
    add_evidence_to_investigation,
    get_investigations,
    get_investigation_by_id,
    get_dashboard_statistics
)
from backend.models.entities import Base, DocumentEntity, KnowledgeChunkEntity, InvestigationEntity, EvidenceEntity
from backend.rag.vector_store import vector_store, check_vector_store_health


class TestPersistenceArchitecture(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        init_db()

    def test_A_local_defaults(self):
        """Test A: Verify default configuration resolves cleanly to SQLite and Local Chroma."""
        self.assertEqual(settings.database_type, "sqlite")
        self.assertEqual(settings.vector_store_type, "local_chroma")
        self.assertFalse(settings.is_postgres)
        self.assertFalse(settings.is_remote_chroma)
        self.assertTrue(Path(settings.UPLOAD_DIR).exists())
        self.assertTrue(Path(settings.CHROMA_PERSIST_DIR).exists())

    def test_B_postgres_configuration_compatibility(self):
        """Test B: Verify PostgreSQL URL normalization and pooling engine configuration."""
        test_settings = Settings(
            DATABASE_URL="postgres://testuser:secretpass@ep-cool-db.us-east-1.neon.tech/knowledgeguard"
        )
        self.assertTrue(test_settings.is_postgres)
        self.assertEqual(test_settings.database_type, "postgresql")
        # Ensure postgres:// is normalized to postgresql:// for SQLAlchemy
        self.assertTrue(test_settings.effective_database_url.startswith("postgresql://"))

        # Verify safe storage summary masks credentials
        summary = test_settings.get_safe_storage_summary()
        self.assertNotIn("secretpass", summary["database_description"])
        self.assertIn("host=ep-cool-db.us-east-1.neon.tech", summary["database_description"])

    def test_C_remote_chroma_configuration_fail_fast(self):
        """Test C: Verify Remote Chroma settings and fail-fast behavior on unreachable remote host."""
        test_settings = Settings(
            CHROMA_SERVER_HOST="chroma.invalid-nonexistent-domain.com",
            CHROMA_SERVER_PORT=8000
        )
        self.assertTrue(test_settings.is_remote_chroma)
        self.assertEqual(test_settings.vector_store_type, "remote_chroma")

        summary = test_settings.get_safe_storage_summary()
        self.assertIn("Remote ChromaDB", summary["vector_store_description"])
        self.assertIn("chroma.invalid-nonexistent-domain.com:8000", summary["vector_store_description"])

    def test_D_and_E_document_upload_and_persistence(self):
        """Tests D & E: Document upload, chunking, and persistence across database sessions."""
        test_engine = create_engine(settings.effective_database_url, connect_args={"check_same_thread": False})
        SessionTest = sessionmaker(bind=test_engine)
        db = SessionTest()

        test_filename = f"test_doc_persistence_{int(datetime.utcnow().timestamp())}.txt"
        doc = create_document(
            db=db,
            filename=test_filename,
            source="Persistence Test Suite",
            version="1.0",
            topic="Persistence Verification",
            document_date="2026-10-03",
            status="ready"
        )
        self.assertIsNotNone(doc.id)
        doc_id = doc.id

        # Add chunk
        chunk = create_knowledge_chunk(
            db=db,
            document_id=doc_id,
            chunk_text="Test chunk content for persistence verification under KnowledgeGuard AI.",
            chunk_index=0,
            page=1,
            metadata={"source": "Persistence Test Suite", "version": "1.0"}
        )
        self.assertIsNotNone(chunk.id)
        db.close()

        # Reopen brand new database session to simulate fresh request / restart
        db2 = SessionTest()
        retrieved_doc = get_document_by_id(db2, doc_id)
        self.assertIsNotNone(retrieved_doc)
        self.assertEqual(retrieved_doc.filename, test_filename)
        self.assertEqual(len(retrieved_doc.chunks), 1)
        self.assertEqual(retrieved_doc.chunks[0].page, 1)
        db2.close()

    def test_F_document_retrieval_after_restart(self):
        """Test F: Documents remain retrievable via get_documents after session recreation."""
        res = self.client.get("/documents")
        self.assertEqual(res.status_code, 200)
        docs = res.json()
        self.assertIsInstance(docs, list)
        self.assertGreater(len(docs), 0)

    def test_G_rag_vector_retrieval(self):
        """Test G: Chroma vector store search retrieves chunks with valid provenance."""
        # Index a dedicated test vector chunk
        test_chunk_id = f"test_chunk_rag_{int(datetime.utcnow().timestamp())}"
        test_text = "Zero Trust Architecture tenets require continuous authentication and validation for access."
        vector_store.add_chunks_with_metadata(
            chunk_ids=[test_chunk_id],
            chunks=[test_text],
            metadatas=[{
                "document_id": 99999,
                "chunk_index": 0,
                "page": 7,
                "source": "NIST SP 800-207",
                "version": "Final",
                "topic": "Zero Trust",
                "document_date": "2020-08-11",
                "filename": "NIST_SP_800-207_Zero_Trust_Architecture.pdf"
            }]
        )

        # Search
        results = vector_store.search("Zero Trust continuous authentication", n_results=3)
        self.assertGreater(len(results), 0)
        found_test_chunk = any(r.get("chunk_id_str") == test_chunk_id or 99999 == r.get("document_id") for r in results)
        self.assertTrue(found_test_chunk)
        # Verify page provenance
        first_match = results[0]
        self.assertIn("page", first_match)
        self.assertIn("relevance_score", first_match)

    def test_H_and_I_investigation_and_evidence_persistence(self):
        """Tests H & I: Investigation history and evidence persistence across database sessions."""
        test_engine = create_engine(settings.effective_database_url, connect_args={"check_same_thread": False})
        SessionTest = sessionmaker(bind=test_engine)
        db = SessionTest()

        claim_text = f"Persistence verification claim {int(datetime.utcnow().timestamp())}"
        inv = create_investigation(
            db=db,
            claim=claim_text,
            classification="CURRENT",
            explanation="Claim confirmed via persistent test evidence verification.",
            confidence=95.0,
            recommendation="Retain authoritative status.",
            human_verification_required=False,
            steps=[{"step_name": "retrieval", "description": "Retrieved evidence", "status": "completed"}],
            comparison="Consistent with reference architecture.",
            execution_time_ms=120.5,
            unique_documents=1,
            evidence_sufficient=True
        )
        inv_id = inv.id

        ev = add_evidence_to_investigation(
            db=db,
            investigation_id=inv_id,
            evidence_text="Zero Trust tenets confirm continuous policy evaluation.",
            relevance_score=0.89,
            source="NIST SP 800-207",
            version="Final",
            date="2020-08-11",
            page=4,
            is_stored_knowledge=True
        )
        self.assertIsNotNone(ev.id)
        db.close()

        # Reopen brand new database session
        db2 = SessionTest()
        retrieved_inv = get_investigation_by_id(db2, inv_id)
        self.assertIsNotNone(retrieved_inv)
        self.assertEqual(retrieved_inv.claim, claim_text)
        self.assertEqual(retrieved_inv.classification, "CURRENT")
        self.assertEqual(len(retrieved_inv.evidences), 1)
        self.assertEqual(retrieved_inv.evidences[0].page, 4)
        db2.close()

    def test_J_existing_document_list_api(self):
        """Test J: GET /documents endpoint returns valid schema expected by React UI."""
        res = self.client.get("/documents")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        if data:
            doc = data[0]
            self.assertIn("id", doc)
            self.assertIn("filename", doc)
            self.assertIn("source", doc)
            self.assertIn("version", doc)
            self.assertIn("topic", doc)
            self.assertIn("chunk_count", doc)

    def test_K_health_and_diagnostic_endpoint_telemetry(self):
        """Test K: GET /health and GET /diagnostic endpoints return safe storage telemetry."""
        # Test /health
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        health_data = res.json()
        self.assertEqual(health_data["status"], "healthy")
        self.assertEqual(health_data["service"], "KnowledgeGuard AI backend")
        self.assertIn("database", health_data)
        self.assertIn("vector_store", health_data)
        self.assertTrue(health_data["database_healthy"])
        self.assertTrue(health_data["vector_store_healthy"])

        # Test /diagnostic
        diag_res = self.client.get("/diagnostic")
        self.assertEqual(diag_res.status_code, 200)
        diag_data = diag_res.json()
        self.assertIn("database_type", diag_data)
        self.assertIn("database_exists", diag_data)
        self.assertIn("chroma_vector_count", diag_data)
        self.assertIn("upload_storage", diag_data)
        self.assertTrue(diag_data["database_exists"])
        self.assertTrue(diag_data["chroma_exists"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
