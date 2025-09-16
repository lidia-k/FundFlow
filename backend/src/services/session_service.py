"""Session management service."""

import uuid
from typing import Optional
from sqlalchemy.orm import Session
from ..models.user_session import UserSession, UploadStatus
from ..models.user import User


class SessionService:
    """Service for managing user upload sessions."""

    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        user_id: int,
        upload_filename: str,
        original_filename: str,
        file_hash: str,
        file_size: int
    ) -> UserSession:
        """Create a new upload session."""
        session = UserSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            upload_filename=upload_filename,
            original_filename=original_filename,
            file_hash=file_hash,
            file_size=file_size,
            status=UploadStatus.QUEUED,
            progress_percentage=0
        )

        self.db.add(session)
        self.db.flush()  # Get the session_id without committing
        return session

    def get_session_by_id(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID."""
        return self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()

    def update_session_status(
        self,
        session_id: str,
        status: UploadStatus,
        progress_percentage: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update session status and progress."""
        session = self.get_session_by_id(session_id)
        if not session:
            return False

        session.status = status

        if progress_percentage is not None:
            session.progress_percentage = max(0, min(100, progress_percentage))

        if error_message is not None:
            session.error_message = error_message

        # Set completed_at if completed or failed
        if status in [UploadStatus.COMPLETED, UploadStatus.FAILED_UPLOAD,
                      UploadStatus.FAILED_PARSING, UploadStatus.FAILED_VALIDATION,
                      UploadStatus.FAILED_SAVING]:
            from datetime import datetime
            session.completed_at = datetime.utcnow()

        return True

    def update_session_counts(
        self,
        session_id: str,
        total_rows: int,
        valid_rows: int
    ) -> bool:
        """Update session row counts."""
        session = self.get_session_by_id(session_id)
        if not session:
            return False

        session.total_rows = total_rows
        session.valid_rows = valid_rows
        return True

    def check_file_duplicate(self, file_hash: str, user_id: int) -> Optional[UserSession]:
        """Check if file hash already exists for user (idempotency)."""
        return self.db.query(UserSession).filter(
            UserSession.file_hash == file_hash,
            UserSession.user_id == user_id
        ).first()

    def get_user_sessions(
        self,
        user_id: int,
        limit: int = 50,
        status_filter: Optional[UploadStatus] = None
    ) -> list[UserSession]:
        """Get user's upload sessions."""
        query = self.db.query(UserSession).filter(UserSession.user_id == user_id)

        if status_filter:
            query = query.filter(UserSession.status == status_filter)

        return query.order_by(UserSession.created_at.desc()).limit(limit).all()

    def get_session_summary(self, session_id: str) -> Optional[dict]:
        """Get session summary with related data counts."""
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        # Count related records
        distribution_count = len(session.distributions)
        error_count = len(session.validation_errors)

        return {
            "session_id": session.session_id,
            "status": session.status.value,
            "progress_percentage": session.progress_percentage,
            "original_filename": session.original_filename,
            "file_size": session.file_size,
            "total_rows": session.total_rows,
            "valid_rows": session.valid_rows,
            "distribution_count": distribution_count,
            "error_count": error_count,
            "created_at": session.created_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "error_message": session.error_message
        }