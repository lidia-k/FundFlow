"""
Integration test for duplicate file detection
Task: T023 - Integration test duplicate file detection
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import io
import hashlib
from uuid import uuid4
from app.main import app


class TestDuplicateDetectionIntegration:
    """Test duplicate file detection functionality"""

    def setup_method(self):
        """Setup test client"""
        # This should fail initially as duplicate detection doesn't exist yet
        self.client = TestClient(app)

    def test_duplicate_detection_same_content_same_period(self):
        """Test detection of duplicate files with same content for same year/quarter"""
        # Create file with specific content
        file_content = b"Specific Excel content for duplicate testing"
        expected_hash = hashlib.sha256(file_content).hexdigest()

        excel_file = io.BytesIO(file_content)
        files = {"file": ("original.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1", "description": "Original upload"}

        # First upload should succeed
        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=expected_hash):
                with patch('src.services.file_service.FileService.check_duplicate_file', return_value=False):
                    mock_process.return_value = {
                        "withholding_rules": self._create_mock_rules(),
                        "composite_rules": self._create_mock_rules(),
                        "validation_issues": []
                    }

                    first_response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert first_response.status_code == 201
        first_result = first_response.json()
        first_rule_set_id = first_result["ruleSetId"]

        # Second upload with identical content should be detected as duplicate
        excel_file_2 = io.BytesIO(file_content)  # Same content
        files_2 = {"file": ("duplicate.xlsx", excel_file_2, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data_2 = {"year": 2025, "quarter": "Q1", "description": "Duplicate upload"}

        # Mock duplicate detection finding the existing file
        mock_existing_file = {
            "id": first_rule_set_id,
            "filename": "original.xlsx",
            "sha256Hash": expected_hash,
            "uploadedAt": "2025-01-01T10:00:00Z",
            "year": 2025,
            "quarter": "Q1"
        }

        with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=expected_hash):
            with patch('src.services.file_service.FileService.check_duplicate_file', return_value=True):
                with patch('src.services.file_service.FileService.find_existing_rule_set_by_hash', return_value=mock_existing_file):
                    second_response = self.client.post("/api/salt-rules/upload", files=files_2, data=data_2)

        assert second_response.status_code == 409  # Conflict
        conflict_result = second_response.json()

        # Validate conflict response
        assert "error" in conflict_result
        assert conflict_result["error"] == "DUPLICATE_FILE"
        assert "duplicate" in conflict_result["message"].lower()
        assert "existingRuleSetId" in conflict_result
        assert conflict_result["existingRuleSetId"] == first_rule_set_id

        # Validate duplicate detection metadata
        assert "duplicateDetection" in conflict_result
        duplicate_info = conflict_result["duplicateDetection"]
        assert duplicate_info["sha256Hash"] == expected_hash
        assert "uploadedAt" in duplicate_info

    def test_duplicate_detection_same_content_different_period(self):
        """Test that same content is allowed for different year/quarter"""
        file_content = b"Same Excel content for different periods"
        expected_hash = hashlib.sha256(file_content).hexdigest()

        # Upload for Q1 2025
        excel_file_q1 = io.BytesIO(file_content)
        files_q1 = {"file": ("q1_rules.xlsx", excel_file_q1, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data_q1 = {"year": 2025, "quarter": "Q1"}

        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=expected_hash):
                with patch('src.services.file_service.FileService.check_duplicate_file', return_value=False):
                    mock_process.return_value = {
                        "withholding_rules": self._create_mock_rules(),
                        "composite_rules": self._create_mock_rules(),
                        "validation_issues": []
                    }

                    q1_response = self.client.post("/api/salt-rules/upload", files=files_q1, data=data_q1)

        assert q1_response.status_code == 201

        # Upload same content for Q2 2025 should be allowed
        excel_file_q2 = io.BytesIO(file_content)
        files_q2 = {"file": ("q2_rules.xlsx", excel_file_q2, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data_q2 = {"year": 2025, "quarter": "Q2"}

        # Mock duplicate check returns False for different period
        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=expected_hash):
                with patch('src.services.file_service.FileService.check_duplicate_file', return_value=False):  # Different period allowed
                    mock_process.return_value = {
                        "withholding_rules": self._create_mock_rules(),
                        "composite_rules": self._create_mock_rules(),
                        "validation_issues": []
                    }

                    q2_response = self.client.post("/api/salt-rules/upload", files=files_q2, data=data_q2)

        assert q2_response.status_code == 201
        # Both uploads should succeed for different quarters

    def test_duplicate_detection_different_content_same_period(self):
        """Test that different content is allowed for same year/quarter"""
        # First file
        content_1 = b"First Excel content with different data"
        hash_1 = hashlib.sha256(content_1).hexdigest()
        excel_file_1 = io.BytesIO(content_1)
        files_1 = {"file": ("first.xlsx", excel_file_1, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data_1 = {"year": 2025, "quarter": "Q1", "description": "First upload"}

        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=hash_1):
                with patch('src.services.file_service.FileService.check_duplicate_file', return_value=False):
                    mock_process.return_value = {
                        "withholding_rules": self._create_mock_rules(),
                        "composite_rules": self._create_mock_rules(),
                        "validation_issues": []
                    }

                    first_response = self.client.post("/api/salt-rules/upload", files=files_1, data=data_1)

        assert first_response.status_code == 201

        # Second file with different content
        content_2 = b"Second Excel content with completely different data"
        hash_2 = hashlib.sha256(content_2).hexdigest()
        excel_file_2 = io.BytesIO(content_2)
        files_2 = {"file": ("second.xlsx", excel_file_2, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data_2 = {"year": 2025, "quarter": "Q1", "description": "Second upload"}

        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=hash_2):
                with patch('src.services.file_service.FileService.check_duplicate_file', return_value=False):  # Different content allowed
                    mock_process.return_value = {
                        "withholding_rules": self._create_mock_rules(),
                        "composite_rules": self._create_mock_rules(),
                        "validation_issues": []
                    }

                    second_response = self.client.post("/api/salt-rules/upload", files=files_2, data=data_2)

        assert second_response.status_code == 201
        # Both uploads should succeed as content is different

    def test_duplicate_detection_edge_cases(self):
        """Test edge cases in duplicate detection"""
        # Test file with same name but different content
        content_a = b"Content A for duplicate testing"
        content_b = b"Content B for duplicate testing - different"
        hash_a = hashlib.sha256(content_a).hexdigest()
        hash_b = hashlib.sha256(content_b).hexdigest()

        # Upload first file
        excel_file_a = io.BytesIO(content_a)
        files_a = {"file": ("same_name.xlsx", excel_file_a, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=hash_a):
                with patch('src.services.file_service.FileService.check_duplicate_file', return_value=False):
                    mock_process.return_value = {
                        "withholding_rules": self._create_mock_rules(),
                        "composite_rules": self._create_mock_rules(),
                        "validation_issues": []
                    }

                    first_response = self.client.post("/api/salt-rules/upload", files=files_a, data=data)

        assert first_response.status_code == 201

        # Upload file with same name but different content
        excel_file_b = io.BytesIO(content_b)
        files_b = {"file": ("same_name.xlsx", excel_file_b, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=hash_b):
                with patch('src.services.file_service.FileService.check_duplicate_file', return_value=False):  # Different hash
                    mock_process.return_value = {
                        "withholding_rules": self._create_mock_rules(),
                        "composite_rules": self._create_mock_rules(),
                        "validation_issues": []
                    }

                    second_response = self.client.post("/api/salt-rules/upload", files=files_b, data=data)

        assert second_response.status_code == 201
        # Should succeed because content hash is different despite same filename

    def test_duplicate_detection_with_published_rule_set(self):
        """Test duplicate detection when existing rule set is already published"""
        file_content = b"Published rule set content"
        expected_hash = hashlib.sha256(file_content).hexdigest()
        existing_rule_set_id = str(uuid4())

        excel_file = io.BytesIO(file_content)
        files = {"file": ("duplicate_published.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        # Mock existing published rule set
        mock_existing_published = {
            "id": existing_rule_set_id,
            "filename": "original_published.xlsx",
            "sha256Hash": expected_hash,
            "uploadedAt": "2025-01-01T10:00:00Z",
            "year": 2025,
            "quarter": "Q1",
            "status": "active"
        }

        with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=expected_hash):
            with patch('src.services.file_service.FileService.check_duplicate_file', return_value=True):
                with patch('src.services.file_service.FileService.find_existing_rule_set_by_hash', return_value=mock_existing_published):
                    response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert response.status_code == 409
        conflict_result = response.json()

        assert conflict_result["error"] == "DUPLICATE_FILE"
        assert conflict_result["existingRuleSetId"] == existing_rule_set_id
        # Message should indicate that the existing rule set is published/active
        assert "active" in conflict_result["message"].lower() or "published" in conflict_result["message"].lower()

    def test_sha256_hash_calculation_consistency(self):
        """Test that SHA256 hash calculation is consistent"""
        # Create file content
        file_content = b"Consistent content for hash testing with some data: 12345"
        expected_hash = hashlib.sha256(file_content).hexdigest()

        excel_file = io.BytesIO(file_content)
        files = {"file": ("hash_test.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        # Mock file service to return actual calculated hash
        def mock_hash_calculation(content):
            return hashlib.sha256(content).hexdigest()

        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', side_effect=mock_hash_calculation):
                with patch('src.services.file_service.FileService.check_duplicate_file', return_value=False):
                    mock_process.return_value = {
                        "withholding_rules": self._create_mock_rules(),
                        "composite_rules": self._create_mock_rules(),
                        "validation_issues": []
                    }

                    response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert response.status_code == 201
        result = response.json()

        # Verify that the hash in the response matches expected
        uploaded_file = result["uploadedFile"]
        assert uploaded_file["sha256Hash"] == expected_hash

    def test_duplicate_detection_case_sensitivity(self):
        """Test duplicate detection with different filenames (case sensitivity)"""
        file_content = b"Same content different case filenames"
        expected_hash = hashlib.sha256(file_content).hexdigest()

        # Upload with lowercase filename
        excel_file_1 = io.BytesIO(file_content)
        files_1 = {"file": ("lowercase.xlsx", excel_file_1, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=expected_hash):
                with patch('src.services.file_service.FileService.check_duplicate_file', return_value=False):
                    mock_process.return_value = {
                        "withholding_rules": self._create_mock_rules(),
                        "composite_rules": self._create_mock_rules(),
                        "validation_issues": []
                    }

                    first_response = self.client.post("/api/salt-rules/upload", files=files_1, data=data)

        assert first_response.status_code == 201
        first_rule_set_id = first_response.json()["ruleSetId"]

        # Upload with uppercase filename but same content
        excel_file_2 = io.BytesIO(file_content)
        files_2 = {"file": ("LOWERCASE.XLSX", excel_file_2, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        mock_existing_file = {
            "id": first_rule_set_id,
            "filename": "lowercase.xlsx",
            "sha256Hash": expected_hash,
            "uploadedAt": "2025-01-01T10:00:00Z"
        }

        with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=expected_hash):
            with patch('src.services.file_service.FileService.check_duplicate_file', return_value=True):
                with patch('src.services.file_service.FileService.find_existing_rule_set_by_hash', return_value=mock_existing_file):
                    second_response = self.client.post("/api/salt-rules/upload", files=files_2, data=data)

        assert second_response.status_code == 409
        # Should be detected as duplicate based on content hash, not filename

    def test_duplicate_detection_large_file_handling(self):
        """Test duplicate detection with large files"""
        # Simulate large file (close to 20MB limit)
        large_content = b"x" * (19 * 1024 * 1024)  # 19MB
        expected_hash = hashlib.sha256(large_content).hexdigest()

        excel_file = io.BytesIO(large_content)
        files = {"file": ("large_file.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        # Mock successful processing of large file
        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=expected_hash):
                with patch('src.services.file_service.FileService.check_duplicate_file', return_value=False):
                    mock_process.return_value = {
                        "withholding_rules": self._create_mock_rules(),
                        "composite_rules": self._create_mock_rules(),
                        "validation_issues": []
                    }

                    response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert response.status_code == 201
        result = response.json()

        # Verify large file hash is calculated correctly
        uploaded_file = result["uploadedFile"]
        assert uploaded_file["sha256Hash"] == expected_hash
        assert uploaded_file["fileSize"] == len(large_content)

    def test_duplicate_detection_database_consistency(self):
        """Test that duplicate detection maintains database consistency"""
        file_content = b"Database consistency test content"
        expected_hash = hashlib.sha256(file_content).hexdigest()

        excel_file = io.BytesIO(file_content)
        files = {"file": ("consistency.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        # First upload
        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=expected_hash):
                with patch('src.services.file_service.FileService.check_duplicate_file', return_value=False):
                    mock_process.return_value = {
                        "withholding_rules": self._create_mock_rules(),
                        "composite_rules": self._create_mock_rules(),
                        "validation_issues": []
                    }

                    first_response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert first_response.status_code == 201

        # Verify that subsequent lookup finds the stored hash
        mock_stored_file = {
            "id": first_response.json()["ruleSetId"],
            "filename": "consistency.xlsx",
            "sha256Hash": expected_hash,
            "uploadedAt": "2025-01-01T10:00:00Z"
        }

        # Second upload attempt
        excel_file_2 = io.BytesIO(file_content)
        files_2 = {"file": ("duplicate_consistency.xlsx", excel_file_2, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=expected_hash):
            with patch('src.services.file_service.FileService.check_duplicate_file', return_value=True):
                with patch('src.services.file_service.FileService.find_existing_rule_set_by_hash', return_value=mock_stored_file):
                    second_response = self.client.post("/api/salt-rules/upload", files=files_2, data=data)

        assert second_response.status_code == 409
        # Database should maintain consistency in hash lookups

    def _create_mock_rules(self):
        """Helper method to create mock rules for testing"""
        return [
            {
                "id": str(uuid4()),
                "stateCode": "CA",
                "entityType": "corporation",
                "taxRate": 0.0525,
                "incomeThreshold": 1000.00,
                "taxThreshold": 100.00
            }
        ]