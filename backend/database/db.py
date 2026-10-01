from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from backend.utils.config import settings
from backend.utils.logger import get_logger
from backend.models.entities import Base

logger = get_logger("database")

# Handle Render's postgres:// URI scheme requirement for SQLAlchemy
raw_db_url = settings.DATABASE_URL or "sqlite:///data/knowledgeguard.db"
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

is_sqlite = raw_db_url.startswith("sqlite")

engine_kwargs = {}
if is_sqlite:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL connection pooling and health checks for production
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(raw_db_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes tables and ensures incremental schema migrations across SQLite and PostgreSQL."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database schema verified on engine: {'SQLite' if is_sqlite else 'PostgreSQL'}")

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
    except Exception as e:
        logger.warning(f"Database initialization notice: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

