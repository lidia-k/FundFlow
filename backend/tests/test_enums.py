"""Tests for enum models."""

import pytest
from src.models.enums import InvestorEntityType, USJurisdiction


class TestInvestorEntityType:
    """Test InvestorEntityType enum functionality."""

    def test_enum_has_display_value_and_coding(self):
        """Test that enum members have both display value and coding."""
        entity_type = InvestorEntityType.CORPORATION
        assert entity_type.value == "Corporation"
        assert entity_type.coding == "Corporation"

    def test_all_entity_types_have_coding(self):
        """Test that all entity types have coding values."""
        for entity_type in InvestorEntityType:
            assert hasattr(entity_type, "coding")
            assert entity_type.coding is not None
            assert isinstance(entity_type.coding, str)
            assert len(entity_type.coding) > 0

    def test_coding_mappings_match_expected_values(self):
        """Test specific coding mappings based on the provided table."""
        expected_mappings = {
            InvestorEntityType.CORPORATION: "Corporation",
            InvestorEntityType.LIMITED_PARTNERSHIP: "Partnership",
            InvestorEntityType.EXEMPT_ORGANIZATION: "Exempt Org",
            InvestorEntityType.LLC_TAXED_AS_PARTNERSHIP: "Partnership",
            InvestorEntityType.INDIVIDUAL: "Individual",
            InvestorEntityType.TRUST: "Trust",
            InvestorEntityType.S_CORPORATION: "S Corporation",
            InvestorEntityType.PARTNERSHIP: "Partnership",
            InvestorEntityType.JOINT_TENANCY_TENANCY_IN_COMMON: "Individual",
            InvestorEntityType.GOVERNMENT_BENEFIT_PLAN: "Exempt Org",
            InvestorEntityType.IRA_KEOGH: "IRA",
            InvestorEntityType.IRA: "IRA",
            InvestorEntityType.EXEMPT_ORGANIZATION_BENEFIT: "Exempt Org",
            InvestorEntityType.LLP: "Partnership",
            InvestorEntityType.BENEFIT_PLAN_INVESTOR_ERISA_TITLE_I: "Exempt Org",
            InvestorEntityType.GRANTOR_TRUST: "Individual",
            InvestorEntityType.LLC_TAXED_AS_CORPORATION: "Corporation",
            InvestorEntityType.LLC_TAXED_AS_PARTNERSHIP_ALT: "Partnership",
            InvestorEntityType.ESTATE: "Estate",
            InvestorEntityType.BENEFIT_PLAN_INVESTOR_PLAN_ASSETS: "Exempt Org",
        }

        for entity_type, expected_coding in expected_mappings.items():
            assert entity_type.coding == expected_coding, f"Expected {entity_type} to have coding '{expected_coding}', got '{entity_type.coding}'"

    def test_get_by_coding_success(self):
        """Test successful retrieval by coding value."""
        entity_type = InvestorEntityType.get_by_coding("Corporation")
        assert entity_type == InvestorEntityType.CORPORATION

        entity_type = InvestorEntityType.get_by_coding("Partnership")
        # Should return one of the partnership types
        assert entity_type.coding == "Partnership"

    def test_get_by_coding_not_found(self):
        """Test error when coding value not found."""
        with pytest.raises(ValueError, match="No entity type found for coding: NonExistent"):
            InvestorEntityType.get_by_coding("NonExistent")

    def test_get_all_codings(self):
        """Test getting all coding mappings."""
        codings = InvestorEntityType.get_all_codings()

        assert isinstance(codings, dict)
        assert len(codings) == len(InvestorEntityType)

        # Check specific mappings
        assert codings["Corporation"] == "Corporation"
        assert codings["Limited Partnership"] == "Partnership"
        assert codings["Individual"] == "Individual"

    def test_get_unique_codings(self):
        """Test getting unique coding values."""
        unique_codings = InvestorEntityType.get_unique_codings()

        assert isinstance(unique_codings, set)

        # Expected unique codings based on the table
        expected_unique = {
            "Corporation", "Partnership", "Exempt Org", "Individual",
            "Trust", "S Corporation", "IRA", "Estate"
        }

        assert unique_codings == expected_unique

    def test_coding_distribution(self):
        """Test the distribution of coding values."""
        coding_counts = {}
        for entity_type in InvestorEntityType:
            coding = entity_type.coding
            coding_counts[coding] = coding_counts.get(coding, 0) + 1

        # Based on the enum, Partnership should be the most common
        assert coding_counts["Partnership"] >= 5  # LLP, LIMITED_PARTNERSHIP, etc.
        assert coding_counts["Exempt Org"] >= 4   # Multiple benefit plan types
        assert coding_counts["Individual"] >= 2   # INDIVIDUAL, JOINT_TENANCY, GRANTOR_TRUST
        assert coding_counts["Corporation"] >= 2  # CORPORATION, LLC_TAXED_AS_CORPORATION

    def test_backward_compatibility(self):
        """Test that existing enum usage still works."""
        # Test that we can still access the display value
        assert str(InvestorEntityType.CORPORATION.value) == "Corporation"
        assert str(InvestorEntityType.LIMITED_PARTNERSHIP.value) == "Limited Partnership"

        # Test enum comparison
        assert InvestorEntityType.CORPORATION == InvestorEntityType.CORPORATION
        assert InvestorEntityType.CORPORATION != InvestorEntityType.PARTNERSHIP

        # Test iteration
        entity_types = list(InvestorEntityType)
        assert len(entity_types) == 20  # Total number of entity types


class TestUSJurisdiction:
    """Test USJurisdiction enum functionality."""

    def test_all_states_present(self):
        """Test that all 50 states + DC are present."""
        jurisdictions = list(USJurisdiction)
        assert len(jurisdictions) == 51  # 50 states + DC

    def test_specific_jurisdictions(self):
        """Test specific jurisdiction values."""
        assert USJurisdiction.CA.value == "CA"
        assert USJurisdiction.NY.value == "NY"
        assert USJurisdiction.TX.value == "TX"
        assert USJurisdiction.DC.value == "DC"

    def test_jurisdiction_values_are_two_chars(self):
        """Test that all jurisdiction values are 2-character codes."""
        for jurisdiction in USJurisdiction:
            assert len(jurisdiction.value) == 2
            assert jurisdiction.value.isupper()
