import os
import sys
import time
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.database.db import SessionLocal
from backend.services.document_service import document_service
from backend.services.investigation_service import InvestigationService
from backend.rag.vector_store import vector_store
from backend.database.crud import get_chunks_for_document

PDF_PATH = BASE_DIR / "data" / "knowledge_base" / "cybersecurity" / "NIST_SP_800-61r3_ipd_Incident_Response_Recommendations.pdf"

def run_test():
    print("=" * 80)
    print("VERIFYING COMPLETE BATCH PDF INGESTION & RAG ON PAGES 31-49")
    print("=" * 80)

    if not PDF_PATH.exists():
        print(f"[ERROR] PDF not found at: {PDF_PATH}")
        return

    db = SessionLocal()
    try:
        with open(PDF_PATH, "rb") as f:
            pdf_bytes = f.read()

        filename = "NIST.SP.800-61r3.pdf"
        print(f"\n1. Ingesting full PDF '{filename}' ({len(pdf_bytes)} bytes)...")
        start_t = time.perf_counter()

        doc = document_service.process_and_save_upload(
            file_bytes=pdf_bytes,
            filename=filename,
            source="National Institute of Standards and Technology (NIST) - NIST SP 800-61r3",
            version="Revision 3 (Draft)",
            topic="Incident Response",
            document_date="2024-04-10",
            db=db
        )
        ingest_duration = time.perf_counter() - start_t
        print(f"   [SUCCESS] Document ID: {doc.id}, Status: {doc.status}, Time: {ingest_duration:.2f}s")

        # Verify chunks created
        chunks = get_chunks_for_document(db, doc.id)
        print(f"\n2. Verifying chunks in Database:")
        print(f"   Total chunks created: {len(chunks)}")

        pages_represented = set()
        pages_31_plus_chunks = []
        for c in chunks:
            p = getattr(c, "page", 1) or 1
            pages_represented.add(p)
            if p >= 31:
                pages_31_plus_chunks.append(c)

        print(f"   Unique pages with indexed chunks: {len(pages_represented)} (Pages {min(pages_represented)} to {max(pages_represented)})")
        print(f"   Chunks on Pages 1-30: {len(chunks) - len(pages_31_plus_chunks)}")
        print(f"   Chunks on Pages 31-49: {len(pages_31_plus_chunks)}")

        if not pages_31_plus_chunks:
            print("   [FAIL] No chunks found for pages 31-49!")
            return
        else:
            print(f"   [PASS] Successfully indexed {len(pages_31_plus_chunks)} chunks from previously truncated pages (31-49)!")

        # 3. Test RAG Vector Retrieval specifically on Pages 31–48
        print("\n3. Testing RAG Vector Store Retrieval on Pages 31-48:")

        # Test A: Content from Glossary on Page 48 ("adverse cybersecurity event")
        query_a = "adverse cybersecurity event definition in NIST SP 800-61r3"
        print(f"\n   Query A: \"{query_a}\" (Expected: Page 48 Glossary)")
        results_a = vector_store.search(query=query_a, n_results=4)
        for idx, r in enumerate(results_a, 1):
            print(f"     Match #{idx}: Doc {r.get('document_id')} | Page {r.get('page')} | Score: {r.get('relevance_score'):.3f}")
            print(f"       Text: {r.get('chunk_text')[:140].strip()}...")

        top_page_a = results_a[0].get("page") if results_a else None
        print(f"   Top Match Page: {top_page_a}")

        # Test B: Content from Appendix A on Page 31 ("CSF Element PR Protect Priority Medium N1")
        query_b = "NIST SP 800-61r3 Protect PR Priority Medium Lowering the number of incidents shortens operational disruptions"
        print(f"\n   Query B: \"{query_b}\" (Expected: Page 31 Appendix A)")
        results_b = vector_store.search(query=query_b, n_results=4)
        for idx, r in enumerate(results_b, 1):
            print(f"     Match #{idx}: Doc {r.get('document_id')} | Page {r.get('page')} | Score: {r.get('relevance_score'):.3f}")
            print(f"       Text: {r.get('chunk_text')[:140].strip()}...")

        top_page_b = results_b[0].get("page") if results_b else None
        print(f"   Top Match Page: {top_page_b}")

        # 4. Test Full LangGraph Agent Investigation on Content from Page 48
        print("\n4. Running Full LangGraph Agent Investigation on Claim from Page 48:")
        claim = "According to NIST SP 800-61r3, an adverse cybersecurity event is defined as any event with a potentially negative impact on cybersecurity."
        inv_service = InvestigationService()
        inv_resp = inv_service.investigate_claim(claim=claim, db=db)

        print(f"   Classification: [{inv_resp.classification}]")
        print(f"   Confidence: {inv_resp.confidence}%")
        print(f"   Execution Time: {inv_resp.execution_time_ms}ms")
        print(f"   Explanation: {inv_resp.explanation}")
        print(f"   Evidence items retrieved: {len(inv_resp.evidences)}")
        for i, ev in enumerate(inv_resp.evidences[:3], 1):
            print(f"     Evidence #{i}: [{ev.source}] Page: {ev.page} | Score: {ev.relevance_score:.3f}")
            print(f"       Snippet: {ev.evidence_text[:140].strip()}...")

        # Verify pages 31-48 were retrieved
        retrieved_pages = [ev.page for ev in inv_resp.evidences]
        print(f"   Retrieved Evidence Pages: {retrieved_pages}")
        if any(p >= 31 for p in retrieved_pages if p):
            print("   [PASS] LangGraph Agent successfully reasoned over evidence retrieved from pages 31-48!")
        else:
            print("   [WARN] No pages >= 31 among top evidence items.")

    finally:
        db.close()

if __name__ == "__main__":
    run_test()
