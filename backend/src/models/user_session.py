"""UserSession model for tracking file upload sessions."""

import uuid
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from ..database.connection import Base


class UploadStatus(Enum):
    """Upload status enumeration."""
    QUEUED = "queued"
    UPLOADING = "uploading"
    PARSING = "parsing"
    VALIDATING = "validating"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED_UPLOAD = "failed_upload"
    FAILED_PARSING = "failed_parsing"
    FAILED_VALIDATION = "failed_validation"
    FAILED_SAVING = "failed_saving"


class UserSession(Base):
    """UserSession entity for tracking file upload and processing sessions."""

    __tablename__ = "user_sessions"

    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA256
    file_size = Column(Integer, nullable=False)
    status = Column(SQLEnum(UploadStatus), nullable=False, default=UploadStatus.QUEUED)
    progress_percentage = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    total_rows = Column(Integer, nullable=True)
    valid_rows = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="sessions")
    distributions = relationship("Distribution", back_populates="session")
    validation_errors = relationship("ValidationError", back_populates="session")

    def __repr__(self) -> str:
        return f"<UserSession(id='{self.session_id}', status='{self.status.value}', filename='{self.original_filename}')>"