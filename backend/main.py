import sys
from pathlib import Path

# Ensure repository root is on sys.path regardless of execution entrypoint
_ROOT_DIR = str(Path(__file__).resolve().parent.parent)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.utils.config import settings
from backend.utils.logger import get_logger
from backend.database.db import init_db, engine, is_sqlite
from backend.api import api_router

logger = get_logger("main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_SUBTITLE,
    version="1.0.0"
)


# Parse CORS origins from settings
cors_origins_raw = settings.CORS_ORIGINS.strip()
if cors_origins_raw == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]
if not origins:
    origins = ["*"]

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True if origins != ["*"] else False,
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
app.include_router(api_router, prefix="/api")  # supports both direct and /api prefixed routes


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    """Simple, lightweight health check endpoint for Render service liveness verification."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "env": settings.ENV,
        "database": "SQLite" if is_sqlite else "PostgreSQL",
        "vector_store": "ChromaDB"
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

