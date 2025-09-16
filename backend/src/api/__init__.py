"""API router configuration."""

from fastapi import APIRouter
from .upload import router as upload_router
from .download import router as download_router
from .health import router as health_router
from .results import router as results_router
from .template import router as template_router

# Create main API router
router = APIRouter()

# Include all endpoint routers
router.include_router(upload_router)
router.include_router(download_router)
router.include_router(health_router)
router.include_router(results_router)
router.include_router(template_router)