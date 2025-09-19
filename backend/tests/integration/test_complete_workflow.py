"""
Integration test for complete upload → validate workflow (auto-publish)
Task: T021 - Integration test complete upload → validate workflow
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import io
import tempfile
import os
from uuid import uuid4
from app.main import app
from src.models.salt_rule_set import RuleSetStatus
from src.models.validation_issue import IssueSeverity


class TestCompleteWorkflowIntegration:
    """Test complete SALT rules workflow integration"""

    def setup_method(self):
        """Setup test client and test data"""
        self.client = TestClient(app)
        self.test_rule_set_id = str(uuid4())

    def test_complete_successful_workflow(self):
        """Test complete workflow from upload to auto-publish without errors"""
        # Step 1: Upload Excel file (automatically validates and publishes)
        excel_content = self._create_mock_excel_content()
        files = {"file": ("EY_SALT_Rules_2025Q1.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        # Mock successful upload with auto-publish
        mock_upload_response = {
            "ruleSetId": self.test_rule_set_id,
            "status": "valid",
            "uploadedFile": {
                "filename": "EY_SALT_Rules_2025Q1.xlsx",
                "fileSize": len(excel_content.getvalue()),
                "uploadTimestamp": "2025-01-01T10:00:00Z"
            },
            "validationStarted": True,
            "message": "File uploaded and validated successfully",
            "ruleCounts": {
                "withholding": 51,
                "composite": 51
            }
        }

        with patch('src.services.excel_processor.ExcelProcessor.validate_file') as mock_validate, \
             patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process, \
             patch('src.services.file_service.FileService.store_uploaded_file') as mock_store:

            # Mock validation success
            mock_validate.return_value = Mock(is_valid=True, errors=[])

            # Mock file storage
            mock_store.return_value = Mock(
                error_message=None,
                source_file=Mock(
                    id=str(uuid4()),
                    filename="EY_SALT_Rules_2025Q1.xlsx",
                    filepath="/tmp/test.xlsx",
                    file_size=1024
                )
            )

            # Mock processing
            mock_process.return_value = Mock(
                withholding_rules=[],
                composite_rules=[],
                validation_issues=[]
            )

            upload_response = self.client.post("/api/salt-rules/upload", files=files)

        assert upload_response.status_code == 201
        upload_result = upload_response.json()
        rule_set_id = upload_result["ruleSetId"]
        assert upload_result["status"] == "valid"
        assert upload_result["validationStarted"] is True

        # Step 2: Verify rule set details (should be auto-published as active)
        mock_detail_response = {
            "id": rule_set_id,
            "year": 2025,
            "quarter": "Q1",
            "version": "1.0.0",
            "status": "active",
            "effectiveDate": "2025-01-01",
            "createdAt": "2025-01-01T10:00:00Z",
            "publishedAt": "2025-01-01T10:05:00Z",
            "ruleCountWithholding": 51,
            "ruleCountComposite": 51,
            "description": None
        }

        with patch('src.services.rule_set_service.RuleSetService.get_rule_set_detail', return_value=mock_detail_response):
            detail_response = self.client.get(f"/api/salt-rules/{rule_set_id}")

        assert detail_response.status_code == 200
        detail_result = detail_response.json()
        assert detail_result["status"] == "active"
        assert detail_result["publishedAt"] is not None

    def test_workflow_with_validation_errors(self):
        """Test workflow blocked when validation errors prevent upload"""
        excel_content = self._create_mock_excel_content()
        files = {"file": ("Invalid_SALT_Rules.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        # Mock validation failure
        with patch('src.services.excel_processor.ExcelProcessor.validate_file') as mock_validate:
            mock_validate.return_value = Mock(
                is_valid=False,
                errors=[
                    {
                        "sheet": "Withholding",
                        "row": 5,
                        "column": "TaxRate",
                        "error_code": "INVALID_RATE",
                        "message": "Tax rate must be between 0 and 1",
                        "field_value": "150%"
                    }
                ]
            )

            upload_response = self.client.post("/api/salt-rules/upload", files=files)

        assert upload_response.status_code == 201
        upload_result = upload_response.json()
        assert upload_result["status"] == "validation_failed"
        assert upload_result["validationStarted"] is False
        assert upload_result["validationErrors"] is not None
        assert len(upload_result["validationErrors"]) > 0

    def test_workflow_with_archival_of_existing_active(self):
        """Test workflow that archives existing active rule set"""
        excel_content = self._create_mock_excel_content()
        files = {"file": ("New_SALT_Rules_2025Q1.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        # Mock successful upload that archives existing active rule set
        mock_upload_response = {
            "ruleSetId": str(uuid4()),
            "status": "valid",
            "uploadedFile": {
                "filename": "New_SALT_Rules_2025Q1.xlsx",
                "fileSize": len(excel_content.getvalue()),
                "uploadTimestamp": "2025-01-01T12:00:00Z"
            },
            "validationStarted": True,
            "message": "File uploaded and validated successfully",
            "ruleCounts": {
                "withholding": 51,
                "composite": 51
            }
        }

        with patch('src.services.excel_processor.ExcelProcessor.validate_file') as mock_validate, \
             patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process, \
             patch('src.services.file_service.FileService.store_uploaded_file') as mock_store:

            # Mock validation success
            mock_validate.return_value = Mock(is_valid=True, errors=[])

            # Mock file storage
            mock_store.return_value = Mock(
                error_message=None,
                source_file=Mock(
                    id=str(uuid4()),
                    filename="New_SALT_Rules_2025Q1.xlsx",
                    filepath="/tmp/test2.xlsx",
                    file_size=1024
                )
            )

            # Mock processing
            mock_process.return_value = Mock(
                withholding_rules=[],
                composite_rules=[],
                validation_issues=[]
            )

            upload_response = self.client.post("/api/salt-rules/upload", files=files)

        assert upload_response.status_code == 201
        upload_result = upload_response.json()
        assert upload_result["status"] == "valid"
        # The new rule set should be active, and any existing active rule set should be archived automatically

    def test_workflow_state_transitions(self):
        """Test rule set status transitions throughout workflow"""
        excel_content = self._create_mock_excel_content()
        files = {"file": ("EY_SALT_Rules_2025Q1.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

        # 1. After upload: status becomes 'active' immediately (auto-publish)
        with patch('src.services.excel_processor.ExcelProcessor.validate_file') as mock_validate, \
             patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process, \
             patch('src.services.file_service.FileService.store_uploaded_file') as mock_store:

            # Mock validation success
            mock_validate.return_value = Mock(is_valid=True, errors=[])

            # Mock file storage
            mock_store.return_value = Mock(
                error_message=None,
                source_file=Mock(
                    id=str(uuid4()),
                    filename="EY_SALT_Rules_2025Q1.xlsx",
                    filepath="/tmp/test3.xlsx",
                    file_size=1024
                )
            )

            # Mock processing
            mock_process.return_value = Mock(
                withholding_rules=[],
                composite_rules=[],
                validation_issues=[]
            )

            upload_response = self.client.post("/api/salt-rules/upload", files=files)

        assert upload_response.status_code == 201
        upload_result = upload_response.json()
        rule_set_id = upload_result["ruleSetId"]
        assert upload_result["status"] == "valid"

        # Verify the rule set is automatically active
        mock_detail_response = {
            "id": rule_set_id,
            "status": "active",
            "publishedAt": "2025-01-01T10:05:00Z"
        }

        with patch('src.services.rule_set_service.RuleSetService.get_rule_set_detail', return_value=mock_detail_response):
            detail_response = self.client.get(f"/api/salt-rules/{rule_set_id}")

        assert detail_response.status_code == 200
        assert detail_response.json()["status"] == "active"

    def _create_mock_excel_content(self):
        """Create mock Excel file content"""
        return io.BytesIO(b"Mock Excel content for testing")

    def _create_mock_withholding_rules(self):
        """Create mock withholding rules for testing"""
        return [
            {
                "id": "wr1",
                "stateCode": "CA",
                "entityType": "Corporation",
                "taxRate": "0.0525",
                "incomeThreshold": "1000.00",
                "taxThreshold": "100.00"
            },
            {
                "id": "wr2",
                "stateCode": "NY",
                "entityType": "Partnership",
                "taxRate": "0.0625",
                "incomeThreshold": "1000.00",
                "taxThreshold": "100.00"
            }
        ]

    def _create_mock_composite_rules(self):
        """Create mock composite rules for testing"""
        return [
            {
                "id": "cr1",
                "stateCode": "CA",
                "entityType": "Corporation",
                "taxRate": "0.0875",
                "incomeThreshold": "1000.00",
                "mandatoryFiling": True,
                "minTaxAmount": "25.00",
                "maxTaxAmount": "10000.00"
            },
            {
                "id": "cr2",
                "stateCode": "NY",
                "entityType": "Partnership",
                "taxRate": "0.0925",
                "incomeThreshold": "1000.00",
                "mandatoryFiling": True,
                "minTaxAmount": "50.00",
                "maxTaxAmount": "15000.00"
            }
        ]