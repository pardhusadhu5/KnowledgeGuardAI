import os
import sys
import json
import time
import requests
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KB_DIR = DATA_DIR / "knowledge_base"

# Ensure root paths are on sys.path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Define authoritative documents with complete provenance and version relationships
KNOWLEDGE_BASE_DOCUMENTS = [
    {
        "filename": "NIST_SP_800-61r2_Computer_Security_Incident_Handling_Guide.pdf",
        "title": "Computer Security Incident Handling Guide (Revision 2)",
        "organization": "National Institute of Standards and Technology (NIST)",
        "document_identifier": "NIST SP 800-61r2",
        "publication_date": "2012-08-01",
        "effective_date": "2012-08-01",
        "version": "Revision 2",
        "topic": "Incident Response",
        "category": "cybersecurity",
        "source_url": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf",
        "authority": "Official Standard (Superseded by Rev 3 IPD)",
        "relationship": {
            "status": "SUPERSEDED",
            "superseded_by": "NIST SP 800-61r3",
            "notes": "Classic 4-phase incident handling cycle (Preparation; Detection & Analysis; Containment, Eradication & Recovery; Post-Incident Activity). Replaced by Rev 3 which aligns with CSF 2.0."
        },
        "summary": "Establishes baseline incident handling guidelines, incident response team structures, coordination mechanisms, and the traditional 4-phase incident response lifecycle."
    },
    {
        "filename": "NIST_SP_800-61r3_ipd_Incident_Response_Recommendations.pdf",
        "title": "Incident Response Recommendations and Considerations for Cybersecurity Risk Management (Revision 3 Initial Public Draft)",
        "organization": "National Institute of Standards and Technology (NIST)",
        "document_identifier": "NIST SP 800-61r3.ipd",
        "publication_date": "2024-04-10",
        "effective_date": "2024-04-10",
        "version": "Revision 3 (Draft)",
        "topic": "Incident Response",
        "category": "cybersecurity",
        "source_url": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r3.ipd.pdf",
        "authority": "Initial Public Draft / Latest Guidance",
        "relationship": {
            "status": "CURRENT_DRAFT",
            "revises": "NIST SP 800-61r2",
            "notes": "Updates incident response posture to align with NIST CSF 2.0, emphasizing continuous governance, cloud architectures, and supply-chain incident coordination."
        },
        "summary": "Modernizes incident response practices, framing incident response within enterprise cybersecurity risk management and the CSF 2.0 Respond function."
    },
    {
        "filename": "NIST_CSF_1.1_Framework_Critical_Infrastructure.pdf",
        "title": "Framework for Improving Critical Infrastructure Cybersecurity (Version 1.1)",
        "organization": "National Institute of Standards and Technology (NIST)",
        "document_identifier": "NIST CSWP 04162018",
        "publication_date": "2018-04-16",
        "effective_date": "2018-04-16",
        "version": "1.1",
        "topic": "Cybersecurity Framework",
        "category": "cybersecurity",
        "source_url": "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.04162018.pdf",
        "authority": "Official Standard (Superseded by CSF 2.0)",
        "relationship": {
            "status": "SUPERSEDED",
            "superseded_by": "NIST CSF 2.0",
            "notes": "Structured around 5 core functions: Identify (ID), Protect (PR), Detect (DE), Respond (RS), Recover (RC). Does not include the GOVERN function."
        },
        "summary": "Framework providing common taxonomy and risk management mechanisms for critical infrastructure across five core functions."
    },
    {
        "filename": "NIST_CSF_2.0_Cybersecurity_Framework.pdf",
        "title": "The NIST Cybersecurity Framework (CSF) 2.0",
        "organization": "National Institute of Standards and Technology (NIST)",
        "document_identifier": "NIST CSWP 29",
        "publication_date": "2024-02-26",
        "effective_date": "2024-02-26",
        "version": "2.0",
        "topic": "Cybersecurity Framework",
        "category": "cybersecurity",
        "source_url": "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf",
        "authority": "Official Standard (Current)",
        "relationship": {
            "status": "CURRENT",
            "revises": "NIST CSF 1.1",
            "notes": "Expanded scope beyond critical infrastructure to all organizations. Added the new 'Govern' (GV) function to the original five functions."
        },
        "summary": "Flagship cybersecurity framework establishing 6 core functions: Govern (GV), Identify (ID), Protect (PR), Detect (DE), Respond (RS), and Recover (RC)."
    },
    {
        "filename": "NIST_AI_100-1_AI_RMF_1.0.pdf",
        "title": "Artificial Intelligence Risk Management Framework (AI RMF 1.0)",
        "organization": "National Institute of Standards and Technology (NIST)",
        "document_identifier": "NIST AI 100-1",
        "publication_date": "2023-01-26",
        "effective_date": "2023-01-26",
        "version": "1.0",
        "topic": "Artificial Intelligence Risk Management",
        "category": "artificial_intelligence",
        "source_url": "https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf",
        "authority": "Official Framework (Current)",
        "relationship": {
            "status": "CURRENT_FOUNDATIONAL",
            "extended_by": "NIST AI 600-1",
            "notes": "Defines foundational AI risk governance across four core functions: GOVERN, MAP, MEASURE, and MANAGE."
        },
        "summary": "Voluntary guidance to improve trustworthiness of AI systems and manage risks across design, development, and deployment."
    },
    {
        "filename": "NIST_AI_600-1_Generative_AI_Profile.pdf",
        "title": "Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile",
        "organization": "National Institute of Standards and Technology (NIST)",
        "document_identifier": "NIST AI 600-1",
        "publication_date": "2024-07-26",
        "effective_date": "2024-07-26",
        "version": "Final",
        "topic": "Generative AI Risk Management",
        "category": "artificial_intelligence",
        "source_url": "https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf",
        "authority": "Official Guidance (Current)",
        "relationship": {
            "status": "CURRENT_PROFILE",
            "extends": "NIST AI 100-1",
            "notes": "Identifies 12 unique risks specific to Generative AI (e.g., hallucinations, CBRN risks, confabulation, data privacy, copyright)."
        },
        "summary": "Companion profile to the AI RMF 1.0 specifically targeting risks, safety measures, and actions for Generative AI and Foundation Models."
    },
    {
        "filename": "NIST_SP_800-218_Secure_Software_Development_Framework.pdf",
        "title": "Secure Software Development Framework (SSDF) Version 1.1: Recommendations for Mitigating the Risk of Software Vulnerabilities",
        "organization": "National Institute of Standards and Technology (NIST)",
        "document_identifier": "NIST SP 800-218",
        "publication_date": "2022-02-03",
        "effective_date": "2022-02-03",
        "version": "1.1",
        "topic": "Software Supply Chain Security",
        "category": "software",
        "source_url": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf",
        "authority": "Official Standard (Current)",
        "relationship": {
            "status": "CURRENT",
            "notes": "Core standard for Executive Order 14028 software supply chain security; structured into Prepare Organization (PO), Protect Software (PS), Produce Well-Secured Software (PW), and Respond to Vulnerabilities (RV)."
        },
        "summary": "Defines fundamental, sound secure software development practices to reduce the number of vulnerabilities in released software and mitigate impacts."
    },
    {
        "filename": "NIST_SP_800-207_Zero_Trust_Architecture.pdf",
        "title": "Zero Trust Architecture",
        "organization": "National Institute of Standards and Technology (NIST)",
        "document_identifier": "NIST SP 800-207",
        "publication_date": "2020-08-11",
        "effective_date": "2020-08-11",
        "version": "Final",
        "topic": "Zero Trust Security Architecture",
        "category": "technology",
        "source_url": "https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf",
        "authority": "Official Standard (Current)",
        "relationship": {
            "status": "CURRENT",
            "notes": "Foundational federal definition of Zero Trust tenets, Policy Decision Points (PDP), Policy Enforcement Points (PEP), and deployment models."
        },
        "summary": "Establishes core cybersecurity guidelines and architectural tenets for implementing Zero Trust Architectures (ZTA) across enterprise systems."
    }
]


def ensure_directories():
    """Create directory structure for knowledge base."""
    categories = ["cybersecurity", "artificial_intelligence", "software", "technology"]
    for cat in categories:
        cat_dir = KB_DIR / cat
        cat_dir.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Directory structure ready at: {KB_DIR}")


def is_valid_pdf(file_path: Path) -> bool:
    """Check if file exists, is non-empty, and has PDF header."""
    if not file_path.exists() or file_path.stat().st_size < 1024:
        return False
    try:
        with open(file_path, "rb") as f:
            header = f.read(5)
            return header.startswith(b"%PDF")
    except Exception:
        return False


def download_documents(force: bool = False):
    """Download official PDFs with verification and retry logic."""
    ensure_directories()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/pdf,application/octet-stream,*/*",
        "Accept-Encoding": "gzip, deflate, br",
    }

    results = []
    print("\n" + "=" * 70)
    print("DOWNLOADING AUTHORITATIVE KNOWLEDGE BASE DOCUMENTS")
    print("=" * 70)

    for item in KNOWLEDGE_BASE_DOCUMENTS:
        cat = item["category"]
        filename = item["filename"]
        target_path = KB_DIR / cat / filename
        url = item["source_url"]

        if not force and is_valid_pdf(target_path):
            size_mb = target_path.stat().st_size / (1024 * 1024)
            print(f"[EXISTS] {filename} ({size_mb:.2f} MB) - Skipping")
            results.append({"filename": filename, "status": "already_downloaded", "path": str(target_path), "size_mb": round(size_mb, 2)})
            continue

        print(f"\n[FETCHING] {item['document_identifier']}: {item['title']}")
        print(f"  URL: {url}")
        print(f"  Target: {target_path}")

        download_success = False
        for attempt in range(1, 4):
            try:
                response = requests.get(url, headers=headers, timeout=60, stream=True)
                if response.status_code == 200:
                    with open(target_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=65536):
                            if chunk:
                                f.write(chunk)
                    
                    if is_valid_pdf(target_path):
                        size_mb = target_path.stat().st_size / (1024 * 1024)
                        print(f"  [SUCCESS] Downloaded {filename} ({size_mb:.2f} MB)")
                        results.append({"filename": filename, "status": "downloaded", "path": str(target_path), "size_mb": round(size_mb, 2)})
                        download_success = True
                        break
                    else:
                        print(f"  [WARN] Attempt {attempt}: Downloaded file failed PDF validation. Retrying...")
                else:
                    print(f"  [WARN] Attempt {attempt}: HTTP {response.status_code}. Retrying...")
            except Exception as e:
                print(f"  [ERROR] Attempt {attempt} failed: {e}")
            time.sleep(2)

        if not download_success:
            print(f"  [FAILED] Could not download {filename}")
            results.append({"filename": filename, "status": "failed", "path": str(target_path), "size_mb": 0})

    # Save metadata.json
    metadata_path = KB_DIR / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "description": "KnowledgeGuard AI Authoritative Reference Knowledge Base",
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_documents": len(KNOWLEDGE_BASE_DOCUMENTS),
                "documents": KNOWLEDGE_BASE_DOCUMENTS
            },
            f,
            indent=2
        )
    print(f"\n[OK] Metadata file written to: {metadata_path}")
    return results


def ingest_into_knowledgeguard():
    """Ingest downloaded documents through the official DocumentService pipeline."""
    from backend.database.db import SessionLocal
    from backend.services.document_service import document_service
    from backend.database.crud import get_documents

    print("\n" + "=" * 70)
    print("INGESTING DOCUMENTS INTO KNOWLEDGEGUARD AI (ChromaDB + SQLite)")
    print("=" * 70)

    db = SessionLocal()
    existing_docs = get_documents(db)
    existing_filenames = {d.filename for d in existing_docs}

    ingested_count = 0
    skipped_count = 0

    try:
        for item in KNOWLEDGE_BASE_DOCUMENTS:
            cat = item["category"]
            filename = item["filename"]
            file_path = KB_DIR / cat / filename

            if not file_path.exists() or not is_valid_pdf(file_path):
                print(f"[SKIP] File not found or invalid: {file_path}")
                continue

            if filename in existing_filenames:
                print(f"[SKIP] Already indexed in database: {filename}")
                skipped_count += 1
                continue

            print(f"\n[INGESTING] {item['document_identifier']}: {item['title']}")
            print(f"  Category: {cat} | Version: {item['version']} | Date: {item['publication_date']}")
            
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            start_t = time.perf_counter()
            doc_record = document_service.process_and_save_upload(
                file_bytes=file_bytes,
                filename=filename,
                source=f"{item['organization']} - {item['document_identifier']}",
                version=item["version"],
                topic=item["topic"],
                document_date=item["publication_date"],
                db=db
            )
            elapsed = time.perf_counter() - start_t
            chunk_cnt = len(doc_record.chunks) if hasattr(doc_record, "chunks") and doc_record.chunks else "indexed"
            print(f"  [DONE] Doc ID: {doc_record.id} | Status: {doc_record.status} | Chunks: {chunk_cnt} | Time: {elapsed:.2f}s")
            ingested_count += 1

        print("\n" + "-" * 70)
        print(f"Ingestion complete: {ingested_count} newly ingested, {skipped_count} already existed.")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="KnowledgeGuard AI Document Fetcher & Ingester")
    parser.add_argument("--force", action="store_true", help="Force redownload even if files exist")
    parser.add_argument("--download-only", action="store_true", help="Download documents without ingesting")
    parser.add_argument("--ingest-only", action="store_true", help="Ingest existing downloaded documents without downloading")
    args = parser.parse_args()

    if args.ingest_only:
        ingest_into_knowledgeguard()
    elif args.download_only:
        download_documents(force=args.force)
    else:
        download_documents(force=args.force)
        ingest_into_knowledgeguard()
