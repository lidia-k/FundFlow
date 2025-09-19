"""
Unit tests for StateEntityTaxRuleResolved model validation
Task: T010 - Unit test StateEntityTaxRuleResolved model
"""
import pytest
from uuid import UUID, uuid4
from datetime import datetime, date
from decimal import Decimal
from pydantic import ValidationError
from src.models.resolved_rule import StateEntityTaxRuleResolved
from src.models.enums import USJurisdiction


class TestStateEntityTaxRuleResolvedValidation:
    """Test StateEntityTaxRuleResolved model validation rules"""

    def test_valid_resolved_rule_creation(self):
        """Test creating a valid StateEntityTaxRuleResolved instance"""
        valid_data = {
            "id": uuid4(),
            "rule_set_id": uuid4(),
            "state_code": USJurisdiction.CA,
            "entity_type": "Corporation",
            "withholding_rate": Decimal("0.0525"),
            "withholding_income_threshold": Decimal("1000.00"),
            "withholding_tax_threshold": Decimal("100.00"),
            "composite_rate": Decimal("0.0625"),
            "composite_income_threshold": Decimal("1000.00"),
            "composite_mandatory_filing": True,
            "composite_min_tax": Decimal("25.00"),
            "composite_max_tax": Decimal("10000.00"),
            "effective_date": date(2025, 1, 1),
            "expiration_date": date(2025, 12, 31),
            "created_at": datetime.now(),
            "source_withholding_rule_id": uuid4(),
            "source_composite_rule_id": uuid4()
        }

        # This should fail initially as StateEntityTaxRuleResolved model doesn't exist yet
        resolved_rule = StateEntityTaxRuleResolved(**valid_data)
        assert resolved_rule.state_code == USJurisdiction.CA
        assert resolved_rule.entity_type == "Corporation"
        assert resolved_rule.withholding_rate == Decimal("0.0525")
        assert resolved_rule.composite_rate == Decimal("0.0625")
        assert isinstance(resolved_rule.id, UUID)

    def test_state_code_validation(self):
        """Test state code validation rules"""
        valid_data = self._get_valid_data()

        # Test required state_code
        invalid_data = valid_data.copy()
        del invalid_data["state_code"]
        with pytest.raises(ValidationError):
            StateEntityTaxRuleResolved(**invalid_data)

        # Test invalid state code
        invalid_data = valid_data.copy()
        invalid_data["state_code"] = "ZZ"
        with pytest.raises(ValidationError):
            StateEntityTaxRuleResolved(**invalid_data)

    def test_entity_type_validation(self):
        """Test entity type validation rules"""
        valid_data = self._get_valid_data()

        # Test required entity_type
        invalid_data = valid_data.copy()
        del invalid_data["entity_type"]
        with pytest.raises(ValidationError):
            StateEntityTaxRuleResolved(**invalid_data)

        # Test valid entity types
        valid_types = ["Corporation", "Partnership", "Individual", "Trust", "S Corporation", "Exempt Org", "IRA"]
        for entity_type in valid_types:
            test_data = valid_data.copy()
            test_data["entity_type"] = entity_type
            rule = StateEntityTaxRuleResolved(**test_data)
            assert rule.entity_type == entity_type

    def test_withholding_fields_validation(self):
        """Test withholding fields validation rules"""
        valid_data = self._get_valid_data()

        # Test required withholding fields
        required_fields = ["withholding_rate", "withholding_income_threshold", "withholding_tax_threshold"]
        for field in required_fields:
            invalid_data = valid_data.copy()
            del invalid_data[field]
            with pytest.raises(ValidationError):
                StateEntityTaxRuleResolved(**invalid_data)

        # Test negative rates/thresholds
        invalid_data = valid_data.copy()
        invalid_data["withholding_rate"] = Decimal("-0.01")
        with pytest.raises(ValidationError):
            StateEntityTaxRuleResolved(**invalid_data)

        # Test rate above 100%
        invalid_data = valid_data.copy()
        invalid_data["withholding_rate"] = Decimal("1.0001")
        with pytest.raises(ValidationError):
            StateEntityTaxRuleResolved(**invalid_data)

    def test_composite_fields_validation(self):
        """Test composite fields validation rules"""
        valid_data = self._get_valid_data()

        # Test required composite fields
        required_fields = ["composite_rate", "composite_income_threshold", "composite_mandatory_filing"]
        for field in required_fields:
            invalid_data = valid_data.copy()
            del invalid_data[field]
            with pytest.raises(ValidationError):
                StateEntityTaxRuleResolved(**invalid_data)

        # Test negative rates/thresholds
        invalid_data = valid_data.copy()
        invalid_data["composite_rate"] = Decimal("-0.01")
        with pytest.raises(ValidationError):
            StateEntityTaxRuleResolved(**invalid_data)

        # Test rate above 100%
        invalid_data = valid_data.copy()
        invalid_data["composite_rate"] = Decimal("1.0001")
        with pytest.raises(ValidationError):
            StateEntityTaxRuleResolved(**invalid_data)

    def test_composite_min_max_tax_validation(self):
        """Test composite min/max tax validation rules"""
        valid_data = self._get_valid_data()

        # Test optional composite_min_tax
        test_data = valid_data.copy()
        del test_data["composite_min_tax"]
        rule = StateEntityTaxRuleResolved(**test_data)
        assert rule.composite_min_tax is None

        # Test optional composite_max_tax
        test_data = valid_data.copy()
        del test_data["composite_max_tax"]
        rule = StateEntityTaxRuleResolved(**test_data)
        assert rule.composite_max_tax is None

        # Test negative min tax
        invalid_data = valid_data.copy()
        invalid_data["composite_min_tax"] = Decimal("-1.00")
        with pytest.raises(ValidationError):
            StateEntityTaxRuleResolved(**invalid_data)

        # Test max < min relationship
        invalid_data = valid_data.copy()
        invalid_data["composite_min_tax"] = Decimal("100.00")
        invalid_data["composite_max_tax"] = Decimal("25.00")
        with pytest.raises(ValidationError):
            StateEntityTaxRuleResolved(**invalid_data)

    def test_effective_date_validation(self):
        """Test effective date validation rules"""
        valid_data = self._get_valid_data()

        # Test required effective_date
        invalid_data = valid_data.copy()
        del invalid_data["effective_date"]
        with pytest.raises(ValidationError):
            StateEntityTaxRuleResolved(**invalid_data)

        # Test optional expiration_date
        test_data = valid_data.copy()
        del test_data["expiration_date"]
        rule = StateEntityTaxRuleResolved(**test_data)
        assert rule.expiration_date is None

        # Test expiration before effective date
        invalid_data = valid_data.copy()
        invalid_data["effective_date"] = date(2025, 12, 31)
        invalid_data["expiration_date"] = date(2025, 1, 1)
        with pytest.raises(ValidationError):
            StateEntityTaxRuleResolved(**invalid_data)

    def test_source_rule_ids_validation(self):
        """Test source rule IDs validation rules"""
        valid_data = self._get_valid_data()

        # Test required source_withholding_rule_id
        invalid_data = valid_data.copy()
        del invalid_data["source_withholding_rule_id"]
        with pytest.raises(ValidationError):
            StateEntityTaxRuleResolved(**invalid_data)

        # Test required source_composite_rule_id
        invalid_data = valid_data.copy()
        del invalid_data["source_composite_rule_id"]
        with pytest.raises(ValidationError):
            StateEntityTaxRuleResolved(**invalid_data)

        # Test valid UUIDs
        withholding_id = uuid4()
        composite_id = uuid4()
        test_data = valid_data.copy()
        test_data["source_withholding_rule_id"] = withholding_id
        test_data["source_composite_rule_id"] = composite_id
        rule = StateEntityTaxRuleResolved(**test_data)
        assert rule.source_withholding_rule_id == withholding_id
        assert rule.source_composite_rule_id == composite_id

    def test_unique_constraint_logic(self):
        """Test unique constraint for (rule_set_id, state_code, entity_type)"""
        # This would be tested at the database level, but we can test model logic
        valid_data = self._get_valid_data()

        rule = StateEntityTaxRuleResolved(**valid_data)
        assert rule.rule_set_id == valid_data["rule_set_id"]
        assert rule.state_code == valid_data["state_code"]
        assert rule.entity_type == valid_data["entity_type"]
        # Unique constraint would be enforced by database

    def test_decimal_precision_validation(self):
        """Test decimal precision validation for all rate and amount fields"""
        valid_data = self._get_valid_data()

        # Test rate precision (5,4)
        rate_fields = ["withholding_rate", "composite_rate"]
        for field in rate_fields:
            invalid_data = valid_data.copy()
            invalid_data[field] = Decimal("0.12345")  # Too many decimal places
            with pytest.raises(ValidationError):
                StateEntityTaxRuleResolved(**invalid_data)

        # Test amount precision (12,2)
        amount_fields = ["withholding_income_threshold", "withholding_tax_threshold",
                        "composite_income_threshold", "composite_min_tax", "composite_max_tax"]
        for field in amount_fields:
            if field in valid_data:  # Some are optional
                invalid_data = valid_data.copy()
                invalid_data[field] = Decimal("1000.123")  # Too many decimal places
                with pytest.raises(ValidationError):
                    StateEntityTaxRuleResolved(**invalid_data)

    def _get_valid_data(self):
        """Helper method to get valid test data"""
        return {
            "id": uuid4(),
            "rule_set_id": uuid4(),
            "state_code": USJurisdiction.CA,
            "entity_type": "Corporation",
            "withholding_rate": Decimal("0.0525"),
            "withholding_income_threshold": Decimal("1000.00"),
            "withholding_tax_threshold": Decimal("100.00"),
            "composite_rate": Decimal("0.0625"),
            "composite_income_threshold": Decimal("1000.00"),
            "composite_mandatory_filing": True,
            "composite_min_tax": Decimal("25.00"),
            "composite_max_tax": Decimal("10000.00"),
            "effective_date": date(2025, 1, 1),
            "expiration_date": date(2025, 12, 31),
            "created_at": datetime.now(),
            "source_withholding_rule_id": uuid4(),
            "source_composite_rule_id": uuid4()
        }