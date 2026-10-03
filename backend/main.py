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
from backend.database.db import init_db, engine, is_sqlite, get_db, check_db_health
from backend.models.entities import DocumentEntity
from backend.rag.vector_store import vector_store, check_vector_store_health
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
    storage_summary = settings.get_safe_storage_summary()
    logger.info("=" * 60)
    logger.info("KnowledgeGuard AI Storage Configuration:")
    logger.info(f"  Database:       {storage_summary['database_description']}")
    logger.info(f"  Vector Store:   {storage_summary['vector_store_description']}")
    logger.info(f"  Upload Storage: {storage_summary['upload_storage']}")
    logger.info(f"  Collection:     {storage_summary['collection_name']}")
    logger.info("=" * 60)
    init_db()
    logger.info(f"KnowledgeGuard AI backend initialized successfully. Environment: {settings.ENV}")


# Mount API routers
app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """System health check endpoint verifying core service, database, and vector store availability."""
    db_ok = check_db_health(db)
    vec_ok = check_vector_store_health()
    is_healthy = db_ok and vec_ok

    payload = {
        "status": "healthy" if is_healthy else "degraded",
        "service": "KnowledgeGuard AI backend",
        "database": settings.database_type,
        "database_healthy": db_ok,
        "vector_store": settings.vector_store_type,
        "vector_store_healthy": vec_ok
    }
    status_code = 200 if is_healthy else 503
    return JSONResponse(status_code=status_code, content=payload)


@app.get("/diagnostic", tags=["Health"])
def diagnostic_check(db: Session = Depends(get_db)):
    """System diagnostic endpoint reporting database and vector store persistence status."""
    storage_summary = settings.get_safe_storage_summary()
    doc_count = 0
    try:
        doc_count = db.query(DocumentEntity).count()
    except Exception as e:
        logger.warning(f"Diagnostic DB count notice: {e}")

    db_exists = check_db_health(db)
    chroma_exists = check_vector_store_health()
    chroma_vector_count = 0
    try:
        chroma_vector_count = vector_store.count()
    except Exception as e:
        logger.warning(f"Diagnostic Chroma count notice: {e}")

    return {
        "database_type": settings.database_type,
        "database_path": storage_summary["database_description"],
        "database_exists": db_exists,
        "document_count_sqlite": doc_count,
        "chroma_path": storage_summary["vector_store_description"],
        "chroma_exists": chroma_exists,
        "chroma_collection": settings.effective_collection_name,
        "chroma_vector_count": chroma_vector_count,
        "upload_storage": storage_summary["upload_storage"]
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

