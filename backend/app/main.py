from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import logging
import traceback

from app.core.config import settings, ensure_directories
from src.api import router as api_router
from src.database.connection import init_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure required directories exist
ensure_directories()

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-Powered PE Back-Office Automation Platform for SALT calculations",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting up FundFlow application...")

    # Import all models to ensure they're registered with SQLAlchemy
    from src.models import User, UserSession, Investor, Distribution, ValidationError
    from src.models import SourceFile, SaltRuleSet, WithholdingRule, CompositeRule, ValidationIssue, StateEntityTaxRuleResolved

    # Initialize database tables
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and responses for debugging"""
    try:
        logger.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(e)}"}
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with detailed logging"""
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(f"Request: {request.method} {request.url}")
    logger.error(f"Traceback: {traceback.format_exc()}")

    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "type": type(exc).__name__
        }
    )

# Include API routes
app.include_router(api_router, prefix="/api")

# Mount static files for uploads and results
if os.path.exists(settings.upload_dir):
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
if os.path.exists(settings.results_dir):
    app.mount("/results", StaticFiles(directory=settings.results_dir), name="results")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": settings.app_version,
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "service": settings.app_name
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )