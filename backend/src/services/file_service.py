"""File storage service for SALT rule workbooks."""

import logging
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.source_file import SourceFile

logger = logging.getLogger(__name__)


class FileStorageResult:
    """Result of file storage operation."""

    def __init__(
        self,
        source_file: Optional[SourceFile],
        error_message: Optional[str] = None
    ):
        self.source_file = source_file
        self.error_message = error_message


class FileService:
    """Service for secure file storage."""

    def __init__(self, db: Session, storage_root: Path = None):
        """Initialize file service with storage configuration."""
        self.db = db
        self.storage_root = storage_root or Path("backend/data/uploads")
        self.storage_root.mkdir(parents=True, exist_ok=True)

        # File size limit: 10MB for prototype
        self.max_file_size = 10 * 1024 * 1024  # 10,485,760 bytes

        # Allowed content types
        self.allowed_content_types = {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel.sheet.macroEnabled.12"
        }

    def store_uploaded_file(
        self,
        file_path: Path,
        original_filename: str,
        content_type: str,
        uploaded_by: str,
        year: int,
        quarter: str
    ) -> FileStorageResult:
        """
        Store uploaded file, overriding any existing file.

        Args:
            file_path: Path to temporary uploaded file
            original_filename: Original filename from upload
            content_type: MIME content type
            uploaded_by: User identifier
            year: Tax year
            quarter: Tax quarter

        Returns:
            FileStorageResult with storage outcome
        """
        try:
            # Validate file size
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                return FileStorageResult(
                    source_file=None,
                    error_message=f"File size {file_size} exceeds maximum allowed size {self.max_file_size}"
                )

            # Validate content type
            if content_type not in self.allowed_content_types:
                return FileStorageResult(
                    source_file=None,
                    error_message=f"Content type '{content_type}' not allowed"
                )

            # Generate storage path and copy file
            secure_path = self._generate_storage_path(year, quarter, original_filename)
            secure_path.parent.mkdir(parents=True, exist_ok=True)

            # Check for existing SourceFile with same filepath and delete it
            existing_source_file = self.db.query(SourceFile).filter(
                SourceFile.filepath == str(secure_path)
            ).first()

            if existing_source_file:
                logger.info(f"Found existing source file with same path, deleting: {existing_source_file.filepath}")
                self.db.delete(existing_source_file)
                self.db.commit()

            shutil.copy2(file_path, secure_path)

            # Create SourceFile record (simple - any duplicates handled at rule set level)
            source_file = SourceFile(
                id=str(uuid4()),
                filename=original_filename,
                filepath=str(secure_path),
                file_size=file_size,
                content_type=content_type,
                upload_timestamp=datetime.now(),
                uploaded_by=uploaded_by
            )

            self.db.add(source_file)
            self.db.commit()
            self.db.refresh(source_file)

            logger.info(f"File stored successfully: {original_filename} -> {secure_path}")

            return FileStorageResult(
                source_file=source_file
            )

        except Exception as e:
            logger.error(f"Error storing file {original_filename}: {str(e)}")
            return FileStorageResult(
                source_file=None,
                error_message=f"Storage error: {str(e)}"
            )







    def _generate_storage_path(
        self, year: int, quarter: str, original_filename: str
    ) -> Path:
        """Generate storage path for uploaded file."""
        # Create path: storage_root/year/quarter/filename
        return (
            self.storage_root
            / str(year)
            / quarter.lower()
            / original_filename
        )

