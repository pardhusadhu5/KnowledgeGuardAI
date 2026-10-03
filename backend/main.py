import sys
from pathlib import Path

# Ensure repository root is on sys.path regardless of execution entrypoint
_ROOT_DIR = str(Path(__file__).resolve().parent.parent)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.utils.config import settings
from backend.utils.logger import get_logger
from backend.database.db import init_db, engine, is_sqlite, get_db
from backend.models.entities import DocumentEntity
from backend.rag.vector_store import vector_store
from backend.api import api_router

logger = get_logger("main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_SUBTITLE,
    version="1.0.0"
)


# Parse CORS origins (explicitly allows production frontend and local dev)
origins_set = {
    "https://knowledgeguardai-1.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://knowledgeguardai.onrender.com",
}

# Incorporate any custom origins defined in environment variables
if settings.CORS_ORIGINS:
    for item in settings.CORS_ORIGINS.split(","):
        cleaned = item.strip().rstrip("/")
        if cleaned and cleaned != "*":
            origins_set.add(cleaned)

if settings.FRONTEND_URL:
    for item in settings.FRONTEND_URL.split(","):
        cleaned = item.strip().rstrip("/")
        if cleaned and cleaned != "*":
            origins_set.add(cleaned)

origins = sorted(list(origins_set))
logger.info(f"Configured CORS allowed origins: {origins}")

# Attach CORSMiddleware to the main FastAPI application served by Uvicorn
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





@app.on_event("startup")
def on_startup():
    db_engine_name = "SQLite" if is_sqlite else "PostgreSQL"
    logger.info(f"Initializing {db_engine_name} relational database...")
    init_db()
    logger.info(f"KnowledgeGuard AI backend initialized successfully. Environment: {settings.ENV}")


# Mount API routers
app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health_check():
    """Simple, lightweight health check endpoint for Render service liveness verification."""
    return {
        "status": "healthy",
        "service": "KnowledgeGuard AI backend"
    }


@app.get("/diagnostic", tags=["Health"])
def diagnostic_check(db: Session = Depends(get_db)):
    """System diagnostic endpoint reporting database and vector store persistence status."""
    db_raw = str(settings.DATABASE_URL)
    db_exists = False
    doc_count_sqlite = 0
    db_display_path = db_raw
    try:
        doc_count_sqlite = db.query(DocumentEntity).count()
        if is_sqlite:
            clean_path = db_raw.replace("sqlite:///", "").replace("sqlite://", "")
            db_exists = Path(clean_path).exists()
            db_display_path = clean_path
        else:
            db_exists = True
            db_display_path = "postgresql://[credentials_hidden]@" + db_raw.split("@")[-1] if "@" in db_raw else "postgresql://[external]"
    except Exception as e:
        logger.warning(f"Diagnostic DB check notice: {e}")
        db_display_path = "unknown"

    chroma_path = str(settings.CHROMA_PERSIST_DIR)
    chroma_exists = Path(chroma_path).exists()
    chroma_collection = settings.COLLECTION_NAME
    chroma_vector_count = 0
    try:
        chroma_vector_count = vector_store.count()
    except Exception as e:
        logger.warning(f"Diagnostic Chroma count notice: {e}")

    return {
        "database_path": db_display_path,
        "database_exists": db_exists,
        "document_count_sqlite": doc_count_sqlite,
        "chroma_path": chroma_path,
        "chroma_exists": chroma_exists,
        "chroma_collection": chroma_collection,
        "chroma_vector_count": chroma_vector_count
    }



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred during processing. Please review input or consult system logs."
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

