from fastapi import APIRouter
from .routes_documents import router as documents_router
from .routes_investigate import router as investigate_router
from .routes_dashboard import router as dashboard_router

api_router = APIRouter()
api_router.include_router(documents_router)
api_router.include_router(investigate_router)
api_router.include_router(dashboard_router)

__all__ = ["api_router"]
