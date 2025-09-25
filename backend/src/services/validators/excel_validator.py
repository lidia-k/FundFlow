"""Excel content validation service."""

from typing import List

from ...exceptions.upload_exceptions import ExcelProcessingException
from ...services.excel_service import ExcelParsingResult


class ExcelValidator:
    """Service for validating Excel content and parsing results."""

    def validate_excel_content(self, parsing_result: ExcelParsingResult) -> None:
        """
        Validate Excel parsing results for blocking errors.

        Args:
            parsing_result: Result from Excel parsing

        Raises:
            ExcelProcessingException: If blocking validation errors found
        """
        blocking_errors = [
            error
            for error in parsing_result.errors
            if error.severity.value == "ERROR"
        ]

        if blocking_errors:
            error_details = self._format_error_details(blocking_errors)
            raise ExcelProcessingException(
                "Excel validation failed. Please fix the following errors and try again.",
                parsing_errors=blocking_errors,
            )

    def _format_error_details(self, errors: List) -> List[str]:
        """Format error details for user display."""
        error_details = []
        for error in errors:
            error_detail = f"Row {error.row_number}, {error.column_name}: {error.error_message}"
            if error.field_value:
                error_detail += f" (Value: '{error.field_value}')"
            error_details.append(error_detail)
        return error_details

    def get_validation_summary(self, parsing_result: ExcelParsingResult) -> dict:
        """Get validation summary for response."""
        blocking_errors = [
            error
            for error in parsing_result.errors
            if error.severity.value == "ERROR"
        ]

        return {
            "status": "validation_failed",
            "message": "File validation failed. Please fix the following errors and try again:",
            "errors": self._format_error_details(blocking_errors),
            "error_count": len(blocking_errors),
            "total_rows": parsing_result.total_rows,
            "fund_source_data_present": len(parsing_result.fund_source_data) > 0,
        }