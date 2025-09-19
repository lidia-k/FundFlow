"""
Unit tests for SourceFile model validation
Task: T005 - Unit test SourceFile model validation
"""
import pytest
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import ValidationError
from src.models.source_file import SourceFile


class TestSourceFileValidation:
    """Test SourceFile model validation rules"""

    def test_valid_source_file_creation(self):
        """Test creating a valid SourceFile instance"""
        valid_data = {
            "id": uuid4(),
            "filename": "EY_SALT_Rules_2025Q1.xlsx",
            "filepath": "/secure/uploads/2025q1/abc123/file.xlsx",
            "sha256_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
            "file_size": 1048576,
            "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "upload_timestamp": datetime.now(),
            "uploaded_by": "admin@fundflow.com"
        }

        # This should fail initially as SourceFile model doesn't exist yet
        source_file = SourceFile(**valid_data)
        assert source_file.filename == "EY_SALT_Rules_2025Q1.xlsx"
        assert source_file.file_size == 1048576
        assert isinstance(source_file.id, UUID)

    def test_filename_validation(self):
        """Test filename validation rules"""
        valid_data = self._get_valid_data()

        # Test required filename
        invalid_data = valid_data.copy()
        del invalid_data["filename"]
        with pytest.raises(ValidationError):
            SourceFile(**invalid_data)

        # Test filename max length (255 chars)
        invalid_data = valid_data.copy()
        invalid_data["filename"] = "a" * 256
        with pytest.raises(ValidationError):
            SourceFile(**invalid_data)

    def test_filepath_validation(self):
        """Test filepath validation rules"""
        valid_data = self._get_valid_data()

        # Test required filepath
        invalid_data = valid_data.copy()
        del invalid_data["filepath"]
        with pytest.raises(ValidationError):
            SourceFile(**invalid_data)

    def test_sha256_hash_validation(self):
        """Test SHA256 hash validation rules"""
        valid_data = self._get_valid_data()

        # Test required hash
        invalid_data = valid_data.copy()
        del invalid_data["sha256_hash"]
        with pytest.raises(ValidationError):
            SourceFile(**invalid_data)

        # Test invalid hash length
        invalid_data = valid_data.copy()
        invalid_data["sha256_hash"] = "invalid_hash"
        with pytest.raises(ValidationError):
            SourceFile(**invalid_data)

        # Test non-hex characters
        invalid_data = valid_data.copy()
        invalid_data["sha256_hash"] = "g665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
        with pytest.raises(ValidationError):
            SourceFile(**invalid_data)

    def test_file_size_validation(self):
        """Test file size validation rules"""
        valid_data = self._get_valid_data()

        # Test required file_size
        invalid_data = valid_data.copy()
        del invalid_data["file_size"]
        with pytest.raises(ValidationError):
            SourceFile(**invalid_data)

        # Test negative file size
        invalid_data = valid_data.copy()
        invalid_data["file_size"] = -1
        with pytest.raises(ValidationError):
            SourceFile(**invalid_data)

        # Test file size exceeding 20MB limit
        invalid_data = valid_data.copy()
        invalid_data["file_size"] = 20971521  # 20MB + 1 byte
        with pytest.raises(ValidationError):
            SourceFile(**invalid_data)

    def test_content_type_validation(self):
        """Test content type validation rules"""
        valid_data = self._get_valid_data()

        # Test required content_type
        invalid_data = valid_data.copy()
        del invalid_data["content_type"]
        with pytest.raises(ValidationError):
            SourceFile(**invalid_data)

        # Test invalid content type
        invalid_data = valid_data.copy()
        invalid_data["content_type"] = "application/pdf"
        with pytest.raises(ValidationError):
            SourceFile(**invalid_data)

    def _get_valid_data(self):
        """Helper method to get valid test data"""
        return {
            "id": uuid4(),
            "filename": "EY_SALT_Rules_2025Q1.xlsx",
            "filepath": "/secure/uploads/2025q1/abc123/file.xlsx",
            "sha256_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
            "file_size": 1048576,
            "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "upload_timestamp": datetime.now(),
            "uploaded_by": "admin@fundflow.com"
        }