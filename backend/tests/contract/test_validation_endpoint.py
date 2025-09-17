"""
Contract tests for GET /api/salt-rules/{ruleSetId}/validation endpoint
Task: T016 - Contract test GET /api/salt-rules/{ruleSetId}/validation
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from uuid import uuid4
from app.main import app


class TestValidationEndpointContract:
    """Test validation endpoint API contract compliance"""

    def setup_method(self):
        """Setup test client"""
        # This should fail initially as the endpoint doesn't exist yet
        self.client = TestClient(app)

    def test_validation_endpoint_exists(self):
        """Test that validation endpoint exists and accepts GET"""
        rule_set_id = str(uuid4())
        response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")

        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    def test_validation_success_response_schema_json(self):
        """Test successful validation response matches OpenAPI schema (JSON format)"""
        rule_set_id = str(uuid4())

        # Mock validation service response
        mock_validation_result = {
            "ruleSetId": rule_set_id,
            "status": "completed",
            "summary": {
                "totalIssues": 5,
                "errorCount": 2,
                "warningCount": 3,
                "rulesProcessed": {
                    "withholding": 51,
                    "composite": 51
                }
            },
            "issues": [
                {
                    "sheetName": "Withholding",
                    "rowNumber": 15,
                    "columnName": "State",
                    "errorCode": "INVALID_STATE",
                    "severity": "error",
                    "message": "Invalid state code 'ZZ' - must be valid US state",
                    "fieldValue": "ZZ"
                }
            ],
            "csvDownloadUrl": f"/api/salt-rules/{rule_set_id}/validation?format=csv"
        }

        with patch('src.services.validation_service.ValidationService.get_validation_results', return_value=mock_validation_result):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")

        assert response.status_code == 200
        response_data = response.json()

        # Validate response schema according to OpenAPI spec
        assert "ruleSetId" in response_data
        assert "status" in response_data
        assert "summary" in response_data
        assert "issues" in response_data

        # Validate ruleSetId is UUID format
        import uuid
        uuid.UUID(response_data["ruleSetId"])

        # Validate status enum
        assert response_data["status"] in ["validating", "completed", "failed"]

        # Validate summary schema
        summary = response_data["summary"]
        assert "totalIssues" in summary
        assert "errorCount" in summary
        assert "warningCount" in summary
        assert "rulesProcessed" in summary
        assert isinstance(summary["totalIssues"], int)
        assert isinstance(summary["errorCount"], int)
        assert isinstance(summary["warningCount"], int)

        rules_processed = summary["rulesProcessed"]
        assert "withholding" in rules_processed
        assert "composite" in rules_processed
        assert isinstance(rules_processed["withholding"], int)
        assert isinstance(rules_processed["composite"], int)

        # Validate issues array
        assert isinstance(response_data["issues"], list)
        if len(response_data["issues"]) > 0:
            issue = response_data["issues"][0]
            assert "sheetName" in issue
            assert "rowNumber" in issue
            assert "errorCode" in issue
            assert "severity" in issue
            assert "message" in issue
            assert isinstance(issue["rowNumber"], int)
            assert issue["severity"] in ["error", "warning"]

        # Optional csvDownloadUrl
        if "csvDownloadUrl" in response_data:
            assert isinstance(response_data["csvDownloadUrl"], str)

    def test_validation_response_csv_format(self):
        """Test validation response in CSV format"""
        rule_set_id = str(uuid4())

        mock_csv_data = "sheet_name,row_number,column_name,error_code,severity,message,field_value\nWithholding,15,State,INVALID_STATE,error,Invalid state code,ZZ"

        with patch('src.services.validation_service.ValidationService.get_validation_results_csv', return_value=mock_csv_data):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation?format=csv")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "sheet_name,row_number,column_name,error_code,severity,message,field_value" in response.text

    def test_validation_format_parameter_validation(self):
        """Test format query parameter validation"""
        rule_set_id = str(uuid4())

        # Valid formats
        for format_type in ["json", "csv"]:
            with patch('src.services.validation_service.ValidationService.get_validation_results'):
                response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation?format={format_type}")
            assert response.status_code in [200, 404]  # 404 if rule set not found

        # Invalid format
        response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation?format=xml")
        assert response.status_code == 400

    def test_validation_default_format_is_json(self):
        """Test that default format is JSON when format parameter is omitted"""
        rule_set_id = str(uuid4())

        mock_validation_result = {
            "ruleSetId": rule_set_id,
            "status": "completed",
            "summary": {
                "totalIssues": 0,
                "errorCount": 0,
                "warningCount": 0,
                "rulesProcessed": {"withholding": 0, "composite": 0}
            },
            "issues": []
        }

        with patch('src.services.validation_service.ValidationService.get_validation_results', return_value=mock_validation_result):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        response_data = response.json()
        assert "ruleSetId" in response_data

    def test_validation_rule_set_not_found(self):
        """Test 404 response when rule set doesn't exist"""
        non_existent_id = str(uuid4())

        with patch('src.services.validation_service.ValidationService.get_validation_results', side_effect=ValueError("Rule set not found")):
            response = self.client.get(f"/api/salt-rules/{non_existent_id}/validation")

        assert response.status_code == 404
        response_data = response.json()

        # Validate error response schema
        assert "error" in response_data
        assert "message" in response_data
        assert isinstance(response_data["error"], str)
        assert isinstance(response_data["message"], str)

    def test_validation_invalid_rule_set_id_format(self):
        """Test 400 response for invalid UUID format"""
        invalid_id = "not-a-uuid"
        response = self.client.get(f"/api/salt-rules/{invalid_id}/validation")

        assert response.status_code == 400
        response_data = response.json()

        # Validate error response schema
        assert "error" in response_data
        assert "message" in response_data

    def test_validation_status_values(self):
        """Test all possible validation status values"""
        rule_set_id = str(uuid4())

        for status in ["validating", "completed", "failed"]:
            mock_result = {
                "ruleSetId": rule_set_id,
                "status": status,
                "summary": {
                    "totalIssues": 0,
                    "errorCount": 0,
                    "warningCount": 0,
                    "rulesProcessed": {"withholding": 0, "composite": 0}
                },
                "issues": []
            }

            with patch('src.services.validation_service.ValidationService.get_validation_results', return_value=mock_result):
                response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")

            assert response.status_code == 200
            response_data = response.json()
            assert response_data["status"] == status

    def test_validation_issue_severity_values(self):
        """Test validation issue severity enum values"""
        rule_set_id = str(uuid4())

        mock_issues = [
            {
                "sheetName": "Withholding",
                "rowNumber": 10,
                "errorCode": "INVALID_STATE",
                "severity": "error",
                "message": "Error message"
            },
            {
                "sheetName": "Composite",
                "rowNumber": 20,
                "errorCode": "UNUSUAL_RATE",
                "severity": "warning",
                "message": "Warning message"
            }
        ]

        mock_result = {
            "ruleSetId": rule_set_id,
            "status": "completed",
            "summary": {
                "totalIssues": 2,
                "errorCount": 1,
                "warningCount": 1,
                "rulesProcessed": {"withholding": 51, "composite": 51}
            },
            "issues": mock_issues
        }

        with patch('src.services.validation_service.ValidationService.get_validation_results', return_value=mock_result):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")

        assert response.status_code == 200
        response_data = response.json()

        issues = response_data["issues"]
        assert len(issues) == 2
        assert issues[0]["severity"] == "error"
        assert issues[1]["severity"] == "warning"

    def test_validation_optional_fields(self):
        """Test optional fields in validation issue schema"""
        rule_set_id = str(uuid4())

        # Issue with all optional fields
        issue_with_optionals = {
            "sheetName": "Withholding",
            "rowNumber": 15,
            "columnName": "State",
            "errorCode": "INVALID_STATE",
            "severity": "error",
            "message": "Invalid state code",
            "fieldValue": "ZZ"
        }

        # Issue without optional fields
        issue_without_optionals = {
            "sheetName": "Composite",
            "rowNumber": 20,
            "errorCode": "MISSING_FIELD",
            "severity": "error",
            "message": "Required field missing"
            # No columnName or fieldValue
        }

        mock_result = {
            "ruleSetId": rule_set_id,
            "status": "completed",
            "summary": {
                "totalIssues": 2,
                "errorCount": 2,
                "warningCount": 0,
                "rulesProcessed": {"withholding": 51, "composite": 51}
            },
            "issues": [issue_with_optionals, issue_without_optionals]
        }

        with patch('src.services.validation_service.ValidationService.get_validation_results', return_value=mock_result):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")

        assert response.status_code == 200
        response_data = response.json()

        issues = response_data["issues"]
        # First issue has optional fields
        assert "columnName" in issues[0]
        assert "fieldValue" in issues[0]

        # Second issue may not have optional fields
        # (This would be validated by the actual implementation)