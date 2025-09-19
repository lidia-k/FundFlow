"""
Unit tests for validation pipeline service
Task: T012 - Unit test validation pipeline service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from datetime import datetime
from src.services.validation_service import ValidationService
from src.models.validation_issue import ValidationIssue, IssueSeverity
from src.models.salt_rule_set import SaltRuleSet, RuleSetStatus
from src.models.withholding_rule import WithholdingRule
from src.models.composite_rule import CompositeRule


class TestValidationServiceLogic:
    """Test validation pipeline service business logic"""

    def test_validation_service_initialization(self):
        """Test ValidationService initialization"""
        # This should fail initially as ValidationService doesn't exist yet
        service = ValidationService()
        assert service is not None

    def test_validate_rule_set_draft_status(self):
        """Test rule set validation for draft status"""
        service = ValidationService()

        # Create mock rule set
        mock_rule_set = Mock(spec=SaltRuleSet)
        mock_rule_set.id = uuid4()
        mock_rule_set.status = RuleSetStatus.DRAFT
        mock_rule_set.year = 2025
        mock_rule_set.quarter = "Q1"

        # Should validate successfully for draft
        validation_result = service.validate_rule_set_status(mock_rule_set)
        assert validation_result.is_valid is True
        assert len(validation_result.issues) == 0

    def test_validate_rule_set_active_status_with_errors(self):
        """Test rule set validation preventing publication with errors"""
        service = ValidationService()

        # Create mock rule set with validation errors
        mock_rule_set = Mock(spec=SaltRuleSet)
        mock_rule_set.id = uuid4()
        mock_rule_set.status = RuleSetStatus.DRAFT

        # Mock validation issues with errors
        mock_error = Mock(spec=ValidationIssue)
        mock_error.severity = IssueSeverity.ERROR
        mock_error.error_code = "INVALID_STATE"

        mock_warning = Mock(spec=ValidationIssue)
        mock_warning.severity = IssueSeverity.WARNING
        mock_warning.error_code = "DUPLICATE_RULE"

        with patch.object(service, 'get_validation_issues', return_value=[mock_error, mock_warning]):
            validation_result = service.validate_for_publication(mock_rule_set)

        assert validation_result.can_publish is False
        assert validation_result.error_count == 1
        assert validation_result.warning_count == 1
        assert "Cannot publish with validation errors" in validation_result.message

    def test_validate_rule_set_active_status_warnings_only(self):
        """Test rule set validation allowing publication with warnings only"""
        service = ValidationService()

        # Create mock rule set with warnings only
        mock_rule_set = Mock(spec=SaltRuleSet)
        mock_rule_set.id = uuid4()
        mock_rule_set.status = RuleSetStatus.DRAFT

        # Mock validation issues with warnings only
        mock_warning1 = Mock(spec=ValidationIssue)
        mock_warning1.severity = IssueSeverity.WARNING
        mock_warning1.error_code = "POTENTIAL_DUPLICATE"

        mock_warning2 = Mock(spec=ValidationIssue)
        mock_warning2.severity = IssueSeverity.WARNING
        mock_warning2.error_code = "UNUSUAL_RATE"

        with patch.object(service, 'get_validation_issues', return_value=[mock_warning1, mock_warning2]):
            validation_result = service.validate_for_publication(mock_rule_set)

        assert validation_result.can_publish is True
        assert validation_result.error_count == 0
        assert validation_result.warning_count == 2
        assert "Ready for publication" in validation_result.message

    def test_validate_withholding_rules_completeness(self):
        """Test validation of withholding rules completeness"""
        service = ValidationService()

        # Create mock withholding rules - incomplete set
        mock_rules = [
            Mock(spec=WithholdingRule, state_code="CA", entity_type="Corporation"),
            Mock(spec=WithholdingRule, state_code="CA", entity_type="Partnership"),
            # Missing NY rules
        ]

        mock_rule_set = Mock(spec=SaltRuleSet)
        mock_rule_set.id = uuid4()

        with patch.object(service, 'get_withholding_rules', return_value=mock_rules):
            validation_result = service.validate_rules_completeness(mock_rule_set)

        assert validation_result.is_complete is False
        assert len(validation_result.missing_combinations) > 0
        assert any("NY" in combo for combo in validation_result.missing_combinations)

    def test_validate_composite_rules_completeness(self):
        """Test validation of composite rules completeness"""
        service = ValidationService()

        # Create complete set of composite rules
        expected_states = ["CA", "NY", "TX", "FL"]
        expected_entities = ["Corporation", "Partnership", "Individual"]

        mock_rules = []
        for state in expected_states:
            for entity in expected_entities:
                mock_rule = Mock(spec=CompositeRule)
                mock_rule.state_code = state
                mock_rule.entity_type = entity
                mock_rules.append(mock_rule)

        mock_rule_set = Mock(spec=SaltRuleSet)
        mock_rule_set.id = uuid4()

        with patch.object(service, 'get_composite_rules', return_value=mock_rules):
            validation_result = service.validate_rules_completeness(mock_rule_set)

        assert validation_result.is_complete is True
        assert len(validation_result.missing_combinations) == 0

    def test_validate_rule_consistency(self):
        """Test validation of rule consistency between withholding and composite"""
        service = ValidationService()

        # Create matching withholding and composite rules
        mock_withholding = Mock(spec=WithholdingRule)
        mock_withholding.state_code = "CA"
        mock_withholding.entity_type = "Corporation"
        mock_withholding.tax_rate = 0.0525

        mock_composite = Mock(spec=CompositeRule)
        mock_composite.state_code = "CA"
        mock_composite.entity_type = "Corporation"
        mock_composite.tax_rate = 0.0625

        mock_rule_set = Mock(spec=SaltRuleSet)
        mock_rule_set.id = uuid4()

        with patch.object(service, 'get_withholding_rules', return_value=[mock_withholding]):
            with patch.object(service, 'get_composite_rules', return_value=[mock_composite]):
                validation_result = service.validate_rule_consistency(mock_rule_set)

        assert validation_result.is_consistent is True
        assert len(validation_result.inconsistencies) == 0

    def test_validate_rule_inconsistency_missing_composite(self):
        """Test validation catches missing composite rules"""
        service = ValidationService()

        # Create withholding rule without matching composite
        mock_withholding = Mock(spec=WithholdingRule)
        mock_withholding.state_code = "CA"
        mock_withholding.entity_type = "Corporation"

        mock_rule_set = Mock(spec=SaltRuleSet)
        mock_rule_set.id = uuid4()

        with patch.object(service, 'get_withholding_rules', return_value=[mock_withholding]):
            with patch.object(service, 'get_composite_rules', return_value=[]):
                validation_result = service.validate_rule_consistency(mock_rule_set)

        assert validation_result.is_consistent is False
        assert len(validation_result.inconsistencies) > 0
        assert any("missing composite" in inc.lower() for inc in validation_result.inconsistencies)

    def test_validate_rate_reasonableness(self):
        """Test validation of rate reasonableness checks"""
        service = ValidationService()

        # Create rules with reasonable rates
        mock_withholding = Mock(spec=WithholdingRule)
        mock_withholding.state_code = "CA"
        mock_withholding.entity_type = "Corporation"
        mock_withholding.tax_rate = 0.0525  # 5.25% - reasonable
        mock_withholding.income_threshold = 1000.00
        mock_withholding.tax_threshold = 100.00

        mock_rule_set = Mock(spec=SaltRuleSet)
        mock_rule_set.id = uuid4()

        with patch.object(service, 'get_withholding_rules', return_value=[mock_withholding]):
            validation_result = service.validate_rate_reasonableness(mock_rule_set)

        assert validation_result.all_reasonable is True
        assert len(validation_result.unreasonable_rates) == 0

    def test_validate_rate_unreasonableness_high_rate(self):
        """Test validation catches unreasonably high rates"""
        service = ValidationService()

        # Create rule with unreasonably high rate
        mock_withholding = Mock(spec=WithholdingRule)
        mock_withholding.state_code = "CA"
        mock_withholding.entity_type = "Corporation"
        mock_withholding.tax_rate = 0.25  # 25% - unreasonably high
        mock_withholding.income_threshold = 1000.00
        mock_withholding.tax_threshold = 100.00

        mock_rule_set = Mock(spec=SaltRuleSet)
        mock_rule_set.id = uuid4()

        with patch.object(service, 'get_withholding_rules', return_value=[mock_withholding]):
            validation_result = service.validate_rate_reasonableness(mock_rule_set)

        assert validation_result.all_reasonable is False
        assert len(validation_result.unreasonable_rates) > 0
        assert any(rate.tax_rate > 0.20 for rate in validation_result.unreasonable_rates)

    def test_run_full_validation_pipeline(self):
        """Test complete validation pipeline execution"""
        service = ValidationService()

        mock_rule_set = Mock(spec=SaltRuleSet)
        mock_rule_set.id = uuid4()
        mock_rule_set.status = RuleSetStatus.DRAFT

        # Mock all validation steps
        with patch.object(service, 'validate_rule_set_status', return_value=Mock(is_valid=True, issues=[])):
            with patch.object(service, 'validate_rules_completeness', return_value=Mock(is_complete=True, missing_combinations=[])):
                with patch.object(service, 'validate_rule_consistency', return_value=Mock(is_consistent=True, inconsistencies=[])):
                    with patch.object(service, 'validate_rate_reasonableness', return_value=Mock(all_reasonable=True, unreasonable_rates=[])):
                        validation_result = service.run_full_validation(mock_rule_set)

        assert validation_result.overall_status == "VALID"
        assert validation_result.total_issues == 0
        assert validation_result.can_publish is True

    def test_run_full_validation_pipeline_with_failures(self):
        """Test validation pipeline with multiple validation failures"""
        service = ValidationService()

        mock_rule_set = Mock(spec=SaltRuleSet)
        mock_rule_set.id = uuid4()
        mock_rule_set.status = RuleSetStatus.DRAFT

        # Mock validation failures
        mock_error = Mock(spec=ValidationIssue)
        mock_error.severity = IssueSeverity.ERROR

        with patch.object(service, 'validate_rule_set_status', return_value=Mock(is_valid=False, issues=[mock_error])):
            with patch.object(service, 'validate_rules_completeness', return_value=Mock(is_complete=False, missing_combinations=["CA+Individual"])):
                with patch.object(service, 'validate_rule_consistency', return_value=Mock(is_consistent=False, inconsistencies=["Rate mismatch"])):
                    with patch.object(service, 'validate_rate_reasonableness', return_value=Mock(all_reasonable=False, unreasonable_rates=[mock_withholding])):
                        validation_result = service.run_full_validation(mock_rule_set)

        assert validation_result.overall_status == "INVALID"
        assert validation_result.total_issues > 0
        assert validation_result.can_publish is False

    def test_generate_validation_summary(self):
        """Test validation summary generation"""
        service = ValidationService()

        mock_rule_set = Mock(spec=SaltRuleSet)
        mock_rule_set.id = uuid4()

        # Mock validation issues
        mock_issues = [
            Mock(spec=ValidationIssue, severity=IssueSeverity.ERROR, error_code="INVALID_STATE"),
            Mock(spec=ValidationIssue, severity=IssueSeverity.ERROR, error_code="MISSING_FIELD"),
            Mock(spec=ValidationIssue, severity=IssueSeverity.WARNING, error_code="UNUSUAL_RATE"),
            Mock(spec=ValidationIssue, severity=IssueSeverity.WARNING, error_code="POTENTIAL_DUPLICATE"),
        ]

        with patch.object(service, 'get_validation_issues', return_value=mock_issues):
            summary = service.generate_validation_summary(mock_rule_set)

        assert summary.total_issues == 4
        assert summary.error_count == 2
        assert summary.warning_count == 2
        assert summary.rules_processed["withholding"] >= 0
        assert summary.rules_processed["composite"] >= 0