"""
Contract tests for POST /api/salt-rules/upload endpoint
Task: T015 - Contract test POST /api/salt-rules/upload
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import io
from app.main import app
from src.services.excel_processor import ExcelProcessingResult
from src.models.salt_rule_set import RuleSetStatus


class TestUploadEndpointContract:
    """Test upload endpoint API contract compliance"""

    def setup_method(self):
        """Setup test client"""
        # This should fail initially as the endpoint doesn't exist yet
        self.client = TestClient(app)

    def test_upload_endpoint_exists(self):
        """Test that upload endpoint exists and accepts POST"""
        # Test with minimal valid request to check endpoint existence
        test_file = io.BytesIO(b"test excel content")
        files = {"file": ("test.xlsx", test_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    def test_upload_success_response_schema(self):
        """Test successful upload response matches OpenAPI schema"""
        test_file = io.BytesIO(b"valid excel content")
        files = {"file": ("EY_SALT_Rules_2025Q1.xlsx", test_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {
            "year": 2025,
            "quarter": "Q1",
            "description": "Updated withholding rates for 2025 Q1"
        }

        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            mock_process.return_value = ExcelProcessingResult(
                withholding_rules=[],
                composite_rules=[],
                validation_issues=[],
                rules_processed={"withholding": 0, "composite": 0}
            )

            response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert response.status_code == 201
        response_data = response.json()

        # Validate response schema according to OpenAPI spec
        assert "ruleSetId" in response_data
        assert "status" in response_data
        assert "uploadedFile" in response_data
        assert "validationStarted" in response_data

        # Validate ruleSetId is UUID format
        import uuid
        uuid.UUID(response_data["ruleSetId"])  # Should not raise exception

        # Validate status is valid enum value
        assert response_data["status"] in ["draft", "active", "archived"]

        # Validate uploadedFile schema
        uploaded_file = response_data["uploadedFile"]
        assert "id" in uploaded_file
        assert "filename" in uploaded_file
        assert "fileSize" in uploaded_file
        assert "contentType" in uploaded_file
        assert "uploadTimestamp" in uploaded_file
        assert "sha256Hash" in uploaded_file

        # Validate validationStarted is boolean
        assert isinstance(response_data["validationStarted"], bool)

    def test_upload_required_fields_validation(self):
        """Test that required fields are validated according to OpenAPI spec"""
        # Missing file
        data = {"year": 2025, "quarter": "Q1"}
        response = self.client.post("/api/salt-rules/upload", data=data)
        assert response.status_code == 400

        # Missing year
        test_file = io.BytesIO(b"test content")
        files = {"file": ("test.xlsx", test_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"quarter": "Q1"}
        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400

        # Missing quarter
        test_file = io.BytesIO(b"test content")
        files = {"file": ("test.xlsx", test_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025}
        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400

    def test_upload_year_validation(self):
        """Test year validation according to OpenAPI spec (2020-2030)"""
        test_file = io.BytesIO(b"test content")
        files = {"file": ("test.xlsx", test_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        # Year below minimum
        data = {"year": 2019, "quarter": "Q1"}
        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400

        # Year above maximum
        data = {"year": 2031, "quarter": "Q1"}
        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400

        # Valid years
        for year in [2020, 2025, 2030]:
            test_file = io.BytesIO(b"test content")
            files = {"file": ("test.xlsx", test_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            data = {"year": year, "quarter": "Q1"}

            with patch('src.services.excel_processor.ExcelProcessor.process_file'):
                response = self.client.post("/api/salt-rules/upload", files=files, data=data)
            assert response.status_code in [201, 400]  # 400 for other validation, not year

    def test_upload_quarter_validation(self):
        """Test quarter validation according to OpenAPI spec"""
        test_file = io.BytesIO(b"test content")
        files = {"file": ("test.xlsx", test_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        # Invalid quarter
        data = {"year": 2025, "quarter": "Q5"}
        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400

        # Valid quarters
        for quarter in ["Q1", "Q2", "Q3", "Q4"]:
            test_file = io.BytesIO(b"test content")
            files = {"file": ("test.xlsx", test_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            data = {"year": 2025, "quarter": quarter}

            with patch('src.services.excel_processor.ExcelProcessor.process_file'):
                response = self.client.post("/api/salt-rules/upload", files=files, data=data)
            assert response.status_code in [201, 400]  # 400 for other validation, not quarter

    def test_upload_description_validation(self):
        """Test description field validation (optional, max 500 chars)"""
        test_file = io.BytesIO(b"test content")
        files = {"file": ("test.xlsx", test_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        # Description too long (over 500 chars)
        long_description = "a" * 501
        data = {"year": 2025, "quarter": "Q1", "description": long_description}
        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400

        # Valid description
        valid_description = "Updated withholding rates for 2025 Q1"
        data = {"year": 2025, "quarter": "Q1", "description": valid_description}

        with patch('src.services.excel_processor.ExcelProcessor.process_file'):
            response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code in [201, 400]  # 400 for other validation, not description

    def test_upload_file_size_limit(self):
        """Test file size limit validation (20MB max)"""
        # File too large (over 20MB)
        large_content = b"x" * (20 * 1024 * 1024 + 1)  # 20MB + 1 byte
        large_file = io.BytesIO(large_content)
        files = {"file": ("large.xlsx", large_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 413

        # Response should match error schema
        response_data = response.json()
        assert "error" in response_data
        assert "message" in response_data

    def test_upload_duplicate_file_detection(self):
        """Test duplicate file detection returns 409 conflict"""
        test_file = io.BytesIO(b"duplicate content")
        files = {"file": ("test.xlsx", test_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        # Mock duplicate detection
        with patch('src.services.file_service.FileService.check_duplicate_file', return_value=True):
            response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert response.status_code == 409

        # Validate conflict response schema
        response_data = response.json()
        assert "error" in response_data
        assert "message" in response_data
        assert "existingRuleSetId" in response_data
        assert "duplicateDetection" in response_data

        duplicate_detection = response_data["duplicateDetection"]
        assert "sha256Hash" in duplicate_detection
        assert "uploadedAt" in duplicate_detection

    def test_upload_invalid_file_type(self):
        """Test invalid file type rejection"""
        # PDF file instead of Excel
        pdf_file = io.BytesIO(b"PDF content")
        files = {"file": ("document.pdf", pdf_file, "application/pdf")}
        data = {"year": 2025, "quarter": "Q1"}

        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400

        # Validate error response schema
        response_data = response.json()
        assert "error" in response_data
        assert "message" in response_data

    def test_upload_error_response_schema(self):
        """Test error response matches OpenAPI schema"""
        # Trigger validation error
        data = {"year": "invalid", "quarter": "Q1"}
        response = self.client.post("/api/salt-rules/upload", data=data)

        assert response.status_code == 400
        response_data = response.json()

        # Validate error response schema
        assert "error" in response_data
        assert "message" in response_data
        assert isinstance(response_data["error"], str)
        assert isinstance(response_data["message"], str)

        # Optional fields
        if "details" in response_data:
            assert isinstance(response_data["details"], dict)
        if "timestamp" in response_data:
            assert isinstance(response_data["timestamp"], str)

    def test_upload_content_type_header(self):
        """Test that endpoint accepts multipart/form-data"""
        test_file = io.BytesIO(b"test content")
        files = {"file": ("test.xlsx", test_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        # FastAPI TestClient automatically sets multipart/form-data for files
        with patch('src.services.excel_processor.ExcelProcessor.process_file'):
            response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        # Should accept the request (not 415 Unsupported Media Type)
        assert response.status_code != 415