"""File validation service for upload processing."""

from typing import List

from fastapi import UploadFile

from ...exceptions.upload_exceptions import FileValidationException


class FileValidator:
    """Service for validating uploaded files."""

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {".xlsx", ".xls"}

    def validate_upload_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file for type and size constraints.

        Args:
            file: The uploaded file to validate

        Raises:
            FileValidationException: If validation fails
        """
        errors = []

        # Validate file type
        if not self._is_valid_file_type(file):
            errors.append(
                "Unsupported file type. Only .xlsx and .xls files are allowed."
            )

        # Validate file size
        if not self._is_valid_file_size(file):
            errors.append(
                f"File too large. Maximum size is {self.MAX_FILE_SIZE // (1024 * 1024)}MB."
            )

        if errors:
            raise FileValidationException(
                "File validation failed", errors=errors
            )

    def _is_valid_file_type(self, file: UploadFile) -> bool:
        """Check if file has valid Excel extension."""
        if not file.filename:
            return False

        filename_lower = file.filename.lower()
        return any(filename_lower.endswith(ext) for ext in self.ALLOWED_EXTENSIONS)

    def _is_valid_file_size(self, file: UploadFile) -> bool:
        """Check if file size is within limits."""
        if not file.size:
            return True  # Size unknown, allow it through

        return file.size <= self.MAX_FILE_SIZE