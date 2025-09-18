"""Sessions API endpoint for retrieving user upload sessions."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database.connection import get_db
from ..services.session_service import SessionService
from ..models.user_session import UploadStatus

router = APIRouter()


@router.get("/sessions")
async def get_sessions(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of sessions to return"),
    status_filter: str = Query(None, description="Filter by status (optional)"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get user's upload sessions.

    Returns a list of sessions ordered by creation date (newest first).
    For now, uses dummy user_id=1 until proper authentication is implemented.
    """
    # Initialize session service
    session_service = SessionService(db)

    # Parse status filter if provided
    status_enum = None
    if status_filter:
        try:
            status_enum = UploadStatus(status_filter.lower())
        except ValueError:
            # Invalid status, ignore filter
            pass

    # For now, use dummy user_id=1 (TODO: get from authentication)
    user_id = 1

    # Get user sessions
    sessions = session_service.get_user_sessions(
        user_id=user_id,
        limit=limit,
        status_filter=status_enum
    )

    # Format sessions for frontend consumption
    session_list = []
    for session in sessions:
        # Map backend UploadStatus to frontend CalculationStatus
        frontend_status = _map_upload_status_to_calculation_status(session.status)

        session_data = {
            "session_id": session.session_id,
            "filename": session.original_filename,
            "status": frontend_status,
            "created_at": session.created_at.isoformat(),
        }

        # Add completed_at if available
        if session.completed_at:
            session_data["completed_at"] = session.completed_at.isoformat()

        session_list.append(session_data)

    return session_list


def _map_upload_status_to_calculation_status(upload_status: UploadStatus) -> str:
    """
    Map backend UploadStatus enum to frontend CalculationStatus string.

    Frontend expects: 'pending' | 'processing' | 'completed' | 'failed'
    """
    status_mapping = {
        UploadStatus.QUEUED: "pending",
        UploadStatus.UPLOADING: "processing",
        UploadStatus.PARSING: "processing",
        UploadStatus.VALIDATING: "processing",
        UploadStatus.SAVING: "processing",
        UploadStatus.COMPLETED: "completed",
        UploadStatus.FAILED_UPLOAD: "failed",
        UploadStatus.FAILED_PARSING: "failed",
        UploadStatus.FAILED_VALIDATION: "failed",
        UploadStatus.FAILED_SAVING: "failed",
    }

    return status_mapping.get(upload_status, "failed")