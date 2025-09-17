"""
Unit tests for CompositeRule model validation
Task: T008 - Unit test CompositeRule model validation
"""
import pytest
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from pydantic import ValidationError
from src.models.composite_rule import CompositeRule
from src.models.enums import USJurisdiction


class TestCompositeRuleValidation:
    """Test CompositeRule model validation rules"""

    def test_valid_composite_rule_creation(self):
        """Test creating a valid CompositeRule instance"""
        valid_data = {
            "id": uuid4(),
            "rule_set_id": uuid4(),
            "state_code": USJurisdiction.NY,
            "entity_type": "Partnership",
            "tax_rate": Decimal("0.0625"),
            "income_threshold": Decimal("1000.00"),
            "mandatory_filing": True,
            "min_tax_amount": Decimal("25.00"),
            "max_tax_amount": Decimal("10000.00"),
            "created_at": datetime.now()
        }

        # This should fail initially as CompositeRule model doesn't exist yet
        rule = CompositeRule(**valid_data)
        assert rule.state_code == USJurisdiction.NY
        assert rule.entity_type == "Partnership"
        assert rule.tax_rate == Decimal("0.0625")
        assert rule.mandatory_filing is True
        assert isinstance(rule.id, UUID)

    def test_state_code_validation(self):
        """Test state code validation rules"""
        valid_data = self._get_valid_data()

        # Test required state_code
        invalid_data = valid_data.copy()
        del invalid_data["state_code"]
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

        # Test invalid state code
        invalid_data = valid_data.copy()
        invalid_data["state_code"] = "ZZ"
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

    def test_entity_type_validation(self):
        """Test entity type validation rules"""
        valid_data = self._get_valid_data()

        # Test required entity_type
        invalid_data = valid_data.copy()
        del invalid_data["entity_type"]
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

        # Test invalid entity type
        invalid_data = valid_data.copy()
        invalid_data["entity_type"] = "InvalidType"
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

        # Test valid entity types
        valid_types = ["Corporation", "Partnership", "Individual", "Trust", "S Corporation", "Exempt Org", "IRA"]
        for entity_type in valid_types:
            test_data = valid_data.copy()
            test_data["entity_type"] = entity_type
            rule = CompositeRule(**test_data)
            assert rule.entity_type == entity_type

    def test_tax_rate_validation(self):
        """Test tax rate validation rules"""
        valid_data = self._get_valid_data()

        # Test required tax_rate
        invalid_data = valid_data.copy()
        del invalid_data["tax_rate"]
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

        # Test negative tax rate
        invalid_data = valid_data.copy()
        invalid_data["tax_rate"] = Decimal("-0.01")
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

        # Test tax rate above 100%
        invalid_data = valid_data.copy()
        invalid_data["tax_rate"] = Decimal("1.0001")
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

        # Test precision validation (5,4)
        invalid_data = valid_data.copy()
        invalid_data["tax_rate"] = Decimal("0.12345")  # Too many decimal places
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

    def test_income_threshold_validation(self):
        """Test income threshold validation rules"""
        valid_data = self._get_valid_data()

        # Test required income_threshold
        invalid_data = valid_data.copy()
        del invalid_data["income_threshold"]
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

        # Test negative income threshold
        invalid_data = valid_data.copy()
        invalid_data["income_threshold"] = Decimal("-1.00")
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

        # Test precision validation (12,2)
        invalid_data = valid_data.copy()
        invalid_data["income_threshold"] = Decimal("1000.123")  # Too many decimal places
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

    def test_mandatory_filing_validation(self):
        """Test mandatory filing validation rules"""
        valid_data = self._get_valid_data()

        # Test required mandatory_filing
        invalid_data = valid_data.copy()
        del invalid_data["mandatory_filing"]
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

        # Test boolean values
        test_data = valid_data.copy()
        test_data["mandatory_filing"] = False
        rule = CompositeRule(**test_data)
        assert rule.mandatory_filing is False

    def test_min_tax_amount_validation(self):
        """Test min tax amount validation rules"""
        valid_data = self._get_valid_data()

        # Test optional min_tax_amount
        test_data = valid_data.copy()
        del test_data["min_tax_amount"]
        rule = CompositeRule(**test_data)
        assert rule.min_tax_amount is None

        # Test negative min tax amount
        invalid_data = valid_data.copy()
        invalid_data["min_tax_amount"] = Decimal("-1.00")
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

        # Test precision validation (12,2)
        invalid_data = valid_data.copy()
        invalid_data["min_tax_amount"] = Decimal("25.123")  # Too many decimal places
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

    def test_max_tax_amount_validation(self):
        """Test max tax amount validation rules"""
        valid_data = self._get_valid_data()

        # Test optional max_tax_amount
        test_data = valid_data.copy()
        del test_data["max_tax_amount"]
        rule = CompositeRule(**test_data)
        assert rule.max_tax_amount is None

        # Test negative max tax amount
        invalid_data = valid_data.copy()
        invalid_data["max_tax_amount"] = Decimal("-1.00")
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

        # Test precision validation (12,2)
        invalid_data = valid_data.copy()
        invalid_data["max_tax_amount"] = Decimal("10000.123")  # Too many decimal places
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

    def test_min_max_tax_amount_relationship(self):
        """Test that max_tax_amount >= min_tax_amount when both present"""
        valid_data = self._get_valid_data()

        # Test valid relationship
        valid_data["min_tax_amount"] = Decimal("25.00")
        valid_data["max_tax_amount"] = Decimal("100.00")
        rule = CompositeRule(**valid_data)
        assert rule.min_tax_amount <= rule.max_tax_amount

        # Test invalid relationship (max < min)
        invalid_data = valid_data.copy()
        invalid_data["min_tax_amount"] = Decimal("100.00")
        invalid_data["max_tax_amount"] = Decimal("25.00")
        with pytest.raises(ValidationError):
            CompositeRule(**invalid_data)

    def test_unique_constraint_logic(self):
        """Test unique constraint for (rule_set_id, state_code, entity_type)"""
        # This would be tested at the database level, but we can test model logic
        valid_data = self._get_valid_data()

        rule = CompositeRule(**valid_data)
        assert rule.rule_set_id == valid_data["rule_set_id"]
        assert rule.state_code == valid_data["state_code"]
        assert rule.entity_type == valid_data["entity_type"]
        # Unique constraint would be enforced by database

    def _get_valid_data(self):
        """Helper method to get valid test data"""
        return {
            "id": uuid4(),
            "rule_set_id": uuid4(),
            "state_code": USJurisdiction.NY,
            "entity_type": "Partnership",
            "tax_rate": Decimal("0.0625"),
            "income_threshold": Decimal("1000.00"),
            "mandatory_filing": True,
            "min_tax_amount": Decimal("25.00"),
            "max_tax_amount": Decimal("10000.00"),
            "created_at": datetime.now()
        }