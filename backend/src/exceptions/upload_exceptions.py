"""Custom exceptions for upload processing."""

from typing import Any, List


class UploadException(Exception):
    """Base exception for upload-related errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class FileValidationException(UploadException):
    """Exception raised when file validation fails."""

    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(message)
        self.errors = errors or []

    def to_error_response(self) -> dict[str, Any]:
        """Convert to API error response format."""
        return {
            "status": "validation_failed",
            "message": self.message,
            "errors": self.errors,
            "error_count": len(self.errors),
        }


class ExcelProcessingException(UploadException):
    """Exception raised when Excel processing fails."""

    def __init__(self, message: str, parsing_errors: List[Any] = None):
        super().__init__(message)
        self.parsing_errors = parsing_errors or []


class TaxCalculationException(UploadException):
    """Exception raised when tax calculation fails."""

    pass


class DataProcessingException(UploadException):
    """Exception raised when data processing fails."""

    def __init__(self, message: str, failed_step: str = None):
        super().__init__(message)
        self.failed_step = failed_step


class FundSourceDataException(UploadException):
    """Exception raised when fund source data processing fails."""

    def __init__(self, message: str, validation_errors: List[str] = None):
        super().__init__(message)
        self.validation_errors = validation_errors or []


class FileStorageException(UploadException):
    """Exception raised when file storage operations fail."""

    pass