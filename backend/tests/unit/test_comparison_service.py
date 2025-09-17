"""
Unit tests for rule comparison service logic
Task: T014 - Unit test rule comparison service logic
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from decimal import Decimal
from src.services.comparison_service import ComparisonService
from src.models.salt_rule_set import SaltRuleSet, RuleSetStatus
from src.models.withholding_rule import WithholdingRule
from src.models.composite_rule import CompositeRule
from src.models.enums import USJurisdiction


class TestComparisonServiceLogic:
    """Test rule comparison service business logic"""

    def test_comparison_service_initialization(self):
        """Test ComparisonService initialization"""
        # This should fail initially as ComparisonService doesn't exist yet
        service = ComparisonService()
        assert service is not None

    def test_compare_rule_sets_no_changes(self):
        """Test comparison between identical rule sets"""
        service = ComparisonService()

        # Create identical mock rule sets
        draft_rule_set = self._create_mock_rule_set("draft", RuleSetStatus.DRAFT)
        active_rule_set = self._create_mock_rule_set("active", RuleSetStatus.ACTIVE)

        # Create identical rules
        draft_rules = self._create_mock_rules("draft")
        active_rules = self._create_mock_rules("active")

        with patch.object(service, 'get_withholding_rules') as mock_get_withholding:
            with patch.object(service, 'get_composite_rules') as mock_get_composite:
                # Return identical rules for both rule sets
                mock_get_withholding.side_effect = lambda rs: draft_rules["withholding"] if rs.id == draft_rule_set.id else active_rules["withholding"]
                mock_get_composite.side_effect = lambda rs: draft_rules["composite"] if rs.id == draft_rule_set.id else active_rules["composite"]

                comparison_result = service.compare_rule_sets(draft_rule_set, active_rule_set)

        assert comparison_result.rules_added == 0
        assert comparison_result.rules_modified == 0
        assert comparison_result.rules_removed == 0
        assert comparison_result.fields_changed == 0
        assert len(comparison_result.changes.added) == 0
        assert len(comparison_result.changes.modified) == 0
        assert len(comparison_result.changes.removed) == 0

    def test_compare_rule_sets_with_additions(self):
        """Test comparison with new rules added"""
        service = ComparisonService()

        draft_rule_set = self._create_mock_rule_set("draft", RuleSetStatus.DRAFT)
        active_rule_set = self._create_mock_rule_set("active", RuleSetStatus.ACTIVE)

        # Active has fewer rules than draft
        active_rules = self._create_mock_rules("active")
        draft_rules = self._create_mock_rules("draft")

        # Add extra rule to draft
        extra_withholding = Mock(spec=WithholdingRule)
        extra_withholding.state_code = USJurisdiction.TX
        extra_withholding.entity_type = "Corporation"
        extra_withholding.tax_rate = Decimal("0.0000")
        draft_rules["withholding"].append(extra_withholding)

        with patch.object(service, 'get_withholding_rules') as mock_get_withholding:
            with patch.object(service, 'get_composite_rules') as mock_get_composite:
                mock_get_withholding.side_effect = lambda rs: draft_rules["withholding"] if rs.id == draft_rule_set.id else active_rules["withholding"]
                mock_get_composite.side_effect = lambda rs: draft_rules["composite"] if rs.id == draft_rule_set.id else active_rules["composite"]

                comparison_result = service.compare_rule_sets(draft_rule_set, active_rule_set)

        assert comparison_result.rules_added > 0
        assert len(comparison_result.changes.added) > 0
        assert any(change.state_code == "TX" for change in comparison_result.changes.added)

    def test_compare_rule_sets_with_modifications(self):
        """Test comparison with modified rules"""
        service = ComparisonService()

        draft_rule_set = self._create_mock_rule_set("draft", RuleSetStatus.DRAFT)
        active_rule_set = self._create_mock_rule_set("active", RuleSetStatus.ACTIVE)

        # Create rules with different rates
        active_withholding = Mock(spec=WithholdingRule)
        active_withholding.state_code = USJurisdiction.CA
        active_withholding.entity_type = "Corporation"
        active_withholding.tax_rate = Decimal("0.0525")
        active_withholding.income_threshold = Decimal("1000.00")
        active_withholding.tax_threshold = Decimal("100.00")

        draft_withholding = Mock(spec=WithholdingRule)
        draft_withholding.state_code = USJurisdiction.CA
        draft_withholding.entity_type = "Corporation"
        draft_withholding.tax_rate = Decimal("0.0575")  # Modified rate
        draft_withholding.income_threshold = Decimal("1000.00")
        draft_withholding.tax_threshold = Decimal("100.00")

        active_rules = {"withholding": [active_withholding], "composite": []}
        draft_rules = {"withholding": [draft_withholding], "composite": []}

        with patch.object(service, 'get_withholding_rules') as mock_get_withholding:
            with patch.object(service, 'get_composite_rules') as mock_get_composite:
                mock_get_withholding.side_effect = lambda rs: draft_rules["withholding"] if rs.id == draft_rule_set.id else active_rules["withholding"]
                mock_get_composite.side_effect = lambda rs: draft_rules["composite"] if rs.id == draft_rule_set.id else active_rules["composite"]

                comparison_result = service.compare_rule_sets(draft_rule_set, active_rule_set)

        assert comparison_result.rules_modified > 0
        assert comparison_result.fields_changed > 0
        assert len(comparison_result.changes.modified) > 0
        modified_change = comparison_result.changes.modified[0]
        assert any(field_change.field == "tax_rate" for field_change in modified_change.field_changes)

    def test_compare_rule_sets_with_removals(self):
        """Test comparison with removed rules"""
        service = ComparisonService()

        draft_rule_set = self._create_mock_rule_set("draft", RuleSetStatus.DRAFT)
        active_rule_set = self._create_mock_rule_set("active", RuleSetStatus.ACTIVE)

        # Active has more rules than draft (rules removed)
        active_rules = self._create_mock_rules("active")
        draft_rules = {"withholding": [], "composite": []}  # Empty draft

        with patch.object(service, 'get_withholding_rules') as mock_get_withholding:
            with patch.object(service, 'get_composite_rules') as mock_get_composite:
                mock_get_withholding.side_effect = lambda rs: draft_rules["withholding"] if rs.id == draft_rule_set.id else active_rules["withholding"]
                mock_get_composite.side_effect = lambda rs: draft_rules["composite"] if rs.id == draft_rule_set.id else active_rules["composite"]

                comparison_result = service.compare_rule_sets(draft_rule_set, active_rule_set)

        assert comparison_result.rules_removed > 0
        assert len(comparison_result.changes.removed) > 0

    def test_detect_field_changes_withholding_rule(self):
        """Test detection of specific field changes in withholding rules"""
        service = ComparisonService()

        old_rule = Mock(spec=WithholdingRule)
        old_rule.tax_rate = Decimal("0.0525")
        old_rule.income_threshold = Decimal("1000.00")
        old_rule.tax_threshold = Decimal("100.00")

        new_rule = Mock(spec=WithholdingRule)
        new_rule.tax_rate = Decimal("0.0575")  # Changed
        new_rule.income_threshold = Decimal("1500.00")  # Changed
        new_rule.tax_threshold = Decimal("100.00")  # Unchanged

        field_changes = service.detect_field_changes(old_rule, new_rule, "withholding")

        assert len(field_changes) == 2
        tax_rate_change = next((fc for fc in field_changes if fc.field == "tax_rate"), None)
        assert tax_rate_change is not None
        assert tax_rate_change.old_value == "0.0525"
        assert tax_rate_change.new_value == "0.0575"

        income_change = next((fc for fc in field_changes if fc.field == "income_threshold"), None)
        assert income_change is not None
        assert income_change.old_value == "1000.00"
        assert income_change.new_value == "1500.00"

    def test_detect_field_changes_composite_rule(self):
        """Test detection of specific field changes in composite rules"""
        service = ComparisonService()

        old_rule = Mock(spec=CompositeRule)
        old_rule.tax_rate = Decimal("0.0625")
        old_rule.income_threshold = Decimal("1000.00")
        old_rule.mandatory_filing = True
        old_rule.min_tax_amount = Decimal("25.00")
        old_rule.max_tax_amount = Decimal("10000.00")

        new_rule = Mock(spec=CompositeRule)
        new_rule.tax_rate = Decimal("0.0625")  # Unchanged
        new_rule.income_threshold = Decimal("1000.00")  # Unchanged
        new_rule.mandatory_filing = False  # Changed
        new_rule.min_tax_amount = Decimal("50.00")  # Changed
        new_rule.max_tax_amount = Decimal("10000.00")  # Unchanged

        field_changes = service.detect_field_changes(old_rule, new_rule, "composite")

        assert len(field_changes) == 2
        filing_change = next((fc for fc in field_changes if fc.field == "mandatory_filing"), None)
        assert filing_change is not None
        assert filing_change.old_value == "True"
        assert filing_change.new_value == "False"

        min_tax_change = next((fc for fc in field_changes if fc.field == "min_tax_amount"), None)
        assert min_tax_change is not None
        assert min_tax_change.old_value == "25.00"
        assert min_tax_change.new_value == "50.00"

    def test_generate_comparison_summary(self):
        """Test generation of comparison summary"""
        service = ComparisonService()

        mock_comparison_result = Mock()
        mock_comparison_result.rules_added = 5
        mock_comparison_result.rules_modified = 12
        mock_comparison_result.rules_removed = 0
        mock_comparison_result.fields_changed = 18

        summary = service.generate_comparison_summary(mock_comparison_result)

        assert summary.rules_added == 5
        assert summary.rules_modified == 12
        assert summary.rules_removed == 0
        assert summary.fields_changed == 18
        assert summary.total_changes == 17  # added + modified + removed

    def test_compare_with_no_active_rule_set(self):
        """Test comparison when no active rule set exists"""
        service = ComparisonService()

        draft_rule_set = self._create_mock_rule_set("draft", RuleSetStatus.DRAFT)
        draft_rules = self._create_mock_rules("draft")

        with patch.object(service, 'get_withholding_rules', return_value=draft_rules["withholding"]):
            with patch.object(service, 'get_composite_rules', return_value=draft_rules["composite"]):
                comparison_result = service.compare_rule_sets(draft_rule_set, None)

        # When no active rule set, everything in draft is considered "added"
        assert comparison_result.rules_added > 0
        assert comparison_result.rules_modified == 0
        assert comparison_result.rules_removed == 0
        assert len(comparison_result.changes.added) > 0

    def test_identify_rule_by_key(self):
        """Test rule identification by composite key"""
        service = ComparisonService()

        rules = [
            Mock(state_code=USJurisdiction.CA, entity_type="Corporation"),
            Mock(state_code=USJurisdiction.CA, entity_type="Partnership"),
            Mock(state_code=USJurisdiction.NY, entity_type="Corporation"),
        ]

        # Find existing rule
        found_rule = service.find_rule_by_key(rules, USJurisdiction.CA, "Partnership")
        assert found_rule is not None
        assert found_rule.entity_type == "Partnership"

        # Rule not found
        not_found = service.find_rule_by_key(rules, USJurisdiction.TX, "Corporation")
        assert not_found is None

    def _create_mock_rule_set(self, name_suffix, status):
        """Helper to create mock rule set"""
        mock_rule_set = Mock(spec=SaltRuleSet)
        mock_rule_set.id = uuid4()
        mock_rule_set.status = status
        mock_rule_set.year = 2025
        mock_rule_set.quarter = "Q1"
        return mock_rule_set

    def _create_mock_rules(self, name_suffix):
        """Helper to create mock rules"""
        withholding_rule = Mock(spec=WithholdingRule)
        withholding_rule.state_code = USJurisdiction.CA
        withholding_rule.entity_type = "Corporation"
        withholding_rule.tax_rate = Decimal("0.0525")
        withholding_rule.income_threshold = Decimal("1000.00")
        withholding_rule.tax_threshold = Decimal("100.00")

        composite_rule = Mock(spec=CompositeRule)
        composite_rule.state_code = USJurisdiction.CA
        composite_rule.entity_type = "Corporation"
        composite_rule.tax_rate = Decimal("0.0625")
        composite_rule.income_threshold = Decimal("1000.00")
        composite_rule.mandatory_filing = True

        return {
            "withholding": [withholding_rule],
            "composite": [composite_rule]
        }