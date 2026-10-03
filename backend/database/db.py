from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from backend.utils.config import settings
from backend.utils.logger import get_logger
from backend.models.entities import Base

logger = get_logger("database")

# Handle Render's postgres:// URI scheme requirement for SQLAlchemy
raw_db_url = settings.effective_database_url
is_sqlite = not settings.is_postgres

engine_kwargs = {}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL connection pooling and health checks for production
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["connect_args"] = {"connect_timeout": 10}

engine = create_engine(raw_db_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def check_db_health(db: Session = None) -> bool:
    """Verifies that the database is responsive via a lightweight query."""
    try:
        if db is not None:
            db.execute(text("SELECT 1"))
        else:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return False


def init_db():
    """Initializes tables and ensures incremental schema migrations across SQLite and PostgreSQL."""
    try:
        Base.metadata.create_all(bind=engine)
        summary = settings.get_safe_storage_summary()
        logger.info(f"Database schema verified on engine: {summary['database_description']}")

        # Universal column verification via SQLAlchemy inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if "investigations" in tables:
            existing_columns = {col["name"] for col in inspector.get_columns("investigations")}
            with engine.begin() as conn:
                if "human_review_status" not in existing_columns:
                    logger.info("Migrating schema: adding human_review_status to investigations")
                    conn.execute(text("ALTER TABLE investigations ADD COLUMN human_review_status VARCHAR(50) DEFAULT 'Pending Review'"))
                if "execution_time_ms" not in existing_columns:
                    logger.info("Migrating schema: adding execution_time_ms to investigations")
                    conn.execute(text("ALTER TABLE investigations ADD COLUMN execution_time_ms FLOAT DEFAULT 0.0"))
                if "research_occurred" not in existing_columns:
                    logger.info("Migrating schema: adding research_occurred to investigations")
                    bool_default = "0" if is_sqlite else "FALSE"
                    conn.execute(text(f"ALTER TABLE investigations ADD COLUMN research_occurred BOOLEAN DEFAULT {bool_default}"))

        if "evidence" in tables:
            existing_ev_cols = {col["name"] for col in inspector.get_columns("evidence")}
            if "page" not in existing_ev_cols:
                logger.info("Migrating schema: adding page to evidence table")
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE evidence ADD COLUMN page INTEGER DEFAULT 1"))

        if "knowledge_chunks" in tables:
            existing_kc_cols = {col["name"] for col in inspector.get_columns("knowledge_chunks")}
            if "page" not in existing_kc_cols:
                logger.info("Migrating schema: adding page to knowledge_chunks table")
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE knowledge_chunks ADD COLUMN page INTEGER DEFAULT 1"))
    except Exception as e:
        logger.warning(f"Database initialization notice: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

