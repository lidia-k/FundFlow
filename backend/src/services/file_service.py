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

            # Generate storage path
            secure_path = self._generate_storage_path(year, quarter, original_filename)

            # Copy file to secure storage
            secure_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, secure_path)

            # Create SourceFile record
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



    def get_file_metadata(self, source_file_id: str) -> Optional[Dict]:
        """
        Get file metadata by source file ID.

        Args:
            source_file_id: UUID of the source file

        Returns:
            Dictionary with file metadata or None
        """
        try:
            source_file = self.db.get(SourceFile, source_file_id)

            if source_file:
                return {
                    "id": str(source_file.id),
                    "filename": source_file.filename,
                    "filepath": source_file.filepath,
                    "fileSize": source_file.file_size,
                    "contentType": source_file.content_type,
                    "uploadTimestamp": source_file.upload_timestamp.isoformat() + "Z",
                    "uploadedBy": source_file.uploaded_by
                }

            return None

        except Exception as e:
            logger.error(f"Error getting file metadata: {str(e)}")
            return None

    def delete_file(self, source_file_id: str) -> bool:
        """
        Delete file and its metadata.

        Args:
            source_file_id: UUID of the source file

        Returns:
            True if deletion successful, False otherwise
        """
        try:
            source_file = self.db.get(SourceFile, source_file_id)

            if source_file:
                # Delete physical file
                file_path = Path(source_file.filepath)
                if file_path.exists():
                    file_path.unlink()

                # Delete database record
                self.db.delete(source_file)
                self.db.commit()

                logger.info(f"File deleted successfully: {source_file.filename}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False



    def _generate_storage_path(
        self, year: int, quarter: str, original_filename: str
    ) -> Path:
        """Generate storage path for uploaded file."""
        # Create path: storage_root/year/quarter/filename
        return (
            self.storage_root
            / str(year)
            / quarter.value.lower()
            / original_filename
        )

    def validate_file_format(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate file format by reading file headers.

        Args:
            file_path: Path to file to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file extension
            if file_path.suffix.lower() not in ['.xlsx', '.xlsm']:
                return False, f"Invalid file extension: {file_path.suffix}"

            # Try to read file headers to verify it's actually an Excel file
            with open(file_path, 'rb') as f:
                header = f.read(4)
                # Excel files start with PK (ZIP format)
                if not header.startswith(b'PK'):
                    return False, "File is not a valid Excel workbook"

            return True, None

        except Exception as e:
            return False, f"Error validating file format: {str(e)}"

    def get_storage_stats(self) -> Dict:
        """Get storage statistics."""
        try:
            total_files = self.db.query(SourceFile).count()
            total_size = sum(
                sf.file_size for sf in self.db.query(SourceFile.file_size).all()
            ) or 0

            return {
                "totalFiles": total_files,
                "totalSizeBytes": total_size,
                "totalSizeMB": round(total_size / (1024 * 1024), 2),
                "storageRoot": str(self.storage_root)
            }

        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return {
                "totalFiles": 0,
                "totalSizeBytes": 0,
                "totalSizeMB": 0.0,
                "storageRoot": str(self.storage_root)
            }