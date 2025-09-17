"""Multi-layer validation pipeline service for SALT rule sets."""

import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from decimal import Decimal
from sqlalchemy.orm import Session

from ..models.salt_rule_set import SaltRuleSet, RuleSetStatus
from ..models.withholding_rule import WithholdingRule
from ..models.composite_rule import CompositeRule
from ..models.validation_issue import ValidationIssue, IssueSeverity
from ..models.enums import USJurisdiction, InvestorEntityType

logger = logging.getLogger(__name__)


@dataclass
class ValidationStatusResult:
    """Result of rule set status validation."""
    is_valid: bool
    issues: List[ValidationIssue]
    message: Optional[str] = None


@dataclass
class ValidationCompletenessResult:
    """Result of rule completeness validation."""
    is_complete: bool
    missing_combinations: List[str]
    expected_combinations: int
    actual_combinations: int


@dataclass
class ValidationConsistencyResult:
    """Result of rule consistency validation."""
    is_consistent: bool
    inconsistencies: List[str]
    matched_pairs: int
    total_rules: int


@dataclass
class ValidationReasonablenessResult:
    """Result of rate reasonableness validation."""
    all_reasonable: bool
    unreasonable_rates: List[Dict]
    warnings: List[str]


@dataclass
class ValidationPublicationResult:
    """Result of publication readiness validation."""
    can_publish: bool
    error_count: int
    warning_count: int
    message: str
    blocking_issues: List[ValidationIssue]


@dataclass
class ValidationSummary:
    """Summary of validation results."""
    total_issues: int
    error_count: int
    warning_count: int
    rules_processed: Dict[str, int]
    validation_status: str


@dataclass
class FullValidationResult:
    """Result of complete validation pipeline."""
    overall_status: str  # VALID, INVALID, WARNING
    total_issues: int
    can_publish: bool
    status_result: ValidationStatusResult
    completeness_result: ValidationCompletenessResult
    consistency_result: ValidationConsistencyResult
    reasonableness_result: ValidationReasonablenessResult
    summary: ValidationSummary


class ValidationService:
    """Service for multi-layer validation of SALT rule sets."""

    # Rate reasonableness thresholds
    MAX_REASONABLE_RATE = Decimal('0.20')  # 20% max reasonable tax rate
    MIN_INCOME_THRESHOLD = Decimal('0.00')
    MAX_INCOME_THRESHOLD = Decimal('1000000.00')  # $1M max reasonable threshold

    def __init__(self, db: Session):
        self.db = db

    def get_validation_issues(self, rule_set: SaltRuleSet) -> List[ValidationIssue]:
        """Get all validation issues for a rule set."""
        return (self.db.query(ValidationIssue)
                .filter(ValidationIssue.rule_set_id == rule_set.id)
                .all())

    def get_withholding_rules(self, rule_set: SaltRuleSet) -> List[WithholdingRule]:
        """Get all withholding rules for a rule set."""
        return (self.db.query(WithholdingRule)
                .filter(WithholdingRule.rule_set_id == rule_set.id)
                .all())

    def get_composite_rules(self, rule_set: SaltRuleSet) -> List[CompositeRule]:
        """Get all composite rules for a rule set."""
        return (self.db.query(CompositeRule)
                .filter(CompositeRule.rule_set_id == rule_set.id)
                .all())

    def validate_rule_set_status(self, rule_set: SaltRuleSet) -> ValidationStatusResult:
        """Validate rule set status and basic metadata."""
        issues = []

        # Check if rule set is in valid status for validation
        if rule_set.status not in [RuleSetStatus.DRAFT, RuleSetStatus.ACTIVE]:
            issues.append(ValidationIssue(
                rule_set_id=rule_set.id,
                sheet_name="METADATA",
                row_number=0,
                error_code="INVALID_STATUS",
                severity=IssueSeverity.ERROR,
                message=f"Rule set status '{rule_set.status.value}' is not valid for processing",
                field_value=rule_set.status.value
            ))

        # Check year range
        if rule_set.year < 2020 or rule_set.year > 2030:
            issues.append(ValidationIssue(
                rule_set_id=rule_set.id,
                sheet_name="METADATA",
                row_number=0,
                error_code="INVALID_YEAR",
                severity=IssueSeverity.ERROR,
                message=f"Year {rule_set.year} is outside valid range (2020-2030)",
                field_value=str(rule_set.year)
            ))

        # Check if source file exists
        if not rule_set.source_file_id:
            issues.append(ValidationIssue(
                rule_set_id=rule_set.id,
                sheet_name="METADATA",
                row_number=0,
                error_code="MISSING_SOURCE_FILE",
                severity=IssueSeverity.ERROR,
                message="Rule set has no associated source file",
                field_value=None
            ))

        is_valid = len([i for i in issues if i.severity == IssueSeverity.ERROR]) == 0
        return ValidationStatusResult(
            is_valid=is_valid,
            issues=issues,
            message="Rule set status validation passed" if is_valid else "Rule set status validation failed"
        )

    def validate_rules_completeness(self, rule_set: SaltRuleSet) -> ValidationCompletenessResult:
        """Validate that we have complete rule coverage for all required state/entity combinations."""
        withholding_rules = self.get_withholding_rules(rule_set)
        composite_rules = self.get_composite_rules(rule_set)

        # Get all state/entity combinations from both rule types
        withholding_combinations = {(rule.state_code.value, rule.entity_type) for rule in withholding_rules}
        composite_combinations = {(rule.state_code.value, rule.entity_type) for rule in composite_rules}

        # Expected combinations (basic validation - we should have some coverage)
        all_states = {state.value for state in USJurisdiction}
        all_entities = InvestorEntityType.get_unique_codings()

        # Check for missing combinations in withholding rules
        missing_withholding = []
        for combination in composite_combinations:
            if combination not in withholding_combinations:
                missing_withholding.append(f"Withholding: {combination[0]}+{combination[1]}")

        # Check for missing combinations in composite rules
        missing_composite = []
        for combination in withholding_combinations:
            if combination not in composite_combinations:
                missing_composite.append(f"Composite: {combination[0]}+{combination[1]}")

        missing_combinations = missing_withholding + missing_composite

        # Calculate expected vs actual combinations
        expected_combinations = len(withholding_combinations.union(composite_combinations))
        actual_combinations = len(withholding_combinations.intersection(composite_combinations))

        is_complete = len(missing_combinations) == 0 and actual_combinations > 0

        return ValidationCompletenessResult(
            is_complete=is_complete,
            missing_combinations=missing_combinations,
            expected_combinations=expected_combinations,
            actual_combinations=actual_combinations
        )

    def validate_rule_consistency(self, rule_set: SaltRuleSet) -> ValidationConsistencyResult:
        """Validate consistency between withholding and composite rules."""
        withholding_rules = self.get_withholding_rules(rule_set)
        composite_rules = self.get_composite_rules(rule_set)

        # Create lookup maps
        withholding_map = {(rule.state_code.value, rule.entity_type): rule for rule in withholding_rules}
        composite_map = {(rule.state_code.value, rule.entity_type): rule for rule in composite_rules}

        inconsistencies = []
        matched_pairs = 0

        # Check for missing corresponding rules
        for key in withholding_map.keys():
            if key not in composite_map:
                inconsistencies.append(f"Missing composite rule for {key[0]}+{key[1]}")
            else:
                matched_pairs += 1

        for key in composite_map.keys():
            if key not in withholding_map:
                inconsistencies.append(f"Missing withholding rule for {key[0]}+{key[1]}")

        # Check for logical inconsistencies in matched pairs
        for key in withholding_map.keys():
            if key in composite_map:
                w_rule = withholding_map[key]
                c_rule = composite_map[key]

                # Income thresholds should be related (warning level)
                if w_rule.income_threshold != c_rule.income_threshold:
                    inconsistencies.append(
                        f"Income threshold mismatch for {key[0]}+{key[1]}: "
                        f"Withholding=${w_rule.income_threshold}, Composite=${c_rule.income_threshold}"
                    )

                # Composite rate should generally be >= withholding rate (warning level)
                if c_rule.tax_rate < w_rule.tax_rate:
                    inconsistencies.append(
                        f"Composite rate ({c_rule.tax_rate}) < Withholding rate ({w_rule.tax_rate}) "
                        f"for {key[0]}+{key[1]} - unusual but not necessarily wrong"
                    )

        is_consistent = len([inc for inc in inconsistencies if "Missing" in inc]) == 0
        total_rules = len(withholding_rules) + len(composite_rules)

        return ValidationConsistencyResult(
            is_consistent=is_consistent,
            inconsistencies=inconsistencies,
            matched_pairs=matched_pairs,
            total_rules=total_rules
        )

    def validate_rate_reasonableness(self, rule_set: SaltRuleSet) -> ValidationReasonablenessResult:
        """Validate that tax rates and thresholds are within reasonable ranges."""
        withholding_rules = self.get_withholding_rules(rule_set)
        composite_rules = self.get_composite_rules(rule_set)

        unreasonable_rates = []
        warnings = []

        # Check withholding rules
        for rule in withholding_rules:
            # Check tax rate
            if rule.tax_rate > self.MAX_REASONABLE_RATE:
                unreasonable_rates.append({
                    "rule_type": "withholding",
                    "state": rule.state_code.value,
                    "entity_type": rule.entity_type,
                    "tax_rate": rule.tax_rate,
                    "issue": f"Tax rate {rule.tax_rate} exceeds reasonable maximum {self.MAX_REASONABLE_RATE}"
                })

            # Check income threshold
            if rule.income_threshold < self.MIN_INCOME_THRESHOLD or rule.income_threshold > self.MAX_INCOME_THRESHOLD:
                warnings.append(
                    f"Unusual income threshold ${rule.income_threshold} for {rule.state_code.value}+{rule.entity_type}"
                )

            # Check tax threshold vs income threshold relationship
            if rule.tax_threshold > rule.income_threshold * rule.tax_rate:
                warnings.append(
                    f"Tax threshold ${rule.tax_threshold} > expected max ${rule.income_threshold * rule.tax_rate} "
                    f"for {rule.state_code.value}+{rule.entity_type}"
                )

        # Check composite rules
        for rule in composite_rules:
            # Check tax rate
            if rule.tax_rate > self.MAX_REASONABLE_RATE:
                unreasonable_rates.append({
                    "rule_type": "composite",
                    "state": rule.state_code.value,
                    "entity_type": rule.entity_type,
                    "tax_rate": rule.tax_rate,
                    "issue": f"Tax rate {rule.tax_rate} exceeds reasonable maximum {self.MAX_REASONABLE_RATE}"
                })

            # Check min/max tax amount relationship
            if rule.min_tax_amount and rule.max_tax_amount:
                if rule.min_tax_amount > rule.max_tax_amount:
                    warnings.append(
                        f"Min tax amount ${rule.min_tax_amount} > Max tax amount ${rule.max_tax_amount} "
                        f"for {rule.state_code.value}+{rule.entity_type}"
                    )

        all_reasonable = len(unreasonable_rates) == 0

        return ValidationReasonablenessResult(
            all_reasonable=all_reasonable,
            unreasonable_rates=unreasonable_rates,
            warnings=warnings
        )

    def validate_for_publication(self, rule_set: SaltRuleSet) -> ValidationPublicationResult:
        """Validate if rule set is ready for publication."""
        validation_issues = self.get_validation_issues(rule_set)

        error_issues = [issue for issue in validation_issues if issue.severity == IssueSeverity.ERROR]
        warning_issues = [issue for issue in validation_issues if issue.severity == IssueSeverity.WARNING]

        error_count = len(error_issues)
        warning_count = len(warning_issues)
        can_publish = error_count == 0

        if can_publish:
            if warning_count > 0:
                message = f"Ready for publication with {warning_count} warnings"
            else:
                message = "Ready for publication"
        else:
            message = f"Cannot publish with {error_count} validation errors"

        return ValidationPublicationResult(
            can_publish=can_publish,
            error_count=error_count,
            warning_count=warning_count,
            message=message,
            blocking_issues=error_issues
        )

    def generate_validation_summary(self, rule_set: SaltRuleSet) -> ValidationSummary:
        """Generate validation summary for rule set."""
        validation_issues = self.get_validation_issues(rule_set)
        withholding_rules = self.get_withholding_rules(rule_set)
        composite_rules = self.get_composite_rules(rule_set)

        error_count = len([issue for issue in validation_issues if issue.severity == IssueSeverity.ERROR])
        warning_count = len([issue for issue in validation_issues if issue.severity == IssueSeverity.WARNING])

        # Determine overall validation status
        if error_count > 0:
            validation_status = "INVALID"
        elif warning_count > 0:
            validation_status = "WARNING"
        else:
            validation_status = "VALID"

        return ValidationSummary(
            total_issues=len(validation_issues),
            error_count=error_count,
            warning_count=warning_count,
            rules_processed={
                "withholding": len(withholding_rules),
                "composite": len(composite_rules)
            },
            validation_status=validation_status
        )

    def run_full_validation(self, rule_set: SaltRuleSet) -> FullValidationResult:
        """Run complete validation pipeline on rule set."""
        logger.info(f"Running full validation pipeline for rule set {rule_set.id}")

        # Run all validation steps
        status_result = self.validate_rule_set_status(rule_set)
        completeness_result = self.validate_rules_completeness(rule_set)
        consistency_result = self.validate_rule_consistency(rule_set)
        reasonableness_result = self.validate_rate_reasonableness(rule_set)

        # Generate summary
        summary = self.generate_validation_summary(rule_set)

        # Determine overall status
        if status_result.is_valid and completeness_result.is_complete and consistency_result.is_consistent:
            if reasonableness_result.all_reasonable and summary.error_count == 0:
                overall_status = "VALID"
            elif summary.error_count == 0:
                overall_status = "WARNING"
            else:
                overall_status = "INVALID"
        else:
            overall_status = "INVALID"

        # Check publication readiness
        publication_result = self.validate_for_publication(rule_set)
        can_publish = publication_result.can_publish

        total_issues = (len(status_result.issues) +
                       len(completeness_result.missing_combinations) +
                       len(consistency_result.inconsistencies) +
                       len(reasonableness_result.unreasonable_rates) +
                       summary.total_issues)

        logger.info(f"Validation completed. Status: {overall_status}, Issues: {total_issues}, "
                   f"Can publish: {can_publish}")

        return FullValidationResult(
            overall_status=overall_status,
            total_issues=total_issues,
            can_publish=can_publish,
            status_result=status_result,
            completeness_result=completeness_result,
            consistency_result=consistency_result,
            reasonableness_result=reasonableness_result,
            summary=summary
        )

    def get_validation_results(self, rule_set_id: str) -> Dict:
        """Get validation results for API response."""
        rule_set = self.db.get(SaltRuleSet, rule_set_id)
        if not rule_set:
            raise ValueError(f"Rule set not found: {rule_set_id}")

        # Run full validation
        validation_result = self.run_full_validation(rule_set)

        # Get all validation issues
        validation_issues = self.get_validation_issues(rule_set)

        # Format issues for API
        formatted_issues = []
        for issue in validation_issues:
            formatted_issues.append({
                "sheetName": issue.sheet_name,
                "rowNumber": issue.row_number,
                "columnName": issue.column_name,
                "errorCode": issue.error_code,
                "severity": issue.severity.value,
                "message": issue.message,
                "fieldValue": issue.field_value
            })

        return {
            "ruleSetId": rule_set_id,
            "status": validation_result.overall_status.lower(),
            "summary": {
                "totalIssues": validation_result.summary.total_issues,
                "errorCount": validation_result.summary.error_count,
                "warningCount": validation_result.summary.warning_count,
                "rulesProcessed": validation_result.summary.rules_processed
            },
            "issues": formatted_issues,
            "canPublish": validation_result.can_publish,
            "validationTimestamp": self.db.query(SaltRuleSet).get(rule_set_id).created_at.isoformat() + "Z"
        }

    def export_validation_issues_csv(self, rule_set_id: str) -> str:
        """Export validation issues as CSV format for API."""
        rule_set = self.db.get(SaltRuleSet, rule_set_id)
        if not rule_set:
            raise ValueError(f"Rule set not found: {rule_set_id}")

        return self.export_validation_results_csv(rule_set)

    def export_validation_results_csv(self, rule_set: SaltRuleSet) -> str:
        """Export validation results as CSV format."""
        validation_issues = self.get_validation_issues(rule_set)

        # CSV header
        csv_lines = ["sheet_name,row_number,column_name,error_code,severity,message,field_value"]

        # Add each validation issue
        for issue in validation_issues:
            field_value = issue.field_value or ""
            # Escape commas and quotes in CSV values
            message = issue.message.replace('"', '""') if issue.message else ""
            field_value = field_value.replace('"', '""') if field_value else ""

            csv_line = f'"{issue.sheet_name}",{issue.row_number},"{issue.column_name or ""}","{issue.error_code}","{issue.severity.value}","{message}","{field_value}"'
            csv_lines.append(csv_line)

        return "\n".join(csv_lines)

