"""
Unit tests for WithholdingRule model validation
Task: T007 - Unit test WithholdingRule model validation
"""
import pytest
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError
from src.models.withholding_rule import WithholdingRule
from src.models.enums import USJurisdiction


class TestWithholdingRuleValidation:
    """Test WithholdingRule model validation rules"""

    def test_valid_withholding_rule_creation(self):
        """Test creating a valid WithholdingRule instance"""
        valid_data = {
            "id": uuid4(),
            "rule_set_id": uuid4(),
            "state_code": USJurisdiction.CA,
            "entity_type": "Corporation",
            "tax_rate": Decimal("0.0525"),
            "income_threshold": Decimal("1000.00"),
            "tax_threshold": Decimal("100.00"),
            "created_at": datetime.now()
        }

        # This should fail initially as WithholdingRule model doesn't exist yet
        rule = WithholdingRule(**valid_data)
        assert rule.state_code == USJurisdiction.CA
        assert rule.entity_type == "Corporation"
        assert rule.tax_rate == Decimal("0.0525")
        assert isinstance(rule.id, UUID)

    def test_state_code_validation(self):
        """Test state code validation rules"""
        valid_data = self._get_valid_data()

        # Test required state_code
        invalid_data = valid_data.copy()
        del invalid_data["state_code"]
        with pytest.raises(ValidationError):
            WithholdingRule(**invalid_data)

        # Test invalid state code
        invalid_data = valid_data.copy()
        invalid_data["state_code"] = "ZZ"
        with pytest.raises(ValidationError):
            WithholdingRule(**invalid_data)

    def test_entity_type_validation(self):
        """Test entity type validation rules"""
        valid_data = self._get_valid_data()

        # Test required entity_type
        invalid_data = valid_data.copy()
        del invalid_data["entity_type"]
        with pytest.raises(ValidationError):
            WithholdingRule(**invalid_data)

        # Test invalid entity type
        invalid_data = valid_data.copy()
        invalid_data["entity_type"] = "InvalidType"
        with pytest.raises(ValidationError):
            WithholdingRule(**invalid_data)

        # Test valid entity types
        valid_types = ["Corporation", "Partnership", "Individual", "Trust", "S Corporation", "Exempt Org", "IRA"]
        for entity_type in valid_types:
            test_data = valid_data.copy()
            test_data["entity_type"] = entity_type
            rule = WithholdingRule(**test_data)
            assert rule.entity_type == entity_type

    def test_tax_rate_validation(self):
        """Test tax rate validation rules"""
        valid_data = self._get_valid_data()

        # Test required tax_rate
        invalid_data = valid_data.copy()
        del invalid_data["tax_rate"]
        with pytest.raises(ValidationError):
            WithholdingRule(**invalid_data)

        # Test negative tax rate
        invalid_data = valid_data.copy()
        invalid_data["tax_rate"] = Decimal("-0.01")
        with pytest.raises(ValidationError):
            WithholdingRule(**invalid_data)

        # Test tax rate above 100%
        invalid_data = valid_data.copy()
        invalid_data["tax_rate"] = Decimal("1.0001")
        with pytest.raises(ValidationError):
            WithholdingRule(**invalid_data)

        # Test precision validation (5,4)
        invalid_data = valid_data.copy()
        invalid_data["tax_rate"] = Decimal("0.12345")  # Too many decimal places
        with pytest.raises(ValidationError):
            WithholdingRule(**invalid_data)

    def test_income_threshold_validation(self):
        """Test income threshold validation rules"""
        valid_data = self._get_valid_data()

        # Test required income_threshold
        invalid_data = valid_data.copy()
        del invalid_data["income_threshold"]
        with pytest.raises(ValidationError):
            WithholdingRule(**invalid_data)

        # Test negative income threshold
        invalid_data = valid_data.copy()
        invalid_data["income_threshold"] = Decimal("-1.00")
        with pytest.raises(ValidationError):
            WithholdingRule(**invalid_data)

        # Test precision validation (12,2)
        invalid_data = valid_data.copy()
        invalid_data["income_threshold"] = Decimal("1000.123")  # Too many decimal places
        with pytest.raises(ValidationError):
            WithholdingRule(**invalid_data)

    def test_tax_threshold_validation(self):
        """Test tax threshold validation rules"""
        valid_data = self._get_valid_data()

        # Test required tax_threshold
        invalid_data = valid_data.copy()
        del invalid_data["tax_threshold"]
        with pytest.raises(ValidationError):
            WithholdingRule(**invalid_data)

        # Test negative tax threshold
        invalid_data = valid_data.copy()
        invalid_data["tax_threshold"] = Decimal("-1.00")
        with pytest.raises(ValidationError):
            WithholdingRule(**invalid_data)

        # Test precision validation (12,2)
        invalid_data = valid_data.copy()
        invalid_data["tax_threshold"] = Decimal("100.123")  # Too many decimal places
        with pytest.raises(ValidationError):
            WithholdingRule(**invalid_data)

    def test_unique_constraint_logic(self):
        """Test unique constraint for (rule_set_id, state_code, entity_type)"""
        # This would be tested at the database level, but we can test model logic
        valid_data = self._get_valid_data()

        rule = WithholdingRule(**valid_data)
        assert rule.rule_set_id == valid_data["rule_set_id"]
        assert rule.state_code == valid_data["state_code"]
        assert rule.entity_type == valid_data["entity_type"]
        # Unique constraint would be enforced by database

    def _get_valid_data(self):
        """Helper method to get valid test data"""
        return {
            "id": uuid4(),
            "rule_set_id": uuid4(),
            "state_code": USJurisdiction.CA,
            "entity_type": "Corporation",
            "tax_rate": Decimal("0.0525"),
            "income_threshold": Decimal("1000.00"),
            "tax_threshold": Decimal("100.00"),
            "created_at": datetime.now()
        }