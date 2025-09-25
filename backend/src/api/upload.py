"""Upload API endpoint for file processing."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..exceptions.upload_exceptions import FileValidationException, UploadException
from ..services.file_upload_orchestrator import FileUploadOrchestrator
from ..services.upload_dependencies import get_upload_services
from ..services.upload_service_factory import UploadServiceDependencies

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    services: UploadServiceDependencies = Depends(get_upload_services)
) -> dict[str, Any]:
    """
    Upload and process Excel file (v1.3 format).

    Returns session information and processing status.
    """
    try:
        # Create orchestrator with injected services
        orchestrator = FileUploadOrchestrator(services, db)

        # Process upload through orchestrator
        result = await orchestrator.process_upload(file)

        return result.to_api_response()

    except FileValidationException as e:
        # File validation errors - return structured response
        return e.to_error_response()

    except UploadException as e:
        # Other upload-related errors
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Unexpected errors
        logger.exception("Upload processing failed with unexpected error")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
