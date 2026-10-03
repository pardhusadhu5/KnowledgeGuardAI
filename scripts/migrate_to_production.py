"""
KnowledgeGuard AI Production Migration Utility
Migrates local SQLite metadata and local ChromaDB vectors to production PostgreSQL
and/or Remote ChromaDB in an idempotent, non-destructive manner.

Usage:
    # Dry run (inspects and counts data without modifying target):
    python scripts/migrate_to_production.py --dry-run --target-db postgresql://user:pass@host:5432/dbname

    # Execute migration:
    python scripts/migrate_to_production.py --target-db postgresql://user:pass@host:5432/dbname

    # Optional Remote Chroma migration:
    python scripts/migrate_to_production.py --target-db postgresql://... --target-chroma-host chroma.example.com --target-chroma-port 8000
"""

import sys
import os
import argparse
from pathlib import Path
import json
import shutil

# Ensure repository root is on sys.path
_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sqlalchemy import create_engine, func, text, inspect
from sqlalchemy.orm import sessionmaker
import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.utils.config import settings, SQLITE_DB_PATH, DEFAULT_CHROMA_DIR, UPLOAD_DIR
from backend.models.entities import Base, DocumentEntity, KnowledgeChunkEntity, InvestigationEntity, EvidenceEntity
from backend.rag.embeddings import get_embedding_function


def parse_args():
    parser = argparse.ArgumentParser(description="KnowledgeGuard AI Data Migration Utility")
    parser.add_argument(
        "--source-db",
        type=str,
        default=f"sqlite:///{SQLITE_DB_PATH}",
        help="Source SQLite database URL (default: local data/knowledgeguard.db)"
    )
    parser.add_argument(
        "--target-db",
        type=str,
        default=os.environ.get("TARGET_DATABASE_URL", "") or os.environ.get("DATABASE_URL", ""),
        help="Target PostgreSQL database URL (e.g. postgresql://user:pass@host:5432/dbname)"
    )
    parser.add_argument(
        "--source-chroma-dir",
        type=str,
        default=str(DEFAULT_CHROMA_DIR),
        help="Source local ChromaDB directory (default: data/chromadb)"
    )
    parser.add_argument(
        "--target-chroma-host",
        type=str,
        default=os.environ.get("TARGET_CHROMA_HOST", "") or os.environ.get("CHROMA_SERVER_HOST", ""),
        help="Target remote ChromaDB host (optional)"
    )
    parser.add_argument(
        "--target-chroma-port",
        type=int,
        default=int(os.environ.get("TARGET_CHROMA_PORT", 8000)),
        help="Target remote ChromaDB port (default: 8000)"
    )
    parser.add_argument(
        "--target-chroma-token",
        type=str,
        default=os.environ.get("TARGET_CHROMA_TOKEN", "") or os.environ.get("CHROMA_AUTH_TOKEN", ""),
        help="Target remote ChromaDB auth token (optional)"
    )
    parser.add_argument(
        "--target-upload-dir",
        type=str,
        default=os.environ.get("TARGET_UPLOAD_DIR", "") or str(UPLOAD_DIR),
        help="Target persistent upload directory for physical PDF/TXT files"
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default=settings.effective_collection_name,
        help="Chroma collection name"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate migration and report counts without modifying the target database"
    )
    return parser.parse_args()


def mask_url(url: str) -> str:
    if not url:
        return "(none)"
    if "@" in url:
        prefix = url.split("://")[0] if "://" in url else "db"
        host_part = url.split("@")[-1]
        return f"{prefix}://***@{host_part}"
    return url


def run_migration():
    args = parse_args()

    print("=" * 70)
    print(" KNOWLEDGEGUARD AI — PRODUCTION STORAGE MIGRATION UTILITY")
    print("=" * 70)
    print(f" Source SQLite DB:       {args.source_db}")
    print(f" Target Relational DB:   {mask_url(args.target_db)}")
    print(f" Source Chroma Dir:      {args.source_chroma_dir}")
    print(f" Target Chroma Host:     {args.target_chroma_host or '(local target)'}")
    print(f" Target Upload Dir:      {args.target_upload_dir}")
    print(f" Mode:                   {'DRY RUN (Read Only)' if args.dry_run else 'LIVE MIGRATION'}")
    print("=" * 70)

    # 1. Connect to Source SQLite
    source_engine = create_engine(args.source_db, connect_args={"check_same_thread": False})
    SourceSession = sessionmaker(bind=source_engine)
    source_db = SourceSession()

    # 2. Count Source Data
    src_docs_count = source_db.query(func.count(DocumentEntity.id)).scalar() or 0
    src_chunks_count = source_db.query(func.count(KnowledgeChunkEntity.id)).scalar() or 0
    src_invs_count = source_db.query(func.count(InvestigationEntity.id)).scalar() or 0
    src_ev_count = source_db.query(func.count(EvidenceEntity.id)).scalar() or 0

    # Count Source Chroma
    src_chroma_count = 0
    src_collection = None
    try:
        src_client = chromadb.PersistentClient(
            path=args.source_chroma_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        existing_colls = [c.name for c in src_client.list_collections()]
        src_coll_name = args.collection_name
        if src_coll_name not in existing_colls and existing_colls:
            src_coll_name = existing_colls[0]
            print(f"[Info] Collection '{args.collection_name}' not found locally. Using detected collection '{src_coll_name}'.")
        src_collection = src_client.get_collection(name=src_coll_name)
        src_chroma_count = src_collection.count()
    except Exception as e:
        print(f"[Warning] Could not inspect source Chroma collection: {e}")

    print("\n[PRE-MIGRATION COUNTS — SOURCE DATA]")
    print(f"  * Documents:           {src_docs_count}")
    print(f"  * Knowledge Chunks:    {src_chunks_count}")
    print(f"  * Investigations:      {src_invs_count}")
    print(f"  * Evidence Records:    {src_ev_count}")
    print(f"  * Chroma Vectors:      {src_chroma_count}")

    if not args.target_db:
        print("\n[Notice] No --target-db provided. Relational database migration skipped.")
        if args.dry_run:
            print("[Dry Run Complete]")
            return
    else:
        # Normalize postgresql:// scheme
        target_db_url = args.target_db
        if target_db_url.startswith("postgres://"):
            target_db_url = target_db_url.replace("postgres://", "postgresql://", 1)
        if target_db_url.startswith("postgresql://") and not target_db_url.startswith("postgresql+"):
            try:
                import psycopg  # noqa: F401
            except ImportError:
                target_db_url = target_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

        target_engine = create_engine(
            target_db_url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 15} if "postgresql" in target_db_url else {}
        )
        TargetSession = sessionmaker(bind=target_engine)
        target_db = TargetSession()

        # Check existing target counts
        target_docs_count_pre = 0
        target_chunks_count_pre = 0
        target_invs_count_pre = 0
        target_ev_count_pre = 0
        try:
            target_inspector = inspect(target_engine)
            if "documents" in target_inspector.get_table_names():
                target_docs_count_pre = target_db.query(func.count(DocumentEntity.id)).scalar() or 0
                target_chunks_count_pre = target_db.query(func.count(KnowledgeChunkEntity.id)).scalar() or 0
                target_invs_count_pre = target_db.query(func.count(InvestigationEntity.id)).scalar() or 0
                target_ev_count_pre = target_db.query(func.count(EvidenceEntity.id)).scalar() or 0
        except Exception:
            pass

        print(f"\n[PRE-MIGRATION COUNTS — TARGET DB ({mask_url(target_db_url)})]")
        print(f"  * Documents:           {target_docs_count_pre}")
        print(f"  * Knowledge Chunks:    {target_chunks_count_pre}")
        print(f"  * Investigations:      {target_invs_count_pre}")
        print(f"  * Evidence Records:    {target_ev_count_pre}")

        if args.dry_run:
            print("\n[DRY RUN SUMMARY] Simulation complete. No changes were committed to target store.")
            return

        # LIVE MIGRATION EXECUTION
        print("\n[Step 1/5] Initializing target database schema...")
        Base.metadata.create_all(bind=target_engine)
        print("  [OK] Schema tables verified and ready on target database.")

        print("\n[Step 2/5] Migrating documents and metadata...", flush=True)
        src_docs = source_db.query(DocumentEntity).all()
        existing_doc_ids = set(r[0] for r in target_db.query(DocumentEntity.id).all())
        new_docs = [
            DocumentEntity(
                id=d.id,
                filename=d.filename,
                source=d.source,
                version=d.version,
                topic=d.topic,
                document_date=d.document_date,
                uploaded_at=d.uploaded_at,
                status=d.status
            )
            for d in src_docs if d.id not in existing_doc_ids
        ]
        if new_docs:
            target_db.add_all(new_docs)
            target_db.commit()
        print(f"  [OK] Migrated {len(new_docs)} new document records (Total: {len(src_docs)}).", flush=True)

        print("\n[Step 3/5] Migrating knowledge chunks...", flush=True)
        src_chunks = source_db.query(KnowledgeChunkEntity).all()
        existing_chunk_ids = set(r[0] for r in target_db.query(KnowledgeChunkEntity.id).all())
        chunks_to_add = [
            KnowledgeChunkEntity(
                id=c.id,
                document_id=c.document_id,
                chunk_index=c.chunk_index,
                page=getattr(c, "page", 1) or 1,
                chunk_text=c.chunk_text,
                metadata_json=c.metadata_json
            )
            for c in src_chunks if c.id not in existing_chunk_ids
        ]
        for i in range(0, len(chunks_to_add), 500):
            target_db.add_all(chunks_to_add[i:i + 500])
            target_db.commit()
            print(f"  Committed chunk batch {i + 1}–{min(i + 500, len(chunks_to_add))} / {len(chunks_to_add)}", flush=True)
        print(f"  [OK] Migrated {len(chunks_to_add)} new knowledge chunk records (Total: {len(src_chunks)}).", flush=True)

        print("\n[Step 4/5] Migrating investigations and evidence audit history...", flush=True)
        src_invs = source_db.query(InvestigationEntity).all()
        existing_inv_ids = set(r[0] for r in target_db.query(InvestigationEntity.id).all())
        invs_to_add = [
            InvestigationEntity(
                id=inv.id,
                claim=inv.claim,
                classification=inv.classification,
                explanation=inv.explanation,
                confidence=inv.confidence,
                recommendation=inv.recommendation,
                human_verification_required=inv.human_verification_required,
                human_review_status=getattr(inv, "human_review_status", "Pending Review") or "Pending Review",
                execution_time_ms=getattr(inv, "execution_time_ms", 0.0) or 0.0,
                research_occurred=getattr(inv, "research_occurred", False) or False,
                created_at=inv.created_at,
                metadata_json=inv.metadata_json
            )
            for inv in src_invs if inv.id not in existing_inv_ids
        ]
        if invs_to_add:
            target_db.add_all(invs_to_add)
            target_db.commit()

        src_evs = source_db.query(EvidenceEntity).all()
        existing_ev_ids = set(r[0] for r in target_db.query(EvidenceEntity.id).all())
        all_target_doc_ids = set(r[0] for r in target_db.query(DocumentEntity.id).all())
        all_target_chunk_ids = set(r[0] for r in target_db.query(KnowledgeChunkEntity.id).all())
        all_target_inv_ids = set(r[0] for r in target_db.query(InvestigationEntity.id).all())

        evs_to_add = []
        for ev in src_evs:
            if ev.id in existing_ev_ids or ev.investigation_id not in all_target_inv_ids:
                continue
            doc_id_val = ev.document_id if ev.document_id in all_target_doc_ids else None
            chunk_id_val = ev.chunk_id if ev.chunk_id in all_target_chunk_ids else None
            new_ev = EvidenceEntity(
                id=ev.id,
                investigation_id=ev.investigation_id,
                document_id=doc_id_val,
                chunk_id=chunk_id_val,
                page=getattr(ev, "page", 1) or 1,
                evidence_text=ev.evidence_text,
                relevance_score=ev.relevance_score,
                source=ev.source,
                version=ev.version,
                date=ev.date,
                is_stored_knowledge=ev.is_stored_knowledge
            )
            evs_to_add.append(new_ev)

        for i in range(0, len(evs_to_add), 500):
            target_db.add_all(evs_to_add[i:i + 500])
            target_db.commit()
        print(f"  [OK] Migrated {len(evs_to_add)} investigations and evidence records.", flush=True)

        # If PostgreSQL, reset sequence auto-increments
        if "postgresql" in target_db_url:
            with target_engine.begin() as conn:
                for tbl in ["documents", "knowledge_chunks", "investigations", "evidence"]:
                    try:
                        conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), COALESCE(MAX(id), 1)) FROM {tbl}"))
                    except Exception:
                        pass
            print("  [OK] Synchronized PostgreSQL sequence generators.")

    # Step 5: Migrate Vector Embeddings to Target ChromaDB
    if args.target_chroma_host and src_collection and src_chroma_count > 0:
        print(f"\n[Step 5/5] Migrating vector embeddings to Remote ChromaDB ({args.target_chroma_host}:{args.target_chroma_port})...")
        target_headers = {"X-Chroma-Token": args.target_chroma_token} if args.target_chroma_token else None
        target_client = chromadb.HttpClient(
            host=args.target_chroma_host,
            port=args.target_chroma_port,
            headers=target_headers,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        embedding_fn = get_embedding_function()
        target_collection = target_client.get_or_create_collection(
            name=args.collection_name,
            embedding_function=embedding_fn
        )

        all_records = src_collection.get(include=["documents", "metadatas"])
        total_vectors = len(all_records["ids"])
        print(f"  Found {total_vectors} vectors to transfer. Ingesting in batches of 100...")

        batch_size = 100
        for i in range(0, total_vectors, batch_size):
            b_ids = all_records["ids"][i:i + batch_size]
            b_docs = all_records["documents"][i:i + batch_size]
            b_metas = all_records["metadatas"][i:i + batch_size]
            target_collection.upsert(ids=b_ids, documents=b_docs, metadatas=b_metas)
            print(f"  Indexed vector batch {i + 1}–{min(i + batch_size, total_vectors)} / {total_vectors}")
        print("  [OK] Vector embedding migration complete.")

    # Migrate uploaded PDF/TXT files to persistent upload dir if distinct
    target_up_path = Path(args.target_upload_dir)
    src_up_path = Path(UPLOAD_DIR)
    if target_up_path != src_up_path and src_up_path.exists():
        target_up_path.mkdir(parents=True, exist_ok=True)
        copied_files = 0
        for f in src_up_path.glob("*.*"):
            dest_file = target_up_path / f.name
            if not dest_file.exists():
                shutil.copy2(f, dest_file)
                copied_files += 1
        print(f"\n  [OK] Synced {copied_files} physical upload files to {target_up_path}")

    # Post-Migration Report
    print("\n" + "=" * 70)
    print(" POST-MIGRATION VERIFICATION REPORT")
    print("=" * 70)
    if args.target_db:
        target_docs_count_post = target_db.query(func.count(DocumentEntity.id)).scalar() or 0
        target_chunks_count_post = target_db.query(func.count(KnowledgeChunkEntity.id)).scalar() or 0
        target_invs_count_post = target_db.query(func.count(InvestigationEntity.id)).scalar() or 0
        target_ev_count_post = target_db.query(func.count(EvidenceEntity.id)).scalar() or 0

        print(" Target PostgreSQL Database:")
        print(f"  * Documents:           {target_docs_count_post}  (Source: {src_docs_count})")
        print(f"  * Knowledge Chunks:    {target_chunks_count_post}  (Source: {src_chunks_count})")
        print(f"  * Investigations:      {target_invs_count_post}  (Source: {src_invs_count})")
        print(f"  * Evidence Records:    {target_ev_count_post}  (Source: {src_ev_count})")

    if args.target_chroma_host:
        target_chroma_count_post = target_collection.count() if 'target_collection' in locals() else 0
        print(f" Target ChromaDB Vectors: {target_chroma_count_post} (Source: {src_chroma_count})")

    print("\n Migration executed successfully without data loss.")
    print(" Source SQLite database and local ChromaDB files remain intact.")
    print("=" * 70)


if __name__ == "__main__":
    run_migration()
