"""
Unit tests for ValidationIssue model validation
Task: T009 - Unit test ValidationIssue model validation
"""
import pytest
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import ValidationError
from src.models.validation_issue import ValidationIssue, IssueSeverity


class TestValidationIssueValidation:
    """Test ValidationIssue model validation rules"""

    def test_valid_validation_issue_creation(self):
        """Test creating a valid ValidationIssue instance"""
        valid_data = {
            "id": uuid4(),
            "rule_set_id": uuid4(),
            "sheet_name": "Withholding",
            "row_number": 15,
            "column_name": "State",
            "error_code": "INVALID_STATE",
            "severity": IssueSeverity.ERROR,
            "message": "Invalid state code 'ZZ' - must be valid US state",
            "field_value": "ZZ",
            "created_at": datetime.now()
        }

        # This should fail initially as ValidationIssue model doesn't exist yet
        issue = ValidationIssue(**valid_data)
        assert issue.sheet_name == "Withholding"
        assert issue.row_number == 15
        assert issue.severity == IssueSeverity.ERROR
        assert isinstance(issue.id, UUID)

    def test_sheet_name_validation(self):
        """Test sheet name validation rules"""
        valid_data = self._get_valid_data()

        # Test required sheet_name
        invalid_data = valid_data.copy()
        del invalid_data["sheet_name"]
        with pytest.raises(ValidationError):
            ValidationIssue(**invalid_data)

        # Test sheet name max length (255 chars)
        invalid_data = valid_data.copy()
        invalid_data["sheet_name"] = "a" * 256
        with pytest.raises(ValidationError):
            ValidationIssue(**invalid_data)

    def test_row_number_validation(self):
        """Test row number validation rules"""
        valid_data = self._get_valid_data()

        # Test required row_number
        invalid_data = valid_data.copy()
        del invalid_data["row_number"]
        with pytest.raises(ValidationError):
            ValidationIssue(**invalid_data)

        # Test positive integer requirement
        invalid_data = valid_data.copy()
        invalid_data["row_number"] = 0
        with pytest.raises(ValidationError):
            ValidationIssue(**invalid_data)

        invalid_data = valid_data.copy()
        invalid_data["row_number"] = -1
        with pytest.raises(ValidationError):
            ValidationIssue(**invalid_data)

    def test_column_name_validation(self):
        """Test column name validation rules"""
        valid_data = self._get_valid_data()

        # Test optional column_name
        test_data = valid_data.copy()
        del test_data["column_name"]
        issue = ValidationIssue(**test_data)
        assert issue.column_name is None

        # Test column name with value
        test_data = valid_data.copy()
        test_data["column_name"] = "EntityType"
        issue = ValidationIssue(**test_data)
        assert issue.column_name == "EntityType"

    def test_error_code_validation(self):
        """Test error code validation rules"""
        valid_data = self._get_valid_data()

        # Test required error_code
        invalid_data = valid_data.copy()
        del invalid_data["error_code"]
        with pytest.raises(ValidationError):
            ValidationIssue(**invalid_data)

        # Test structured format (uppercase with underscores)
        valid_codes = ["INVALID_STATE", "MISSING_FIELD", "DUPLICATE_RULE", "FORMAT_ERROR"]
        for code in valid_codes:
            test_data = valid_data.copy()
            test_data["error_code"] = code
            issue = ValidationIssue(**test_data)
            assert issue.error_code == code

    def test_severity_validation(self):
        """Test severity validation rules"""
        valid_data = self._get_valid_data()

        # Test required severity
        invalid_data = valid_data.copy()
        del invalid_data["severity"]
        with pytest.raises(ValidationError):
            ValidationIssue(**invalid_data)

        # Test invalid severity value
        invalid_data = valid_data.copy()
        invalid_data["severity"] = "critical"
        with pytest.raises(ValidationError):
            ValidationIssue(**invalid_data)

        # Test valid severity values
        test_data = valid_data.copy()
        test_data["severity"] = IssueSeverity.WARNING
        issue = ValidationIssue(**test_data)
        assert issue.severity == IssueSeverity.WARNING

    def test_message_validation(self):
        """Test message validation rules"""
        valid_data = self._get_valid_data()

        # Test required message
        invalid_data = valid_data.copy()
        del invalid_data["message"]
        with pytest.raises(ValidationError):
            ValidationIssue(**invalid_data)

        # Test message max length (1000 chars)
        invalid_data = valid_data.copy()
        invalid_data["message"] = "a" * 1001
        with pytest.raises(ValidationError):
            ValidationIssue(**invalid_data)

        # Test valid message
        test_data = valid_data.copy()
        test_data["message"] = "A valid error message with details"
        issue = ValidationIssue(**test_data)
        assert issue.message == "A valid error message with details"

    def test_field_value_validation(self):
        """Test field value validation rules"""
        valid_data = self._get_valid_data()

        # Test optional field_value
        test_data = valid_data.copy()
        del test_data["field_value"]
        issue = ValidationIssue(**test_data)
        assert issue.field_value is None

        # Test field value with content
        test_data = valid_data.copy()
        test_data["field_value"] = "Invalid Value"
        issue = ValidationIssue(**test_data)
        assert issue.field_value == "Invalid Value"

    def test_rule_set_id_validation(self):
        """Test rule set ID validation rules"""
        valid_data = self._get_valid_data()

        # Test required rule_set_id
        invalid_data = valid_data.copy()
        del invalid_data["rule_set_id"]
        with pytest.raises(ValidationError):
            ValidationIssue(**invalid_data)

        # Test valid UUID
        test_uuid = uuid4()
        test_data = valid_data.copy()
        test_data["rule_set_id"] = test_uuid
        issue = ValidationIssue(**test_data)
        assert issue.rule_set_id == test_uuid

    def _get_valid_data(self):
        """Helper method to get valid test data"""
        return {
            "id": uuid4(),
            "rule_set_id": uuid4(),
            "sheet_name": "Withholding",
            "row_number": 15,
            "column_name": "State",
            "error_code": "INVALID_STATE",
            "severity": IssueSeverity.ERROR,
            "message": "Invalid state code 'ZZ' - must be valid US state",
            "field_value": "ZZ",
            "created_at": datetime.now()
        }