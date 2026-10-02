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


# Parse CORS origins from settings (supports CORS_ORIGINS and FRONTEND_URL)
origins_set = set()

# Process CORS_ORIGINS (comma-separated string)
if settings.CORS_ORIGINS:
    for item in settings.CORS_ORIGINS.split(","):
        cleaned = item.strip().rstrip("/")
        if cleaned:
            origins_set.add(cleaned)

# Process FRONTEND_URL (supports single or comma-separated URLs)
if settings.FRONTEND_URL:
    for item in settings.FRONTEND_URL.split(","):
        cleaned = item.strip().rstrip("/")
        if cleaned:
            origins_set.add(cleaned)

# Always guarantee production and local development origins
default_production_origins = [
    "https://knowledgeguardai-1.onrender.com",
    "https://knowledgeguardai.onrender.com",
    "https://knowledgeguard-frontend.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
for default_origin in default_production_origins:
    origins_set.add(default_origin.rstrip("/"))

origins = list(origins_set)

# Enable CORS for frontend integration
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
app.include_router(api_router, prefix="/api")  # supports both direct and /api prefixed routes


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    """Simple, lightweight health check endpoint for Render service liveness verification."""
    return {
        "status": "healthy",
        "service": "KnowledgeGuard AI backend"
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

