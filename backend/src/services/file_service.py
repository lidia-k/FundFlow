"""File storage service with SHA256 hashing for SALT rule workbooks."""

import hashlib
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
        is_duplicate: bool,
        existing_source_file: Optional[SourceFile] = None,
        error_message: Optional[str] = None
    ):
        self.source_file = source_file
        self.is_duplicate = is_duplicate
        self.existing_source_file = existing_source_file
        self.error_message = error_message


class FileService:
    """Service for secure file storage and SHA256-based deduplication."""

    def __init__(self, db: Session, storage_root: Path = None):
        """Initialize file service with storage configuration."""
        self.db = db
        self.storage_root = storage_root or Path("backend/data/uploads")
        self.storage_root.mkdir(parents=True, exist_ok=True)

        # File size limit: 20MB
        self.max_file_size = 20 * 1024 * 1024  # 20,971,520 bytes

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
        Store uploaded file with SHA256 hashing and duplicate detection.

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
                    is_duplicate=False,
                    error_message=f"File size {file_size} exceeds maximum allowed size {self.max_file_size}"
                )

            # Validate content type
            if content_type not in self.allowed_content_types:
                return FileStorageResult(
                    source_file=None,
                    is_duplicate=False,
                    error_message=f"Content type '{content_type}' not allowed"
                )

            # Calculate SHA256 hash
            sha256_hash = self._calculate_file_hash(file_path)

            # Check for duplicates
            existing_file = self._find_existing_file_by_hash(
                self.db, sha256_hash, year, quarter
            )

            if existing_file:
                return FileStorageResult(
                    source_file=None,
                    is_duplicate=True,
                    existing_source_file=existing_file,
                    error_message=f"Duplicate file detected for {year} {quarter}"
                )

            # Generate secure storage path
            secure_path = self._generate_secure_path(year, quarter, sha256_hash, original_filename)

            # Copy file to secure storage
            secure_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, secure_path)

            # Create SourceFile record
            source_file = SourceFile(
                id=str(uuid4()),
                filename=original_filename,
                filepath=str(secure_path),
                sha256_hash=sha256_hash,
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
                source_file=source_file,
                is_duplicate=False
            )

        except Exception as e:
            logger.error(f"Error storing file {original_filename}: {str(e)}")
            return FileStorageResult(
                source_file=None,
                is_duplicate=False,
                error_message=f"Storage error: {str(e)}"
            )

    def check_duplicate_file(self, file_path: Path, year: int, quarter: str) -> bool:
        """
        Check if file is a duplicate based on SHA256 hash.

        Args:
            file_path: Path to file to check
            year: Tax year
            quarter: Tax quarter

        Returns:
            True if duplicate exists, False otherwise
        """
        try:
            sha256_hash = self._calculate_file_hash(file_path)
            existing_file = self._find_existing_file_by_hash(self.db, sha256_hash, year, quarter)
            return existing_file is not None

        except Exception as e:
            logger.error(f"Error checking duplicate: {str(e)}")
            return False

    def find_existing_rule_set_by_hash(
        self, file_hash: str, year: int, quarter: str
    ) -> Optional[Dict]:
        """
        Find existing rule set by file hash.

        Args:
            file_hash: SHA256 hash of the file
            year: Tax year
            quarter: Tax quarter

        Returns:
            Dictionary with rule set information or None
        """
        try:
            source_file = self._find_existing_file_by_hash(self.db, file_hash, year, quarter)

            if source_file and source_file.rule_set:
                return {
                    "id": str(source_file.rule_set.id),
                    "filename": source_file.filename,
                    "uploadedAt": source_file.upload_timestamp.isoformat() + "Z"
                }

            return None

        except Exception as e:
            logger.error(f"Error finding rule set by hash: {str(e)}")
            return None

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
                    "sha256Hash": source_file.sha256_hash,
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

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    def _find_existing_file_by_hash(
        self, session: Session, file_hash: str, year: int, quarter: str
    ) -> Optional[SourceFile]:
        """Find existing file by SHA256 hash for the same year/quarter."""
        return (
            session.query(SourceFile)
            .join(SourceFile.rule_set)
            .filter(
                SourceFile.sha256_hash == file_hash,
                SourceFile.rule_set.has(year=year, quarter=quarter)
            )
            .first()
        )

    def _generate_secure_path(
        self, year: int, quarter: str, file_hash: str, original_filename: str
    ) -> Path:
        """Generate secure storage path for uploaded file."""
        # Extract file extension
        extension = Path(original_filename).suffix

        # Create path: storage_root/year/quarter/hash[:8]/hash + extension
        return (
            self.storage_root
            / str(year)
            / quarter.lower()
            / file_hash[:8]
            / f"{file_hash}{extension}"
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