"""Rule set lifecycle management service for SALT rules."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from sqlalchemy.orm import Session

from ..models.salt_rule_set import SaltRuleSet, RuleSetStatus
from ..models.withholding_rule import WithholdingRule
from ..models.composite_rule import CompositeRule
from ..models.validation_issue import ValidationIssue
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
            "validation_issues": 0
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


 