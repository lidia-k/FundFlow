"""
Unit tests for SaltRuleSet model validation
Task: T006 - Unit test SaltRuleSet model validation
"""
import pytest
from uuid import UUID, uuid4
from datetime import datetime, date
from pydantic import ValidationError
from src.models.salt_rule_set import SaltRuleSet, RuleSetStatus, Quarter


class TestSaltRuleSetValidation:
    """Test SaltRuleSet model validation rules"""

    def test_valid_salt_rule_set_creation(self):
        """Test creating a valid SaltRuleSet instance"""
        valid_data = {
            "id": uuid4(),
            "year": 2025,
            "quarter": Quarter.Q1,
            "version": "1.0.0",
            "status": RuleSetStatus.DRAFT,
            "effective_date": date(2025, 1, 1),
            "created_at": datetime.now(),
            "created_by": "admin@fundflow.com",
            "source_file_id": uuid4(),
            "rule_count_withholding": 51,
            "rule_count_composite": 51
        }

        # This should fail initially as SaltRuleSet model doesn't exist yet
        rule_set = SaltRuleSet(**valid_data)
        assert rule_set.year == 2025
        assert rule_set.quarter == Quarter.Q1
        assert rule_set.status == RuleSetStatus.DRAFT
        assert isinstance(rule_set.id, UUID)

    def test_year_validation(self):
        """Test year validation rules"""
        valid_data = self._get_valid_data()

        # Test required year
        invalid_data = valid_data.copy()
        del invalid_data["year"]
        with pytest.raises(ValidationError):
            SaltRuleSet(**invalid_data)

        # Test year below range
        invalid_data = valid_data.copy()
        invalid_data["year"] = 2019
        with pytest.raises(ValidationError):
            SaltRuleSet(**invalid_data)

        # Test year above range
        invalid_data = valid_data.copy()
        invalid_data["year"] = 2031
        with pytest.raises(ValidationError):
            SaltRuleSet(**invalid_data)

    def test_quarter_validation(self):
        """Test quarter validation rules"""
        valid_data = self._get_valid_data()

        # Test required quarter
        invalid_data = valid_data.copy()
        del invalid_data["quarter"]
        with pytest.raises(ValidationError):
            SaltRuleSet(**invalid_data)

        # Test invalid quarter value
        invalid_data = valid_data.copy()
        invalid_data["quarter"] = "Q5"
        with pytest.raises(ValidationError):
            SaltRuleSet(**invalid_data)

    def test_version_validation(self):
        """Test version validation rules"""
        valid_data = self._get_valid_data()

        # Test required version
        invalid_data = valid_data.copy()
        del invalid_data["version"]
        with pytest.raises(ValidationError):
            SaltRuleSet(**invalid_data)

        # Test invalid semantic version format
        invalid_data = valid_data.copy()
        invalid_data["version"] = "1.0"
        with pytest.raises(ValidationError):
            SaltRuleSet(**invalid_data)

    def test_status_validation(self):
        """Test status validation rules"""
        valid_data = self._get_valid_data()

        # Test required status
        invalid_data = valid_data.copy()
        del invalid_data["status"]
        with pytest.raises(ValidationError):
            SaltRuleSet(**invalid_data)

        # Test invalid status value
        invalid_data = valid_data.copy()
        invalid_data["status"] = "invalid"
        with pytest.raises(ValidationError):
            SaltRuleSet(**invalid_data)

    def test_effective_date_validation(self):
        """Test effective date validation rules"""
        valid_data = self._get_valid_data()

        # Test required effective_date
        invalid_data = valid_data.copy()
        del invalid_data["effective_date"]
        with pytest.raises(ValidationError):
            SaltRuleSet(**invalid_data)

        # Test future date requirement for drafts
        invalid_data = valid_data.copy()
        invalid_data["effective_date"] = date(2020, 1, 1)  # Past date
        invalid_data["status"] = RuleSetStatus.DRAFT
        with pytest.raises(ValidationError):
            SaltRuleSet(**invalid_data)

    def test_unique_constraint_logic(self):
        """Test unique constraint for (year, quarter, status='active')"""
        # This would be tested at the database level, but we can test model logic
        valid_data = self._get_valid_data()
        valid_data["status"] = RuleSetStatus.ACTIVE

        rule_set = SaltRuleSet(**valid_data)
        assert rule_set.status == RuleSetStatus.ACTIVE
        # Unique constraint would be enforced by database

    def test_rule_count_validation(self):
        """Test rule count field validation"""
        valid_data = self._get_valid_data()

        # Test negative rule counts
        invalid_data = valid_data.copy()
        invalid_data["rule_count_withholding"] = -1
        with pytest.raises(ValidationError):
            SaltRuleSet(**invalid_data)

        invalid_data = valid_data.copy()
        invalid_data["rule_count_composite"] = -1
        with pytest.raises(ValidationError):
            SaltRuleSet(**invalid_data)

    def _get_valid_data(self):
        """Helper method to get valid test data"""
        return {
            "id": uuid4(),
            "year": 2025,
            "quarter": Quarter.Q1,
            "version": "1.0.0",
            "status": RuleSetStatus.DRAFT,
            "effective_date": date(2025, 1, 1),
            "created_at": datetime.now(),
            "created_by": "admin@fundflow.com",
            "source_file_id": uuid4(),
            "rule_count_withholding": 51,
            "rule_count_composite": 51
        }