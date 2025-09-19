"""
Integration test for error handling with invalid Excel files
Task: T022 - Integration test error handling with invalid Excel files
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import io
import tempfile
from uuid import uuid4
from app.main import app


class TestErrorScenariosIntegration:
    """Test error handling scenarios with invalid files and data"""

    def setup_method(self):
        """Setup test client"""
        # This should fail initially as error handling doesn't exist yet
        self.client = TestClient(app)

    def test_invalid_file_format_rejection(self):
        """Test rejection of non-Excel file formats"""
        # Test PDF file
        pdf_content = io.BytesIO(b"%PDF-1.4 fake PDF content")
        files = {"file": ("document.pdf", pdf_content, "application/pdf")}
        data = {"year": 2025, "quarter": "Q1"}

        response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert response.status_code == 400
        error_result = response.json()
        assert "error" in error_result
        assert "file format" in error_result["message"].lower() or "content type" in error_result["message"].lower()

        # Test text file
        text_content = io.BytesIO(b"This is a text file, not Excel")
        files = {"file": ("data.txt", text_content, "text/plain")}
        data = {"year": 2025, "quarter": "Q1"}

        response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert response.status_code == 400

        # Test CSV file (not Excel)
        csv_content = io.BytesIO(b"State,EntityType,TaxRate\nCA,Corporation,0.0525")
        files = {"file": ("data.csv", csv_content, "text/csv")}
        data = {"year": 2025, "quarter": "Q1"}

        response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert response.status_code == 400

    def test_file_size_limit_enforcement(self):
        """Test enforcement of 20MB file size limit"""
        # Create file larger than 20MB
        large_content = b"x" * (21 * 1024 * 1024)  # 21MB
        large_file = io.BytesIO(large_content)
        files = {"file": ("huge_file.xlsx", large_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert response.status_code == 413  # Payload Too Large
        error_result = response.json()
        assert "error" in error_result
        assert "size" in error_result["message"].lower() or "large" in error_result["message"].lower()

    def test_malformed_excel_file_handling(self):
        """Test handling of corrupted or malformed Excel files"""
        # Fake Excel file with incorrect content
        fake_excel = io.BytesIO(b"This is not really an Excel file content")
        files = {"file": ("fake.xlsx", fake_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        # Mock Excel processor to simulate parsing error
        with patch('src.services.excel_processor.ExcelProcessor.process_file', side_effect=Exception("Unable to parse Excel file")):
            response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert response.status_code == 400
        error_result = response.json()
        assert "error" in error_result
        assert "excel" in error_result["message"].lower() or "parse" in error_result["message"].lower()

    def test_missing_required_excel_sheets(self):
        """Test handling of Excel files missing required sheets"""
        excel_content = io.BytesIO(b"Valid Excel format but wrong sheets")
        files = {"file": ("wrong_sheets.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        # Mock Excel processor to simulate missing sheets
        with patch('src.services.excel_processor.ExcelProcessor.process_file', side_effect=ValueError("Missing required sheets: Withholding, Composite")):
            response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert response.status_code == 400
        error_result = response.json()
        assert "error" in error_result
        assert "sheet" in error_result["message"].lower()

    def test_invalid_data_in_excel_sheets(self):
        """Test handling of invalid data within Excel sheets"""
        excel_content = io.BytesIO(b"Excel with invalid data")
        files = {"file": ("invalid_data.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        # Mock validation issues from Excel processing
        mock_validation_issues = [
            {
                "sheetName": "Withholding",
                "rowNumber": 5,
                "columnName": "State",
                "errorCode": "INVALID_STATE",
                "severity": "error",
                "message": "Invalid state code 'ZZ' - must be valid US state",
                "fieldValue": "ZZ"
            },
            {
                "sheetName": "Withholding",
                "rowNumber": 10,
                "columnName": "TaxRate",
                "errorCode": "INVALID_DATA_TYPE",
                "severity": "error",
                "message": "Tax rate must be numeric",
                "fieldValue": "invalid"
            },
            {
                "sheetName": "Composite",
                "rowNumber": 15,
                "columnName": "MandatoryFiling",
                "errorCode": "INVALID_BOOLEAN",
                "severity": "error",
                "message": "Mandatory filing must be true/false",
                "fieldValue": "maybe"
            }
        ]

        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            mock_process.return_value = {
                "withholding_rules": [],
                "composite_rules": [],
                "validation_issues": mock_validation_issues
            }

            response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        # Upload should succeed but validation should show errors
        assert response.status_code == 201
        rule_set_id = response.json()["ruleSetId"]

        # Check validation shows multiple errors
        mock_validation_response = {
            "ruleSetId": rule_set_id,
            "status": "failed",
            "summary": {
                "totalIssues": 3,
                "errorCount": 3,
                "warningCount": 0,
                "rulesProcessed": {"withholding": 0, "composite": 0}
            },
            "issues": mock_validation_issues
        }

        with patch('src.services.validation_service.ValidationService.get_validation_results', return_value=mock_validation_response):
            validation_response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")

        assert validation_response.status_code == 200
        validation_result = validation_response.json()
        assert validation_result["summary"]["errorCount"] == 3
        assert validation_result["status"] == "failed"

        # Publishing should be blocked
        publish_data = {"confirmArchive": True}
        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set',
                  side_effect=ValueError("Cannot publish with validation errors")):
            publish_response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=publish_data)

        assert publish_response.status_code == 400

    def test_duplicate_file_detection_and_rejection(self):
        """Test detection and rejection of duplicate files"""
        excel_content = io.BytesIO(b"Duplicate Excel content")
        files = {"file": ("duplicate.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        existing_rule_set_id = str(uuid4())

        # Mock duplicate detection
        with patch('src.services.file_service.FileService.check_duplicate_file', return_value=True):
            with patch('src.services.file_service.FileService.find_existing_rule_set_by_hash', return_value={
                "id": existing_rule_set_id,
                "filename": "original.xlsx",
                "uploadedAt": "2025-01-01T10:00:00Z"
            }):
                response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert response.status_code == 409  # Conflict
        conflict_result = response.json()
        assert "error" in conflict_result
        assert "duplicate" in conflict_result["message"].lower()
        assert "existingRuleSetId" in conflict_result
        assert conflict_result["existingRuleSetId"] == existing_rule_set_id

        # Verify duplicate detection metadata
        if "duplicateDetection" in conflict_result:
            duplicate_info = conflict_result["duplicateDetection"]
            assert "sha256Hash" in duplicate_info
            assert "uploadedAt" in duplicate_info

    def test_invalid_request_parameters(self):
        """Test handling of invalid request parameters"""
        excel_content = io.BytesIO(b"Valid Excel content")
        files = {"file": ("test.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        # Invalid year (out of range)
        data = {"year": 2019, "quarter": "Q1"}  # Below 2020 minimum
        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400

        data = {"year": 2031, "quarter": "Q1"}  # Above 2030 maximum
        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400

        # Invalid quarter
        data = {"year": 2025, "quarter": "Q5"}
        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400

        # Missing required parameters
        data = {"quarter": "Q1"}  # Missing year
        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400

        data = {"year": 2025}  # Missing quarter
        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400

        # Description too long
        data = {"year": 2025, "quarter": "Q1", "description": "a" * 501}  # Over 500 char limit
        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400

    def test_missing_file_in_upload(self):
        """Test handling when no file is provided in upload"""
        data = {"year": 2025, "quarter": "Q1"}

        response = self.client.post("/api/salt-rules/upload", data=data)

        assert response.status_code == 400
        error_result = response.json()
        assert "error" in error_result
        assert "file" in error_result["message"].lower()

    def test_invalid_rule_set_id_in_subsequent_requests(self):
        """Test handling of invalid rule set IDs in validation/preview/publish requests"""
        # Test validation with invalid UUID
        invalid_id = "not-a-uuid"
        response = self.client.get(f"/api/salt-rules/{invalid_id}/validation")
        assert response.status_code == 400

        # Test preview with invalid UUID
        response = self.client.get(f"/api/salt-rules/{invalid_id}/preview")
        assert response.status_code == 400

        # Test publish with invalid UUID
        publish_data = {"confirmArchive": True}
        response = self.client.post(f"/api/salt-rules/{invalid_id}/publish", json=publish_data)
        assert response.status_code == 400

        # Test detail with invalid UUID
        response = self.client.get(f"/api/salt-rules/{invalid_id}")
        assert response.status_code == 400

    def test_non_existent_rule_set_access(self):
        """Test handling of requests for non-existent rule sets"""
        non_existent_id = str(uuid4())

        # Mock service to simulate rule set not found
        with patch('src.services.validation_service.ValidationService.get_validation_results',
                  side_effect=ValueError("Rule set not found")):
            response = self.client.get(f"/api/salt-rules/{non_existent_id}/validation")

        assert response.status_code == 404

        with patch('src.services.comparison_service.ComparisonService.compare_rule_sets',
                  side_effect=ValueError("Rule set not found")):
            response = self.client.get(f"/api/salt-rules/{non_existent_id}/preview")

        assert response.status_code == 404

        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set',
                  side_effect=ValueError("Rule set not found")):
            publish_data = {"confirmArchive": True}
            response = self.client.post(f"/api/salt-rules/{non_existent_id}/publish", json=publish_data)

        assert response.status_code == 404

        with patch('src.services.rule_set_service.RuleSetService.get_rule_set_detail',
                  side_effect=ValueError("Rule set not found")):
            response = self.client.get(f"/api/salt-rules/{non_existent_id}")

        assert response.status_code == 404

    def test_concurrent_upload_conflicts(self):
        """Test handling of concurrent uploads for same year/quarter"""
        excel_content1 = io.BytesIO(b"First upload content")
        excel_content2 = io.BytesIO(b"Second upload content")

        files1 = {"file": ("first.xlsx", excel_content1, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        files2 = {"file": ("second.xlsx", excel_content2, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        # First upload succeeds
        with patch('src.services.excel_processor.ExcelProcessor.process_file'):
            response1 = self.client.post("/api/salt-rules/upload", files=files1, data=data)

        assert response1.status_code == 201
        first_rule_set_id = response1.json()["ruleSetId"]

        # Second upload for same year/quarter should be allowed (draft state)
        # But if first is already active, it should require confirmation
        with patch('src.services.excel_processor.ExcelProcessor.process_file'):
            response2 = self.client.post("/api/salt-rules/upload", files=files2, data=data)

        # This depends on business logic - could be 201 (allowed) or 409 (conflict)
        assert response2.status_code in [201, 409]

    def test_database_connection_errors(self):
        """Test handling of database connection errors"""
        excel_content = io.BytesIO(b"Valid Excel content")
        files = {"file": ("test.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        # Mock database connection error during upload
        with patch('src.services.excel_processor.ExcelProcessor.process_file',
                  side_effect=Exception("Database connection failed")):
            response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert response.status_code == 500
        error_result = response.json()
        assert "error" in error_result

    def test_file_storage_errors(self):
        """Test handling of file storage errors"""
        excel_content = io.BytesIO(b"Valid Excel content")
        files = {"file": ("test.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        # Mock file storage error
        with patch('src.services.file_service.FileService.store_uploaded_file',
                  side_effect=IOError("Disk full - cannot store file")):
            response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert response.status_code == 500
        error_result = response.json()
        assert "error" in error_result

    def test_malformed_json_in_publish_request(self):
        """Test handling of malformed JSON in publish requests"""
        rule_set_id = str(uuid4())

        # Send malformed JSON
        response = self.client.post(
            f"/api/salt-rules/{rule_set_id}/publish",
            headers={"content-type": "application/json"},
            content='{"effectiveDate": "2025-01-01", "confirmArchive": true, malformed'
        )

        assert response.status_code == 400
        error_result = response.json()
        assert "error" in error_result

    def test_unsupported_content_type_in_publish(self):
        """Test handling of unsupported content types in publish requests"""
        rule_set_id = str(uuid4())

        # Send as form data instead of JSON
        response = self.client.post(
            f"/api/salt-rules/{rule_set_id}/publish",
            data={"confirmArchive": "true"}
        )

        assert response.status_code in [400, 415]  # Bad Request or Unsupported Media Type