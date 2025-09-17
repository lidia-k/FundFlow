"""
Unit tests for file service SHA256 hashing
Task: T013 - Unit test file service SHA256 hashing
"""
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import hashlib
from src.services.file_service import FileService
from src.models.source_file import SourceFile


class TestFileServiceLogic:
    """Test file service business logic"""

    def test_file_service_initialization(self):
        """Test FileService initialization"""
        # This should fail initially as FileService doesn't exist yet
        service = FileService()
        assert service is not None

    def test_calculate_sha256_hash_from_file(self):
        """Test SHA256 hash calculation from file"""
        service = FileService()

        # Mock file content
        file_content = b"Test file content for SHA256 hashing"
        expected_hash = hashlib.sha256(file_content).hexdigest()

        # Mock file reading
        with patch("builtins.open", mock_open(read_data=file_content)):
            calculated_hash = service.calculate_sha256_hash("/fake/path/file.xlsx")

        assert calculated_hash == expected_hash
        assert len(calculated_hash) == 64  # SHA256 is 64 hex characters
        assert all(c in "0123456789abcdef" for c in calculated_hash)

    def test_calculate_sha256_hash_from_bytes(self):
        """Test SHA256 hash calculation from bytes"""
        service = FileService()

        file_content = b"Test file content for hashing"
        expected_hash = hashlib.sha256(file_content).hexdigest()

        calculated_hash = service.calculate_sha256_hash_from_bytes(file_content)

        assert calculated_hash == expected_hash
        assert len(calculated_hash) == 64

    def test_calculate_sha256_hash_empty_file(self):
        """Test SHA256 hash calculation for empty file"""
        service = FileService()

        # Empty file content
        file_content = b""
        expected_hash = hashlib.sha256(file_content).hexdigest()

        with patch("builtins.open", mock_open(read_data=file_content)):
            calculated_hash = service.calculate_sha256_hash("/fake/path/empty.xlsx")

        assert calculated_hash == expected_hash
        assert calculated_hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_calculate_sha256_hash_large_file(self):
        """Test SHA256 hash calculation for large file (chunked reading)"""
        service = FileService()

        # Simulate large file content (> 1MB)
        chunk_size = 1024 * 1024  # 1MB chunks
        file_content = b"x" * (chunk_size + 500)  # Slightly larger than 1MB
        expected_hash = hashlib.sha256(file_content).hexdigest()

        with patch("builtins.open", mock_open(read_data=file_content)):
            calculated_hash = service.calculate_sha256_hash("/fake/path/large_file.xlsx")

        assert calculated_hash == expected_hash

    def test_store_uploaded_file(self):
        """Test file storage with hash generation"""
        service = FileService()

        # Mock file upload
        mock_file_data = b"Excel file content"
        mock_filename = "EY_SALT_Rules_2025Q1.xlsx"
        mock_content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        expected_hash = hashlib.sha256(mock_file_data).hexdigest()

        with patch("pathlib.Path.mkdir"):
            with patch("builtins.open", mock_open()) as mock_file:
                with patch.object(service, 'calculate_sha256_hash_from_bytes', return_value=expected_hash):
                    result = service.store_uploaded_file(
                        file_data=mock_file_data,
                        filename=mock_filename,
                        content_type=mock_content_type,
                        year=2025,
                        quarter="Q1"
                    )

        assert result.filename == mock_filename
        assert result.content_type == mock_content_type
        assert result.sha256_hash == expected_hash
        assert result.file_size == len(mock_file_data)
        assert "2025" in result.filepath
        assert "Q1" in result.filepath

    def test_validate_file_size(self):
        """Test file size validation"""
        service = FileService()

        # Valid file size (under 20MB)
        valid_size = 10 * 1024 * 1024  # 10MB
        assert service.validate_file_size(valid_size) is True

        # Invalid file size (over 20MB)
        invalid_size = 25 * 1024 * 1024  # 25MB
        assert service.validate_file_size(invalid_size) is False

        # Edge case - exactly 20MB
        edge_size = 20 * 1024 * 1024  # 20MB
        assert service.validate_file_size(edge_size) is True

        # Zero size
        zero_size = 0
        assert service.validate_file_size(zero_size) is False

    def test_validate_content_type(self):
        """Test content type validation"""
        service = FileService()

        # Valid content types
        valid_types = [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
            "application/vnd.ms-excel.sheet.macroEnabled.12",  # .xlsm
        ]

        for content_type in valid_types:
            assert service.validate_content_type(content_type) is True

        # Invalid content types
        invalid_types = [
            "application/pdf",
            "text/csv",
            "application/vnd.ms-excel",  # Old .xls format
            "text/plain",
            "application/json"
        ]

        for content_type in invalid_types:
            assert service.validate_content_type(content_type) is False

    def test_check_duplicate_file(self):
        """Test duplicate file detection by hash"""
        service = FileService()

        mock_hash = "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"

        # No duplicate found
        with patch.object(service, 'find_file_by_hash', return_value=None):
            is_duplicate = service.check_duplicate_file(mock_hash, 2025, "Q1")
            assert is_duplicate is False

        # Duplicate found
        mock_existing_file = Mock(spec=SourceFile)
        mock_existing_file.sha256_hash = mock_hash
        mock_existing_file.filename = "existing_file.xlsx"

        with patch.object(service, 'find_file_by_hash', return_value=mock_existing_file):
            is_duplicate = service.check_duplicate_file(mock_hash, 2025, "Q1")
            assert is_duplicate is True

    def test_generate_secure_filepath(self):
        """Test secure file path generation"""
        service = FileService()

        filepath = service.generate_secure_filepath(
            filename="EY_SALT_Rules_2025Q1.xlsx",
            year=2025,
            quarter="Q1"
        )

        assert "2025" in filepath
        assert "Q1" in filepath
        assert filepath.endswith(".xlsx")
        assert "/" in filepath or "\\" in filepath  # Path separators
        # Should contain some randomization for security
        assert len(Path(filepath).stem) > len("EY_SALT_Rules_2025Q1")

    def test_cleanup_old_files(self):
        """Test cleanup of old uploaded files"""
        service = FileService()

        # Mock old files
        mock_old_files = [
            Mock(filepath="/uploads/2024/Q1/old_file1.xlsx"),
            Mock(filepath="/uploads/2024/Q2/old_file2.xlsx"),
        ]

        with patch.object(service, 'get_files_older_than', return_value=mock_old_files):
            with patch("pathlib.Path.unlink") as mock_unlink:
                with patch("pathlib.Path.exists", return_value=True):
                    cleaned_count = service.cleanup_old_files(days=90)

        assert cleaned_count == 2
        assert mock_unlink.call_count == 2

    def test_get_file_info(self):
        """Test getting file information"""
        service = FileService()

        mock_filepath = "/uploads/2025/Q1/file.xlsx"
        mock_file_size = 1048576  # 1MB

        with patch("pathlib.Path.stat") as mock_stat:
            mock_stat.return_value.st_size = mock_file_size
            with patch("pathlib.Path.exists", return_value=True):
                file_info = service.get_file_info(mock_filepath)

        assert file_info.file_size == mock_file_size
        assert file_info.exists is True
        assert file_info.filepath == mock_filepath

    def test_verify_file_integrity(self):
        """Test file integrity verification using stored hash"""
        service = FileService()

        mock_filepath = "/uploads/2025/Q1/file.xlsx"
        mock_stored_hash = "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"

        # File integrity verified
        with patch.object(service, 'calculate_sha256_hash', return_value=mock_stored_hash):
            is_valid = service.verify_file_integrity(mock_filepath, mock_stored_hash)
            assert is_valid is True

        # File integrity failed
        wrong_hash = "different_hash_value"
        with patch.object(service, 'calculate_sha256_hash', return_value=wrong_hash):
            is_valid = service.verify_file_integrity(mock_filepath, mock_stored_hash)
            assert is_valid is False

    def test_file_service_error_handling(self):
        """Test file service error handling"""
        service = FileService()

        # File not found error
        with patch("builtins.open", side_effect=FileNotFoundError):
            with pytest.raises(FileNotFoundError):
                service.calculate_sha256_hash("/nonexistent/file.xlsx")

        # Permission error
        with patch("builtins.open", side_effect=PermissionError):
            with pytest.raises(PermissionError):
                service.calculate_sha256_hash("/protected/file.xlsx")

        # IO error
        with patch("builtins.open", side_effect=IOError):
            with pytest.raises(IOError):
                service.calculate_sha256_hash("/corrupted/file.xlsx")