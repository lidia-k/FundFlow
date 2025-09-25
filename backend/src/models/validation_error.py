"""ValidationError model for capturing validation errors during file processing."""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..database.connection import Base


class ErrorSeverity(Enum):
    """Error severity enumeration."""

    ERROR = "ERROR"  # Blocks processing
    WARNING = "WARNING"  # Allows processing but flags issue


class ValidationError(Base):
    """ValidationError entity for capturing validation errors during file processing."""

    __tablename__ = "validation_errors"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        String(36), ForeignKey("user_sessions.session_id"), nullable=False
    )
    row_number = Column(Integer, nullable=False)
    column_name = Column(String(255), nullable=False)
    error_code = Column(String(50), nullable=False)
    error_message = Column(String(500), nullable=False)
    severity = Column(SQLEnum(ErrorSeverity), nullable=False)
    field_value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("UserSession", back_populates="validation_errors")

    def __repr__(self) -> str:
        return f"<ValidationError(id={self.id}, session_id='{self.session_id}', row={self.row_number}, code='{self.error_code}', severity='{self.severity.value}')>"
