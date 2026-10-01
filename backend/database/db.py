from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.utils.config import settings
from backend.models.entities import Base

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    # Safe schema migration for SQLite
    try:
        with engine.connect() as conn:
            cursor = conn.connection.cursor()
            cursor.execute("PRAGMA table_info(investigations)")
            cols = [col[1] for col in cursor.fetchall()]
            if "human_review_status" not in cols:
                cursor.execute("ALTER TABLE investigations ADD COLUMN human_review_status VARCHAR(50) DEFAULT 'Pending Review'")
            if "execution_time_ms" not in cols:
                cursor.execute("ALTER TABLE investigations ADD COLUMN execution_time_ms FLOAT DEFAULT 0.0")
            if "research_occurred" not in cols:
                cursor.execute("ALTER TABLE investigations ADD COLUMN research_occurred BOOLEAN DEFAULT 0")
            conn.connection.commit()
    except Exception as e:
        pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
