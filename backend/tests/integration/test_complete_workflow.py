"""
Integration test for complete upload → validate → preview → publish workflow
Task: T021 - Integration test complete upload → validate → preview → publish workflow
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
        # This should fail initially as the workflow doesn't exist yet
        self.client = TestClient(app)
        self.test_rule_set_id = str(uuid4())

    def test_complete_successful_workflow(self):
        """Test complete workflow from upload to publish without errors"""
        # Step 1: Upload Excel file
        excel_content = self._create_mock_excel_content()
        files = {"file": ("EY_SALT_Rules_2025Q1.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        upload_data = {
            "year": 2025,
            "quarter": "Q1",
            "description": "Test upload for workflow integration"
        }

        # Mock successful upload
        mock_upload_response = {
            "ruleSetId": self.test_rule_set_id,
            "status": "draft",
            "uploadedFile": {
                "id": str(uuid4()),
                "filename": "EY_SALT_Rules_2025Q1.xlsx",
                "fileSize": len(excel_content.getvalue()),
                "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "uploadTimestamp": "2025-01-01T10:00:00Z",
                "sha256Hash": "mock_hash_value"
            },
            "validationStarted": True
        }

        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            with patch('src.services.file_service.FileService.store_uploaded_file') as mock_store:
                mock_process.return_value = {
                    "withholding_rules": self._create_mock_withholding_rules(),
                    "composite_rules": self._create_mock_composite_rules(),
                    "validation_issues": []
                }
                mock_store.return_value = mock_upload_response["uploadedFile"]

                upload_response = self.client.post("/api/salt-rules/upload", files=files, data=upload_data)

        assert upload_response.status_code == 201
        upload_result = upload_response.json()
        rule_set_id = upload_result["ruleSetId"]

        # Step 2: Check validation status
        mock_validation_response = {
            "ruleSetId": rule_set_id,
            "status": "completed",
            "summary": {
                "totalIssues": 0,
                "errorCount": 0,
                "warningCount": 0,
                "rulesProcessed": {
                    "withholding": 2,
                    "composite": 2
                }
            },
            "issues": []
        }

        with patch('src.services.validation_service.ValidationService.get_validation_results', return_value=mock_validation_response):
            validation_response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")

        assert validation_response.status_code == 200
        validation_result = validation_response.json()
        assert validation_result["status"] == "completed"
        assert validation_result["summary"]["errorCount"] == 0

        # Step 3: Preview changes (compare with no active rule set)
        mock_preview_response = {
            "ruleSetId": rule_set_id,
            "comparison": {
                "added": [
                    {
                        "ruleType": "withholding",
                        "state": "CA",
                        "entityType": "corporation",
                        "changes": [
                            {"field": "tax_rate", "oldValue": None, "newValue": "0.0525"}
                        ]
                    },
                    {
                        "ruleType": "composite",
                        "state": "CA",
                        "entityType": "corporation",
                        "changes": [
                            {"field": "tax_rate", "oldValue": None, "newValue": "0.0625"}
                        ]
                    }
                ],
                "modified": [],
                "removed": []
            },
            "summary": {
                "rulesAdded": 2,
                "rulesModified": 0,
                "rulesRemoved": 0,
                "fieldsChanged": 2
            }
        }

        with patch('src.services.comparison_service.ComparisonService.compare_rule_sets', return_value=mock_preview_response):
            preview_response = self.client.get(f"/api/salt-rules/{rule_set_id}/preview")

        assert preview_response.status_code == 200
        preview_result = preview_response.json()
        assert preview_result["summary"]["rulesAdded"] == 2
        assert len(preview_result["comparison"]["added"]) == 2

        # Step 4: Publish the rule set
        publish_data = {
            "effectiveDate": "2025-01-01",
            "confirmArchive": True
        }

        mock_publish_response = {
            "ruleSetId": rule_set_id,
            "status": "active",
            "effectiveDate": "2025-01-01",
            "resolvedRulesGenerated": 102
        }

        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set', return_value=mock_publish_response):
            publish_response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=publish_data)

        assert publish_response.status_code == 200
        publish_result = publish_response.json()
        assert publish_result["status"] == "active"
        assert publish_result["resolvedRulesGenerated"] == 102

        # Step 5: Verify rule set details after publication
        mock_detail_response = {
            "id": rule_set_id,
            "year": 2025,
            "quarter": "Q1",
            "version": "1.0.0",
            "status": "active",
            "effectiveDate": "2025-01-01",
            "createdAt": "2025-01-01T10:00:00Z",
            "publishedAt": "2025-01-01T12:00:00Z",
            "sourceFile": mock_upload_response["uploadedFile"],
            "validationSummary": mock_validation_response["summary"],
            "rules": {
                "withholding": self._create_mock_withholding_rules(),
                "composite": self._create_mock_composite_rules()
            }
        }

        with patch('src.services.rule_set_service.RuleSetService.get_rule_set_detail', return_value=mock_detail_response):
            detail_response = self.client.get(f"/api/salt-rules/{rule_set_id}")

        assert detail_response.status_code == 200
        detail_result = detail_response.json()
        assert detail_result["status"] == "active"
        assert detail_result["publishedAt"] is not None

    def test_workflow_with_validation_warnings(self):
        """Test workflow with validation warnings (should still allow publish)"""
        # Upload with some validation warnings
        excel_content = self._create_mock_excel_content()
        files = {"file": ("EY_SALT_Rules_2025Q1.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        upload_data = {"year": 2025, "quarter": "Q1"}

        mock_upload_response = {
            "ruleSetId": self.test_rule_set_id,
            "status": "draft",
            "uploadedFile": {
                "id": str(uuid4()),
                "filename": "EY_SALT_Rules_2025Q1.xlsx",
                "fileSize": 1024,
                "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "uploadTimestamp": "2025-01-01T10:00:00Z",
                "sha256Hash": "mock_hash"
            },
            "validationStarted": True
        }

        # Mock upload with warnings
        mock_validation_issues = [
            {
                "sheetName": "Withholding",
                "rowNumber": 15,
                "errorCode": "UNUSUAL_RATE",
                "severity": "warning",
                "message": "Tax rate 0% is unusual for this state",
                "fieldValue": "0.0000"
            }
        ]

        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            mock_process.return_value = {
                "withholding_rules": self._create_mock_withholding_rules(),
                "composite_rules": self._create_mock_composite_rules(),
                "validation_issues": mock_validation_issues
            }

            upload_response = self.client.post("/api/salt-rules/upload", files=files, data=upload_data)

        assert upload_response.status_code == 201
        rule_set_id = upload_response.json()["ruleSetId"]

        # Check validation shows warnings
        mock_validation_response = {
            "ruleSetId": rule_set_id,
            "status": "completed",
            "summary": {
                "totalIssues": 1,
                "errorCount": 0,
                "warningCount": 1,
                "rulesProcessed": {"withholding": 2, "composite": 2}
            },
            "issues": mock_validation_issues
        }

        with patch('src.services.validation_service.ValidationService.get_validation_results', return_value=mock_validation_response):
            validation_response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")

        assert validation_response.status_code == 200
        validation_result = validation_response.json()
        assert validation_result["summary"]["warningCount"] == 1
        assert validation_result["summary"]["errorCount"] == 0

        # Should still be able to publish despite warnings
        publish_data = {"confirmArchive": True}
        mock_publish_response = {
            "ruleSetId": rule_set_id,
            "status": "active",
            "effectiveDate": "2025-01-01"
        }

        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set', return_value=mock_publish_response):
            publish_response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=publish_data)

        assert publish_response.status_code == 200

    def test_workflow_blocked_by_validation_errors(self):
        """Test workflow blocked when validation errors prevent publication"""
        # Upload with validation errors
        excel_content = self._create_mock_excel_content()
        files = {"file": ("Invalid_Rules.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        upload_data = {"year": 2025, "quarter": "Q1"}

        mock_validation_errors = [
            {
                "sheetName": "Withholding",
                "rowNumber": 10,
                "columnName": "State",
                "errorCode": "INVALID_STATE",
                "severity": "error",
                "message": "Invalid state code 'ZZ'",
                "fieldValue": "ZZ"
            },
            {
                "sheetName": "Composite",
                "rowNumber": 20,
                "columnName": "TaxRate",
                "errorCode": "INVALID_RATE_RANGE",
                "severity": "error",
                "message": "Tax rate must be between 0 and 1",
                "fieldValue": "1.5"
            }
        ]

        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            mock_process.return_value = {
                "withholding_rules": [],
                "composite_rules": [],
                "validation_issues": mock_validation_errors
            }

            upload_response = self.client.post("/api/salt-rules/upload", files=files, data=upload_data)

        assert upload_response.status_code == 201
        rule_set_id = upload_response.json()["ruleSetId"]

        # Check validation shows errors
        mock_validation_response = {
            "ruleSetId": rule_set_id,
            "status": "failed",
            "summary": {
                "totalIssues": 2,
                "errorCount": 2,
                "warningCount": 0,
                "rulesProcessed": {"withholding": 0, "composite": 0}
            },
            "issues": mock_validation_errors
        }

        with patch('src.services.validation_service.ValidationService.get_validation_results', return_value=mock_validation_response):
            validation_response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")

        assert validation_response.status_code == 200
        validation_result = validation_response.json()
        assert validation_result["summary"]["errorCount"] == 2
        assert validation_result["status"] == "failed"

        # Attempt to publish should fail
        publish_data = {"confirmArchive": True}

        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set',
                  side_effect=ValueError("Cannot publish with validation errors")):
            publish_response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=publish_data)

        assert publish_response.status_code == 400
        error_result = publish_response.json()
        assert "validation errors" in error_result["message"].lower()

    def test_workflow_with_rule_set_comparison(self):
        """Test workflow comparing against existing active rule set"""
        # Setup: Create existing active rule set
        existing_rule_set_id = str(uuid4())

        # Upload new rule set
        excel_content = self._create_mock_excel_content()
        files = {"file": ("EY_SALT_Rules_2025Q1_v2.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        upload_data = {"year": 2025, "quarter": "Q1", "description": "Updated rates"}

        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            mock_process.return_value = {
                "withholding_rules": self._create_mock_withholding_rules_modified(),
                "composite_rules": self._create_mock_composite_rules(),
                "validation_issues": []
            }

            upload_response = self.client.post("/api/salt-rules/upload", files=files, data=upload_data)

        assert upload_response.status_code == 201
        new_rule_set_id = upload_response.json()["ruleSetId"]

        # Preview shows comparison with existing rule set
        mock_preview_response = {
            "ruleSetId": new_rule_set_id,
            "comparison": {
                "added": [],
                "modified": [
                    {
                        "ruleType": "withholding",
                        "state": "CA",
                        "entityType": "corporation",
                        "changes": [
                            {"field": "tax_rate", "oldValue": "0.0525", "newValue": "0.0575"}
                        ]
                    }
                ],
                "removed": []
            },
            "summary": {
                "rulesAdded": 0,
                "rulesModified": 1,
                "rulesRemoved": 0,
                "fieldsChanged": 1
            }
        }

        with patch('src.services.comparison_service.ComparisonService.compare_rule_sets', return_value=mock_preview_response):
            preview_response = self.client.get(f"/api/salt-rules/{new_rule_set_id}/preview")

        assert preview_response.status_code == 200
        preview_result = preview_response.json()
        assert preview_result["summary"]["rulesModified"] == 1

        # Publish should archive existing rule set
        publish_data = {"confirmArchive": True}
        mock_publish_response = {
            "ruleSetId": new_rule_set_id,
            "status": "active",
            "effectiveDate": "2025-01-01",
            "archivedRuleSet": existing_rule_set_id,
            "resolvedRulesGenerated": 102
        }

        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set', return_value=mock_publish_response):
            publish_response = self.client.post(f"/api/salt-rules/{new_rule_set_id}/publish", json=publish_data)

        assert publish_response.status_code == 200
        publish_result = publish_response.json()
        assert publish_result["archivedRuleSet"] == existing_rule_set_id

    def test_workflow_state_transitions(self):
        """Test rule set status transitions throughout workflow"""
        excel_content = self._create_mock_excel_content()
        files = {"file": ("EY_SALT_Rules_2025Q1.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        upload_data = {"year": 2025, "quarter": "Q1"}

        # 1. After upload: status should be 'draft'
        with patch('src.services.excel_processor.ExcelProcessor.process_file'):
            upload_response = self.client.post("/api/salt-rules/upload", files=files, data=upload_data)

        assert upload_response.status_code == 201
        upload_result = upload_response.json()
        assert upload_result["status"] == "draft"
        rule_set_id = upload_result["ruleSetId"]

        # 2. During validation: status remains 'draft'
        mock_validating_response = {
            "ruleSetId": rule_set_id,
            "status": "validating",
            "summary": {"totalIssues": 0, "errorCount": 0, "warningCount": 0, "rulesProcessed": {"withholding": 0, "composite": 0}},
            "issues": []
        }

        with patch('src.services.validation_service.ValidationService.get_validation_results', return_value=mock_validating_response):
            validation_response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")

        assert validation_response.status_code == 200
        assert validation_response.json()["status"] == "validating"

        # 3. After validation complete: ready for publication
        mock_completed_response = {
            "ruleSetId": rule_set_id,
            "status": "completed",
            "summary": {"totalIssues": 0, "errorCount": 0, "warningCount": 0, "rulesProcessed": {"withholding": 2, "composite": 2}},
            "issues": []
        }

        with patch('src.services.validation_service.ValidationService.get_validation_results', return_value=mock_completed_response):
            validation_response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")

        assert validation_response.status_code == 200
        assert validation_response.json()["status"] == "completed"

        # 4. After publish: status becomes 'active'
        publish_data = {"confirmArchive": True}
        mock_publish_response = {
            "ruleSetId": rule_set_id,
            "status": "active",
            "effectiveDate": "2025-01-01"
        }

        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set', return_value=mock_publish_response):
            publish_response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=publish_data)

        assert publish_response.status_code == 200
        assert publish_response.json()["status"] == "active"

    def _create_mock_excel_content(self):
        """Create mock Excel file content"""
        return io.BytesIO(b"Mock Excel content for testing")

    def _create_mock_withholding_rules(self):
        """Create mock withholding rules"""
        return [
            {
                "id": str(uuid4()),
                "stateCode": "CA",
                "entityType": "corporation",
                "taxRate": 0.0525,
                "incomeThreshold": 1000.00,
                "taxThreshold": 100.00
            },
            {
                "id": str(uuid4()),
                "stateCode": "NY",
                "entityType": "partnership",
                "taxRate": 0.0625,
                "incomeThreshold": 1000.00,
                "taxThreshold": 100.00
            }
        ]

    def _create_mock_withholding_rules_modified(self):
        """Create mock modified withholding rules for comparison"""
        return [
            {
                "id": str(uuid4()),
                "stateCode": "CA",
                "entityType": "corporation",
                "taxRate": 0.0575,  # Modified rate
                "incomeThreshold": 1000.00,
                "taxThreshold": 100.00
            },
            {
                "id": str(uuid4()),
                "stateCode": "NY",
                "entityType": "partnership",
                "taxRate": 0.0625,
                "incomeThreshold": 1000.00,
                "taxThreshold": 100.00
            }
        ]

    def _create_mock_composite_rules(self):
        """Create mock composite rules"""
        return [
            {
                "id": str(uuid4()),
                "stateCode": "CA",
                "entityType": "corporation",
                "taxRate": 0.0625,
                "incomeThreshold": 1000.00,
                "mandatoryFiling": True,
                "minTaxAmount": 25.00,
                "maxTaxAmount": 10000.00
            },
            {
                "id": str(uuid4()),
                "stateCode": "NY",
                "entityType": "partnership",
                "taxRate": 0.0700,
                "incomeThreshold": 1000.00,
                "mandatoryFiling": True,
                "minTaxAmount": 50.00,
                "maxTaxAmount": 15000.00
            }
        ]