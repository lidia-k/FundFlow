"""Validation error collection service."""

from typing import List
from sqlalchemy.orm import Session
from ..models.validation_error import ValidationError, ErrorSeverity
from ..services.excel_service import ExcelValidationError


class ValidationService:
    """Service for collecting and managing validation errors."""

    def __init__(self, db: Session):
        self.db = db

    def save_validation_errors(
        self,
        session_id: str,
        excel_errors: List[ExcelValidationError]
    ) -> List[ValidationError]:
        """Save Excel validation errors to database."""
        db_errors = []

        for excel_error in excel_errors:
            db_error = ValidationError(
                session_id=session_id,
                row_number=excel_error.row_number,
                column_name=excel_error.column_name,
                error_code=excel_error.error_code,
                error_message=excel_error.error_message,
                severity=excel_error.severity,
                field_value=excel_error.field_value
            )
            self.db.add(db_error)
            db_errors.append(db_error)

        return db_errors

    def get_errors_by_session(self, session_id: str) -> List[ValidationError]:
        """Get all validation errors for a session."""
        return self.db.query(ValidationError).filter(
            ValidationError.session_id == session_id
        ).order_by(ValidationError.row_number, ValidationError.column_name).all()

    def get_errors_by_severity(
        self,
        session_id: str,
        severity: ErrorSeverity
    ) -> List[ValidationError]:
        """Get validation errors filtered by severity."""
        return self.db.query(ValidationError).filter(
            ValidationError.session_id == session_id,
            ValidationError.severity == severity
        ).order_by(ValidationError.row_number).all()

    def has_blocking_errors(self, session_id: str) -> bool:
        """Check if session has any ERROR-level validation errors."""
        error_count = self.db.query(ValidationError).filter(
            ValidationError.session_id == session_id,
            ValidationError.severity == ErrorSeverity.ERROR
        ).count()

        return error_count > 0

    def get_error_summary(self, session_id: str) -> dict:
        """Get summary of errors by severity and code."""
        errors = self.get_errors_by_session(session_id)

        summary = {
            "total_errors": len(errors),
            "by_severity": {
                "ERROR": 0,
                "WARNING": 0
            },
            "by_code": {},
            "affected_rows": set()
        }

        for error in errors:
            # Count by severity
            summary["by_severity"][error.severity.value] += 1

            # Count by error code
            if error.error_code not in summary["by_code"]:
                summary["by_code"][error.error_code] = 0
            summary["by_code"][error.error_code] += 1

            # Track affected rows
            if error.row_number > 0:
                summary["affected_rows"].add(error.row_number)

        summary["affected_rows"] = len(summary["affected_rows"])
        return summary

    def export_errors_to_csv_data(self, session_id: str) -> List[dict]:
        """Export validation errors as CSV-ready data."""
        errors = self.get_errors_by_session(session_id)

        csv_data = []
        for error in errors:
            csv_data.append({
                "Row": error.row_number,
                "Column": error.column_name,
                "Error Code": error.error_code,
                "Message": error.error_message,
                "Severity": error.severity.value,
                "Field Value": error.field_value or "",
                "Timestamp": error.created_at.isoformat()
            })

        return csv_data