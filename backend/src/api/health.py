"""Health check API endpoint."""

import os
from pathlib import Path
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database.connection import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check endpoint for monitoring application status.

    Returns system status, database connectivity, and service availability.
    """
    health_status = {
        "status": "healthy",
        "timestamp": "",
        "services": {},
        "version": "1.2.0"
    }

    from datetime import datetime
    health_status["timestamp"] = datetime.utcnow().isoformat() + "Z"

    # Check database connectivity
    try:
        # Simple database query to verify connection
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        health_status["services"]["database"] = {
            "status": "healthy",
            "type": "sqlite",
            "connection": "active"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "type": "sqlite",
            "connection": "failed"
        }

    # Check file system permissions
    try:
        # Check if we can write to uploads directory
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(exist_ok=True)

        # Try creating a test file
        test_file = uploads_dir / ".health_check"
        test_file.write_text("health_check")
        test_file.unlink()

        health_status["services"]["filesystem"] = {
            "status": "healthy",
            "uploads_dir": str(uploads_dir.absolute()),
            "writable": True
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["filesystem"] = {
            "status": "unhealthy",
            "error": str(e),
            "uploads_dir": str(uploads_dir.absolute() if 'uploads_dir' in locals() else "unknown"),
            "writable": False
        }

    # Check template availability
    try:
        template_path = Path("data/template/investor_data_template.xlsx")
        template_exists = template_path.exists()

        health_status["services"]["template"] = {
            "status": "healthy" if template_exists else "warning",
            "path": str(template_path.absolute()),
            "exists": template_exists,
            "note": "Template will be auto-generated if missing" if not template_exists else None
        }
    except Exception as e:
        health_status["services"]["template"] = {
            "status": "warning",
            "error": str(e),
            "note": "Template generation may fail"
        }

    # Check memory usage (basic)
    try:
        import psutil
        memory = psutil.virtual_memory()
        health_status["system"] = {
            "memory_usage_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "status": "healthy" if memory.percent < 90 else "warning"
        }

        if memory.percent >= 90:
            health_status["status"] = "warning"

    except ImportError:
        # psutil not available, skip system metrics
        health_status["system"] = {
            "status": "unknown",
            "note": "System monitoring not available"
        }
    except Exception as e:
        health_status["system"] = {
            "status": "error",
            "error": str(e)
        }

    # Overall health determination
    service_statuses = [
        service.get("status", "unknown")
        for service in health_status["services"].values()
    ]

    if "unhealthy" in service_statuses:
        health_status["status"] = "unhealthy"
    elif "warning" in service_statuses:
        health_status["status"] = "warning"

    return health_status


@router.get("/health/simple")
async def simple_health_check() -> Dict[str, str]:
    """
    Simple health check endpoint for load balancers.

    Returns minimal status for quick health verification.
    """
    return {
        "status": "healthy",
        "service": "fundflow-backend"
    }