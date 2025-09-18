"""Upload validation service for Excel file processing validation errors."""

from typing import List
from sqlalchemy.orm import Session

from ..models.validation_error import ValidationError, ErrorSeverity
from .excel_service import ExcelValidationError


class UploadValidationService:
    """Service for handling Excel upload validation errors."""

    def __init__(self, db: Session):
        self.db = db

    def save_validation_errors(self, session_id: str, excel_errors: List[ExcelValidationError]) -> None:
        """Save Excel validation errors to database as ValidationError entities."""
        for excel_error in excel_errors:
            validation_error = ValidationError(
                session_id=session_id,
                row_number=excel_error.row_number,
                column_name=excel_error.column_name,
                error_code=excel_error.error_code,
                error_message=excel_error.error_message,
                severity=excel_error.severity,
                field_value=excel_error.field_value
            )
            self.db.add(validation_error)

    def has_blocking_errors(self, session_id: str) -> bool:
        """Check if session has any blocking validation errors (ERROR severity)."""
        error_count = (self.db.query(ValidationError)
                      .filter(ValidationError.session_id == session_id)
                      .filter(ValidationError.severity == ErrorSeverity.ERROR)
                      .count())

        return error_count > 0