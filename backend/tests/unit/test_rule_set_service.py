"""Unit tests for RuleSetService summary and deletion logic."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from src.models.composite_rule import CompositeRule
from src.models.enums import IssueSeverity, Quarter, RuleSetStatus, USJurisdiction
from src.models.salt_rule_set import SaltRuleSet
from src.models.source_file import SourceFile
from src.models.validation_issue import ValidationIssue
from src.models.withholding_rule import WithholdingRule
from src.services.rule_set_service import RuleSetService


def _make_source_file() -> SourceFile:
    return SourceFile(
        id=str(uuid4()),
        filename="rules.xlsx",
        filepath=f"/tmp/{uuid4()}.xlsx",
        file_size=1024,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        uploaded_by="admin@fundflow.com",
    )


def _make_rule_set(source_file_id: str, status: RuleSetStatus = RuleSetStatus.ACTIVE) -> SaltRuleSet:
    now = datetime.utcnow()
    return SaltRuleSet(
        id=str(uuid4()),
        year=2025,
        quarter=Quarter.Q1,
        version="1.0.0",
        status=status,
        effective_date=date(2025, 1, 1),
        created_at=now,
        published_at=now,
        created_by="admin@fundflow.com",
        description="Test rule set",
        source_file_id=source_file_id,
    )


def _add_rules_and_issues(db, rule_set_id: str) -> None:
    withholding = WithholdingRule(
        rule_set_id=rule_set_id,
        state="New York",
        state_code=USJurisdiction.NY,
        entity_type="Partnership",
        tax_rate=Decimal("0.0525"),
        income_threshold=Decimal("1000.00"),
        tax_threshold=Decimal("100.00"),
    )

    composite = CompositeRule(
        rule_set_id=rule_set_id,
        state="New York",
        state_code=USJurisdiction.NY,
        entity_type="Partnership",
        tax_rate=Decimal("0.0625"),
        income_threshold=Decimal("1000.00"),
        mandatory_filing=True,
    )

    error_issue = ValidationIssue(
        rule_set_id=rule_set_id,
        sheet_name="Withholding",
        row_number=10,
        column_name="Tax Rate",
        error_code="INVALID_RATE",
        severity=IssueSeverity.ERROR,
        message="Tax rate must be less than 100%",
    )

    warning_issue = ValidationIssue(
        rule_set_id=rule_set_id,
        sheet_name="Composite",
        row_number=20,
        column_name="Mandatory",
        error_code="OPTIONAL_FIELD",
        severity=IssueSeverity.WARNING,
        message="Mandatory flag defaults to False",
    )

    db.add_all([withholding, composite, error_issue, warning_issue])


class TestRuleSetService:
    def test_get_rule_set_detail_summarizes_counts(self, db_session):
        source_file = _make_source_file()
        rule_set = _make_rule_set(source_file.id)
        db_session.add_all([source_file, rule_set])
        db_session.flush()
        _add_rules_and_issues(db_session, rule_set.id)
        db_session.commit()

        service = RuleSetService(db_session)
        result = service.get_rule_set_detail(rule_set.id)

        assert result["id"] == rule_set.id
        assert result["ruleCountWithholding"] == 1
        assert result["ruleCountComposite"] == 1
        summary = result["validationSummary"]
        assert summary["errorCount"] == 0
        assert summary["warningCount"] == 0
        assert summary["totalIssues"] == 0
        assert result["sourceFile"]["filename"] == "rules.xlsx"
        assert "withholdingRules" not in result
        assert "compositeRules" not in result

    def test_get_rule_set_detail_includes_rules_when_requested(self, db_session):
        source_file = _make_source_file()
        rule_set = _make_rule_set(source_file.id)
        db_session.add_all([source_file, rule_set])
        db_session.flush()
        _add_rules_and_issues(db_session, rule_set.id)
        db_session.commit()

        service = RuleSetService(db_session)
        result = service.get_rule_set_detail(rule_set.id, include_rules=True)

        assert len(result["withholdingRules"]) == 1
        assert result["withholdingRules"][0]["stateCode"] == "NY"
        assert len(result["compositeRules"]) == 1
        assert result["compositeRules"][0]["mandatoryFiling"] is True

    def test_delete_rule_set_requires_force_when_active(self, db_session):
        source_file = _make_source_file()
        rule_set = _make_rule_set(source_file.id, status=RuleSetStatus.ACTIVE)
        db_session.add_all([source_file, rule_set])
        db_session.commit()

        service = RuleSetService(db_session)

        with pytest.raises(ValueError, match="force=True"):
            service.delete_rule_set(rule_set.id)

    def test_delete_rule_set_removes_related_data(self, db_session):
        source_file = _make_source_file()
        rule_set = _make_rule_set(source_file.id, status=RuleSetStatus.ARCHIVED)
        db_session.add_all([source_file, rule_set])
        db_session.flush()
        _add_rules_and_issues(db_session, rule_set.id)
        db_session.commit()

        service = RuleSetService(db_session)
        result = service.delete_rule_set(rule_set.id, force=True)

        assert result["deleted"] is True
        assert result["deletedCounts"]["withholding_rules"] == 1
        assert result["deletedCounts"]["composite_rules"] == 1
        assert db_session.get(SaltRuleSet, rule_set.id) is None
        assert db_session.query(WithholdingRule).filter_by(rule_set_id=rule_set.id).count() == 0
        assert db_session.query(CompositeRule).filter_by(rule_set_id=rule_set.id).count() == 0
        assert db_session.query(ValidationIssue).filter_by(rule_set_id=rule_set.id).count() == 0
