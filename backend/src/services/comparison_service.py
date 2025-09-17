"""Rule comparison service for diff preview between SALT rule sets."""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, asdict
from decimal import Decimal
from sqlalchemy.orm import Session

from ..models.salt_rule_set import SaltRuleSet, RuleSetStatus
from ..models.withholding_rule import WithholdingRule
from ..models.composite_rule import CompositeRule
from ..models.enums import USJurisdiction

logger = logging.getLogger(__name__)


@dataclass
class RuleChange:
    """Represents a change to a rule."""
    change_type: str  # 'added', 'modified', 'removed'
    rule_type: str    # 'withholding', 'composite'
    state_code: str
    entity_type: str
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None


@dataclass
class ComparisonSummary:
    """Summary of rule set comparison."""
    total_changes: int
    added_rules: int
    modified_rules: int
    removed_rules: int
    withholding_changes: int
    composite_changes: int


@dataclass
class ComparisonResult:
    """Result of rule set comparison."""
    summary: ComparisonSummary
    changes: List[RuleChange]
    current_rule_set: Optional[Dict]
    new_rule_set: Dict
    comparison_timestamp: str


class ComparisonService:
    """Service for comparing SALT rule sets and generating diff previews."""

    def __init__(self, db: Session):
        """Initialize comparison service with database session."""
        self.db = db

    def compare_rule_sets(
        self,
        new_rule_set_id: str,
        current_rule_set_id: Optional[str] = None
    ) -> ComparisonResult:
        """
        Compare two rule sets and generate change preview.

        Args:
            new_rule_set_id: UUID of the new (draft) rule set
            current_rule_set_id: UUID of current rule set, or None to compare with active

        Returns:
            ComparisonResult with detailed changes
        """
        # Load new rule set
        new_rule_set = self.db.get(SaltRuleSet, new_rule_set_id)
        if not new_rule_set:
            raise ValueError(f"Rule set not found: {new_rule_set_id}")

        # Load current rule set
        current_rule_set = None
        if current_rule_set_id:
            current_rule_set = self.db.get(SaltRuleSet, current_rule_set_id)
            if not current_rule_set:
                raise ValueError(f"Current rule set not found: {current_rule_set_id}")
        else:
            # Find active rule set for same year/quarter
            current_rule_set = (
                self.db.query(SaltRuleSet)
                .filter(
                    SaltRuleSet.year == new_rule_set.year,
                    SaltRuleSet.quarter == new_rule_set.quarter,
                    SaltRuleSet.status == RuleSetStatus.ACTIVE
                )
                .first()
            )

        # Compare rules
        changes = self._compare_rules(current_rule_set, new_rule_set)

        # Generate summary
        summary = self._generate_summary(changes)

        # Format result
        return ComparisonResult(
            summary=summary,
            changes=changes,
            current_rule_set=self._format_rule_set_info(current_rule_set) if current_rule_set else None,
            new_rule_set=self._format_rule_set_info(new_rule_set),
            comparison_timestamp=self._get_timestamp()
        )

    def get_rule_set_preview(self, rule_set_id: str) -> Dict:
        """
        Get preview of rule set with change comparison.

        Args:
            rule_set_id: UUID of the rule set

        Returns:
            Dictionary with rule set preview and changes
        """
        comparison_result = self.compare_rule_sets(rule_set_id)

        # Convert to API response format
        return {
            "ruleSetId": rule_set_id,
            "summary": asdict(comparison_result.summary),
            "currentRuleSet": comparison_result.current_rule_set,
            "newRuleSet": comparison_result.new_rule_set,
            "changes": [self._format_change_for_api(change) for change in comparison_result.changes],
            "comparisonTimestamp": comparison_result.comparison_timestamp,
            "hasCurrentRuleSet": comparison_result.current_rule_set is not None
        }

    def get_detailed_changes(self, rule_set_id: str, change_type: Optional[str] = None) -> List[Dict]:
        """
        Get detailed list of changes with filtering.

        Args:
            rule_set_id: UUID of the rule set
            change_type: Filter by change type ('added', 'modified', 'removed')

        Returns:
            List of detailed change objects
        """
        comparison_result = self.compare_rule_sets(rule_set_id)

        changes = comparison_result.changes
        if change_type:
            changes = [c for c in changes if c.change_type == change_type]

        return [self._format_detailed_change(change) for change in changes]

    def _compare_rules(
        self,
        current_rule_set: Optional[SaltRuleSet],
        new_rule_set: SaltRuleSet
    ) -> List[RuleChange]:
        """Compare rules between two rule sets."""
        changes = []

        # Compare withholding rules
        current_withholding = self._load_withholding_rules(current_rule_set)
        new_withholding = self._load_withholding_rules(new_rule_set)

        withholding_changes = self._compare_withholding_rules(current_withholding, new_withholding)
        changes.extend(withholding_changes)

        # Compare composite rules
        current_composite = self._load_composite_rules(current_rule_set)
        new_composite = self._load_composite_rules(new_rule_set)

        composite_changes = self._compare_composite_rules(current_composite, new_composite)
        changes.extend(composite_changes)

        return changes

    def _load_withholding_rules(
        self, rule_set: Optional[SaltRuleSet]
    ) -> Dict[Tuple[str, str], WithholdingRule]:
        """Load withholding rules indexed by (state_code, entity_type)."""
        if not rule_set:
            return {}

        rules = (
            self.db.query(WithholdingRule)
            .filter(WithholdingRule.rule_set_id == rule_set.id)
            .all()
        )

        return {(rule.state_code.value, rule.entity_type): rule for rule in rules}

    def _load_composite_rules(
        self, rule_set: Optional[SaltRuleSet]
    ) -> Dict[Tuple[str, str], CompositeRule]:
        """Load composite rules indexed by (state_code, entity_type)."""
        if not rule_set:
            return {}

        rules = (
            self.db.query(CompositeRule)
            .filter(CompositeRule.rule_set_id == rule_set.id)
            .all()
        )

        return {(rule.state_code.value, rule.entity_type): rule for rule in rules}

    def _compare_withholding_rules(
        self,
        current_rules: Dict[Tuple[str, str], WithholdingRule],
        new_rules: Dict[Tuple[str, str], WithholdingRule]
    ) -> List[RuleChange]:
        """Compare withholding rules and identify changes."""
        changes = []

        current_keys = set(current_rules.keys())
        new_keys = set(new_rules.keys())

        # Added rules
        for key in new_keys - current_keys:
            state_code, entity_type = key
            new_rule = new_rules[key]
            changes.append(RuleChange(
                change_type="added",
                rule_type="withholding",
                state_code=state_code,
                entity_type=entity_type,
                old_values=None,
                new_values=self._extract_withholding_values(new_rule)
            ))

        # Removed rules
        for key in current_keys - new_keys:
            state_code, entity_type = key
            old_rule = current_rules[key]
            changes.append(RuleChange(
                change_type="removed",
                rule_type="withholding",
                state_code=state_code,
                entity_type=entity_type,
                old_values=self._extract_withholding_values(old_rule),
                new_values=None
            ))

        # Modified rules
        for key in current_keys & new_keys:
            current_rule = current_rules[key]
            new_rule = new_rules[key]

            if self._withholding_rules_differ(current_rule, new_rule):
                state_code, entity_type = key
                changes.append(RuleChange(
                    change_type="modified",
                    rule_type="withholding",
                    state_code=state_code,
                    entity_type=entity_type,
                    old_values=self._extract_withholding_values(current_rule),
                    new_values=self._extract_withholding_values(new_rule)
                ))

        return changes

    def _compare_composite_rules(
        self,
        current_rules: Dict[Tuple[str, str], CompositeRule],
        new_rules: Dict[Tuple[str, str], CompositeRule]
    ) -> List[RuleChange]:
        """Compare composite rules and identify changes."""
        changes = []

        current_keys = set(current_rules.keys())
        new_keys = set(new_rules.keys())

        # Added rules
        for key in new_keys - current_keys:
            state_code, entity_type = key
            new_rule = new_rules[key]
            changes.append(RuleChange(
                change_type="added",
                rule_type="composite",
                state_code=state_code,
                entity_type=entity_type,
                old_values=None,
                new_values=self._extract_composite_values(new_rule)
            ))

        # Removed rules
        for key in current_keys - new_keys:
            state_code, entity_type = key
            old_rule = current_rules[key]
            changes.append(RuleChange(
                change_type="removed",
                rule_type="composite",
                state_code=state_code,
                entity_type=entity_type,
                old_values=self._extract_composite_values(old_rule),
                new_values=None
            ))

        # Modified rules
        for key in current_keys & new_keys:
            current_rule = current_rules[key]
            new_rule = new_rules[key]

            if self._composite_rules_differ(current_rule, new_rule):
                state_code, entity_type = key
                changes.append(RuleChange(
                    change_type="modified",
                    rule_type="composite",
                    state_code=state_code,
                    entity_type=entity_type,
                    old_values=self._extract_composite_values(current_rule),
                    new_values=self._extract_composite_values(new_rule)
                ))

        return changes

    def _extract_withholding_values(self, rule: WithholdingRule) -> Dict[str, Any]:
        """Extract values from withholding rule for comparison."""
        return {
            "taxRate": float(rule.tax_rate),
            "incomeThreshold": float(rule.income_threshold),
            "taxThreshold": float(rule.tax_threshold)
        }

    def _extract_composite_values(self, rule: CompositeRule) -> Dict[str, Any]:
        """Extract values from composite rule for comparison."""
        values = {
            "taxRate": float(rule.tax_rate),
            "incomeThreshold": float(rule.income_threshold),
            "mandatoryFiling": rule.mandatory_filing
        }

        if rule.min_tax_amount is not None:
            values["minTaxAmount"] = float(rule.min_tax_amount)
        if rule.max_tax_amount is not None:
            values["maxTaxAmount"] = float(rule.max_tax_amount)

        return values

    def _withholding_rules_differ(self, rule1: WithholdingRule, rule2: WithholdingRule) -> bool:
        """Check if two withholding rules have different values."""
        return (
            rule1.tax_rate != rule2.tax_rate or
            rule1.income_threshold != rule2.income_threshold or
            rule1.tax_threshold != rule2.tax_threshold
        )

    def _composite_rules_differ(self, rule1: CompositeRule, rule2: CompositeRule) -> bool:
        """Check if two composite rules have different values."""
        return (
            rule1.tax_rate != rule2.tax_rate or
            rule1.income_threshold != rule2.income_threshold or
            rule1.mandatory_filing != rule2.mandatory_filing or
            rule1.min_tax_amount != rule2.min_tax_amount or
            rule1.max_tax_amount != rule2.max_tax_amount
        )

    def _generate_summary(self, changes: List[RuleChange]) -> ComparisonSummary:
        """Generate summary statistics from changes."""
        added = len([c for c in changes if c.change_type == "added"])
        modified = len([c for c in changes if c.change_type == "modified"])
        removed = len([c for c in changes if c.change_type == "removed"])

        withholding = len([c for c in changes if c.rule_type == "withholding"])
        composite = len([c for c in changes if c.rule_type == "composite"])

        return ComparisonSummary(
            total_changes=len(changes),
            added_rules=added,
            modified_rules=modified,
            removed_rules=removed,
            withholding_changes=withholding,
            composite_changes=composite
        )

    def _format_rule_set_info(self, rule_set: SaltRuleSet) -> Dict:
        """Format rule set information for API response."""
        return {
            "id": str(rule_set.id),
            "year": rule_set.year,
            "quarter": rule_set.quarter.value,
            "version": rule_set.version,
            "status": rule_set.status.value,
            "effectiveDate": rule_set.effective_date.isoformat(),
            "ruleCountWithholding": rule_set.rule_count_withholding,
            "ruleCountComposite": rule_set.rule_count_composite,
            "createdAt": rule_set.created_at.isoformat() + "Z"
        }

    def _format_change_for_api(self, change: RuleChange) -> Dict:
        """Format change for API response."""
        return {
            "changeType": change.change_type,
            "ruleType": change.rule_type,
            "stateCode": change.state_code,
            "entityType": change.entity_type,
            "oldValues": change.old_values,
            "newValues": change.new_values
        }

    def _format_detailed_change(self, change: RuleChange) -> Dict:
        """Format detailed change with field-level differences."""
        detailed = self._format_change_for_api(change)

        if change.change_type == "modified" and change.old_values and change.new_values:
            field_changes = []
            for field, new_value in change.new_values.items():
                old_value = change.old_values.get(field)
                if old_value != new_value:
                    field_changes.append({
                        "field": field,
                        "oldValue": old_value,
                        "newValue": new_value,
                        "changeDescription": self._describe_field_change(field, old_value, new_value)
                    })
            detailed["fieldChanges"] = field_changes

        return detailed

    def _describe_field_change(self, field: str, old_value: Any, new_value: Any) -> str:
        """Generate human-readable description of field change."""
        if field == "taxRate":
            return f"Tax rate changed from {old_value:.4%} to {new_value:.4%}"
        elif field in ["incomeThreshold", "taxThreshold", "minTaxAmount", "maxTaxAmount"]:
            return f"{field} changed from ${old_value:,.2f} to ${new_value:,.2f}"
        elif field == "mandatoryFiling":
            return f"Mandatory filing changed from {old_value} to {new_value}"
        else:
            return f"{field} changed from {old_value} to {new_value}"

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat() + "Z"