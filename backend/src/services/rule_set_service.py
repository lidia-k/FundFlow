"""Rule set lifecycle management service for SALT rules."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from uuid import uuid4
from sqlalchemy.orm import Session

from ..models.salt_rule_set import SaltRuleSet, RuleSetStatus
from ..models.withholding_rule import WithholdingRule
from ..models.composite_rule import CompositeRule
from ..models.validation_issue import ValidationIssue
from ..models.resolved_rule import StateEntityTaxRuleResolved
logger = logging.getLogger(__name__)


class RuleSetService:
    """Service for managing SALT rule set lifecycle operations."""

    def __init__(self, db: Session):
        """Initialize the rule set service."""
        self.db = db

    def get_rule_set_detail(self, rule_set_id: str, include_rules: bool = False) -> Dict[str, Any]:
        """
        Get detailed information about a rule set.

        Args:
            rule_set_id: UUID of the rule set
            include_rules: Whether to include actual rule data (default: False)

        Returns:
            Dictionary with detailed rule set information
        """
        rule_set = self.db.get(SaltRuleSet, rule_set_id)
        if not rule_set:
            raise ValueError(f"Rule set not found: {rule_set_id}")

        # Get rule counts
        withholding_count = (
            self.db.query(WithholdingRule)
            .filter(WithholdingRule.rule_set_id == rule_set_id)
            .count()
        )

        composite_count = (
            self.db.query(CompositeRule)
            .filter(CompositeRule.rule_set_id == rule_set_id)
            .count()
        )

        # Get validation issue counts
        error_count = (
            self.db.query(ValidationIssue)
            .filter(
                ValidationIssue.rule_set_id == rule_set_id,
                ValidationIssue.severity == "error"
            )
            .count()
        )

        warning_count = (
            self.db.query(ValidationIssue)
            .filter(
                ValidationIssue.rule_set_id == rule_set_id,
                ValidationIssue.severity == "warning"
            )
            .count()
        )

        # Prepare base result
        result = {
            "id": str(rule_set.id),
            "year": rule_set.year,
            "quarter": rule_set.quarter.value,
            "version": rule_set.version,
            "status": rule_set.status.value,
            "effectiveDate": rule_set.effective_date.isoformat(),
            "expirationDate": rule_set.expiration_date.isoformat() if rule_set.expiration_date else None,
            "createdAt": rule_set.created_at.isoformat() + "Z",
            "publishedAt": rule_set.published_at.isoformat() + "Z" if rule_set.published_at else None,
            "createdBy": rule_set.created_by,
            "description": rule_set.description,
            "ruleCountWithholding": withholding_count,
            "ruleCountComposite": composite_count,
            "validationSummary": {
                "totalIssues": error_count + warning_count,
                "errorCount": error_count,
                "warningCount": warning_count,
                "rulesProcessed": {
                    "withholding": withholding_count,
                    "composite": composite_count
                }
            },
            "sourceFile": {
                "id": str(rule_set.source_file.id),
                "filename": rule_set.source_file.filename,
                "fileSize": rule_set.source_file.file_size,
                "contentType": rule_set.source_file.content_type,
                "uploadTimestamp": rule_set.source_file.upload_timestamp.isoformat() + "Z",
                "uploadedBy": rule_set.source_file.uploaded_by
            } if rule_set.source_file else None
        }

        # Include actual rule data if requested
        if include_rules:
            # Fetch withholding rules
            withholding_rules = (
                self.db.query(WithholdingRule)
                .filter(WithholdingRule.rule_set_id == rule_set_id)
                .order_by(WithholdingRule.state, WithholdingRule.entity_type)
                .all()
            )

            # Fetch composite rules
            composite_rules = (
                self.db.query(CompositeRule)
                .filter(CompositeRule.rule_set_id == rule_set_id)
                .order_by(CompositeRule.state, CompositeRule.entity_type)
                .all()
            )

            # Add rules to result
            result["withholdingRules"] = [
                {
                    "id": str(rule.id),
                    "state": rule.state,
                    "stateCode": rule.state_code.value,
                    "entityType": rule.entity_type,
                    "taxRate": float(rule.tax_rate),
                    "incomeThreshold": float(rule.income_threshold),
                    "taxThreshold": float(rule.tax_threshold)
                }
                for rule in withholding_rules
            ]

            result["compositeRules"] = [
                {
                    "id": str(rule.id),
                    "state": rule.state,
                    "stateCode": rule.state_code.value,
                    "entityType": rule.entity_type,
                    "taxRate": float(rule.tax_rate),
                    "incomeThreshold": float(rule.income_threshold),
                    "mandatoryFiling": rule.mandatory_filing
                }
                for rule in composite_rules
            ]

        return result

    def publish_rule_set(
        self,
        rule_set_id: str,
        effective_date: Optional[date] = None,
        confirm_archive: bool = False
    ) -> Dict[str, Any]:
        """
        Publish a draft rule set to active status.

        Args:
            rule_set_id: UUID of the rule set to publish
            effective_date: Optional effective date (defaults to today)
            confirm_archive: Whether to confirm archiving existing active rule set

        Returns:
            Dictionary with publish result information
        """
        # Get the rule set
        rule_set = self.db.get(SaltRuleSet, rule_set_id)
        if not rule_set:
            raise ValueError(f"Rule set not found: {rule_set_id}")

        if rule_set.status != RuleSetStatus.ACTIVE:
            raise ValueError("Only active rule sets can be republished")

        # Check for validation errors
        error_count = (
            self.db.query(ValidationIssue)
            .filter(
                ValidationIssue.rule_set_id == rule_set_id,
                ValidationIssue.severity == "error"
            )
            .count()
        )

        if error_count > 0:
            raise ValueError("Cannot publish rule set with validation errors")

        # Check for existing active rule set
        existing_active = (
            self.db.query(SaltRuleSet)
            .filter(
                SaltRuleSet.year == rule_set.year,
                SaltRuleSet.quarter == rule_set.quarter,
                SaltRuleSet.status == RuleSetStatus.ACTIVE
            )
            .first()
        )

        if existing_active and not confirm_archive:
            raise ValueError("Existing active rule set must be archived. Set confirm_archive=True")

        # Archive existing active rule set
        if existing_active:
            existing_active.status = RuleSetStatus.ARCHIVED
            existing_active.expiration_date = date.today()
            logger.info(f"Archived existing active rule set: {existing_active.id}")

        # Publish the new rule set
        rule_set.status = RuleSetStatus.ACTIVE
        rule_set.published_at = datetime.now()
        rule_set.effective_date = effective_date or date.today()

        # Generate resolved rules
        self._generate_resolved_rules(rule_set)

        self.db.commit()

        logger.info(f"Published rule set: {rule_set_id}")

        return {
            "ruleSetId": rule_set_id,
            "status": "active",
            "publishedAt": rule_set.published_at.isoformat() + "Z",
            "effectiveDate": rule_set.effective_date.isoformat(),
            "resolvedRulesGenerated": True,
            "archivedPrevious": existing_active is not None
        }

    def archive_rule_set(self, rule_set_id: str) -> Dict[str, Any]:
        """
        Archive a rule set.

        Args:
            rule_set_id: UUID of the rule set to archive

        Returns:
            Dictionary with archive result information
        """
        rule_set = self.db.get(SaltRuleSet, rule_set_id)
        if not rule_set:
            raise ValueError(f"Rule set not found: {rule_set_id}")

        if rule_set.status == RuleSetStatus.ARCHIVED:
            raise ValueError("Rule set is already archived")

        rule_set.status = RuleSetStatus.ARCHIVED
        rule_set.expiration_date = date.today()

        self.db.commit()

        logger.info(f"Archived rule set: {rule_set_id}")

        return {
            "ruleSetId": rule_set_id,
            "status": "archived",
            "archivedAt": rule_set.expiration_date.isoformat()
        }

    def delete_rule_set(self, rule_set_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Delete a rule set and all associated data.

        Args:
            rule_set_id: UUID of the rule set to delete
            force: Whether to force deletion of active rule sets

        Returns:
            Dictionary with deletion result information
        """
        rule_set = self.db.get(SaltRuleSet, rule_set_id)
        if not rule_set:
            raise ValueError(f"Rule set not found: {rule_set_id}")

        if rule_set.status == RuleSetStatus.ACTIVE and not force:
            raise ValueError("Cannot delete active rule set without force=True")

        # Delete associated data
        deleted_counts = {
            "withholding_rules": 0,
            "composite_rules": 0,
            "validation_issues": 0,
            "resolved_rules": 0
        }

        # Delete withholding rules
        withholding_rules = self.db.query(WithholdingRule).filter(
            WithholdingRule.rule_set_id == rule_set_id
        )
        deleted_counts["withholding_rules"] = withholding_rules.count()
        withholding_rules.delete()

        # Delete composite rules
        composite_rules = self.db.query(CompositeRule).filter(
            CompositeRule.rule_set_id == rule_set_id
        )
        deleted_counts["composite_rules"] = composite_rules.count()
        composite_rules.delete()

        # Delete validation issues
        validation_issues = self.db.query(ValidationIssue).filter(
            ValidationIssue.rule_set_id == rule_set_id
        )
        deleted_counts["validation_issues"] = validation_issues.count()
        validation_issues.delete()

        # Delete resolved rules
        resolved_rules = self.db.query(StateEntityTaxRuleResolved).filter(
            StateEntityTaxRuleResolved.rule_set_id == rule_set_id
        )
        deleted_counts["resolved_rules"] = resolved_rules.count()
        resolved_rules.delete()

        # Delete the rule set itself
        self.db.delete(rule_set)
        self.db.commit()

        logger.info(f"Deleted rule set: {rule_set_id}")

        return {
            "ruleSetId": rule_set_id,
            "deleted": True,
            "deletedCounts": deleted_counts
        }

    def get_active_rule_set(self, year: int, quarter: str) -> Optional[Dict[str, Any]]:
        """
        Get the active rule set for a specific year and quarter.

        Args:
            year: Tax year
            quarter: Tax quarter

        Returns:
            Dictionary with active rule set information or None
        """
        rule_set = (
            self.db.query(SaltRuleSet)
            .filter(
                SaltRuleSet.year == year,
                SaltRuleSet.quarter == quarter,
                SaltRuleSet.status == RuleSetStatus.ACTIVE
            )
            .first()
        )

        if rule_set:
            return {
                "id": str(rule_set.id),
                "year": rule_set.year,
                "quarter": rule_set.quarter.value,
                "version": rule_set.version,
                "effectiveDate": rule_set.effective_date.isoformat(),
                "publishedAt": rule_set.published_at.isoformat() + "Z" if rule_set.published_at else None
            }

        return None

    def _generate_resolved_rules(self, rule_set: SaltRuleSet) -> None:
        """
        Generate resolved rules table for fast calculations.

        Args:
            rule_set: The rule set being published
        """
        logger.info(f"Generating resolved rules for rule set: {rule_set.id}")

        # Delete existing resolved rules for this rule set
        self.db.query(StateEntityTaxRuleResolved).filter(
            StateEntityTaxRuleResolved.rule_set_id == rule_set.id
        ).delete()

        # Get all withholding and composite rules
        withholding_rules = (
            self.db.query(WithholdingRule)
            .filter(WithholdingRule.rule_set_id == rule_set.id)
            .all()
        )

        composite_rules = (
            self.db.query(CompositeRule)
            .filter(CompositeRule.rule_set_id == rule_set.id)
            .all()
        )

        # Create lookup dictionaries
        withholding_lookup = {
            (rule.state_code, rule.entity_type): rule for rule in withholding_rules
        }
        composite_lookup = {
            (rule.state_code, rule.entity_type): rule for rule in composite_rules
        }

        # Find all unique state/entity combinations
        all_combinations = set(withholding_lookup.keys()) | set(composite_lookup.keys())

        resolved_rules = []
        for state_code, entity_type in all_combinations:
            withholding_rule = withholding_lookup.get((state_code, entity_type))
            composite_rule = composite_lookup.get((state_code, entity_type))

            # Create resolved rule (only if both withholding and composite exist)
            if withholding_rule and composite_rule:
                resolved_rule = StateEntityTaxRuleResolved(
                    id=uuid4(),
                    rule_set_id=rule_set.id,
                    state_code=state_code,
                    entity_type=entity_type,
                    # Withholding data
                    withholding_rate=withholding_rule.tax_rate,
                    withholding_income_threshold=withholding_rule.income_threshold,
                    withholding_tax_threshold=withholding_rule.tax_threshold,
                    # Composite data
                    composite_rate=composite_rule.tax_rate,
                    composite_income_threshold=composite_rule.income_threshold,
                    composite_mandatory_filing=composite_rule.mandatory_filing,
                    composite_min_tax=composite_rule.min_tax_amount,
                    composite_max_tax=composite_rule.max_tax_amount,
                    # Effective dates
                    effective_date=rule_set.effective_date,
                    expiration_date=rule_set.expiration_date,
                    # Audit trail
                    created_at=datetime.now(),
                    source_withholding_rule_id=withholding_rule.id,
                    source_composite_rule_id=composite_rule.id
                )
                resolved_rules.append(resolved_rule)

        # Bulk insert resolved rules
        self.db.add_all(resolved_rules)

        logger.info(f"Generated {len(resolved_rules)} resolved rules")

 