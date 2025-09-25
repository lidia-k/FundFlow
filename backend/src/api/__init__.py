"""API router configuration."""

from fastapi import APIRouter

from .download import router as download_router
from .health import router as health_router
from .results import router as results_router
from .salt_rules import router as salt_rules_router
from .sessions import router as sessions_router
from .template import router as template_router
from .upload import router as upload_router

# Create main API router
router = APIRouter()

# Include all endpoint routers
router.include_router(upload_router)
router.include_router(download_router)
router.include_router(health_router)
router.include_router(results_router)
router.include_router(template_router)
router.include_router(salt_rules_router)
router.include_router(sessions_router)
