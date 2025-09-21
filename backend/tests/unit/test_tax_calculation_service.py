"""Unit tests for TaxCalculationService composite and withholding logic."""

from decimal import Decimal
from unittest.mock import MagicMock

from src.models.composite_rule import CompositeRule
from src.models.distribution import Distribution
from src.models.enums import InvestorEntityType, USJurisdiction
from src.models.investor import Investor
from src.models.withholding_rule import WithholdingRule
from src.services.tax_calculation_service import RuleContext, TaxCalculationService


def make_investor(entity_type: InvestorEntityType, tax_state: USJurisdiction) -> Investor:
    investor = Investor(
        investor_name="Test Investor",
        investor_entity_type=entity_type,
        investor_tax_state=tax_state,
    )
    investor.id = 1
    return investor


def make_distribution(
    investor: Investor,
    amount: Decimal,
    jurisdiction: USJurisdiction,
    composite_exemption: bool = False,
    withholding_exemption: bool = False,
) -> Distribution:
    distribution = Distribution(
        investor_id=investor.id,
        session_id="session-123",
        fund_code="FUND",
        period_quarter="Q1",
        period_year=2025,
        jurisdiction=jurisdiction,
        amount=amount,
        composite_exemption=composite_exemption,
        withholding_exemption=withholding_exemption,
    )
    distribution.investor = investor
    return distribution


def make_rule_context(composite=None, withholding=None) -> RuleContext:
    mock_rule_set = MagicMock()
    return RuleContext(
        rule_set=mock_rule_set,
        composite_rules=composite or {},
        withholding_rules=withholding or {},
    )


class TestTaxCalculationServiceLogic:
    """Validate TaxCalculationService rule application."""

    def setup_method(self) -> None:
        self.service = TaxCalculationService(db=None)

    def test_exemption_skips_calculation(self):
        investor = make_investor(InvestorEntityType.PARTNERSHIP, USJurisdiction.CA)
        distribution = make_distribution(
            investor,
            Decimal("1000.00"),
            USJurisdiction.NY,
            composite_exemption=True,
        )

        context = make_rule_context()

        self.service._apply_tax_logic(distribution, context)

        assert distribution.composite_tax_amount is None
        assert distribution.withholding_tax_amount is None

    def test_composite_tax_applied_when_mandatory_and_threshold_met(self):
        investor = make_investor(InvestorEntityType.PARTNERSHIP, USJurisdiction.CA)
        distribution = make_distribution(investor, Decimal("1200.00"), USJurisdiction.NY)

        composite_rule = CompositeRule(
            rule_set_id="ruleset",
            state="New York",
            state_code=USJurisdiction.NY,
            entity_type="Partnership",
            tax_rate=Decimal("0.0625"),
            income_threshold=Decimal("1000.00"),
            mandatory_filing=True,
        )

        context = make_rule_context(composite={("NY", "Partnership"): composite_rule})

        self.service._apply_tax_logic(distribution, context)

        assert distribution.composite_tax_amount == Decimal("7.50")
        assert distribution.withholding_tax_amount is None

    def test_withholding_tax_applied_when_composite_not_applicable(self):
        investor = make_investor(InvestorEntityType.PARTNERSHIP, USJurisdiction.CA)
        distribution = make_distribution(investor, Decimal("1500.00"), USJurisdiction.TX)

        withholding_rule = WithholdingRule(
            rule_set_id="ruleset",
            state="Texas",
            state_code=USJurisdiction.TX,
            entity_type="Partnership",
            tax_rate=Decimal("0.05"),
            income_threshold=Decimal("500.00"),
            tax_threshold=Decimal("0.00"),
        )

        # Composite rule exists but not mandatory filing
        composite_rule = CompositeRule(
            rule_set_id="ruleset",
            state="Texas",
            state_code=USJurisdiction.TX,
            entity_type="Partnership",
            tax_rate=Decimal("0.07"),
            income_threshold=Decimal("500.00"),
            mandatory_filing=False,
        )

        context = make_rule_context(
            composite={("TX", "Partnership"): composite_rule},
            withholding={("TX", "Partnership"): withholding_rule},
        )

        self.service._apply_tax_logic(distribution, context)

        assert distribution.composite_tax_amount is None
        assert distribution.withholding_tax_amount == Decimal("75.00")

    def test_withholding_tax_discarded_when_below_threshold(self):
        investor = make_investor(InvestorEntityType.PARTNERSHIP, USJurisdiction.CA)
        distribution = make_distribution(investor, Decimal("600.00"), USJurisdiction.CO)

        withholding_rule = WithholdingRule(
            rule_set_id="ruleset",
            state="Colorado",
            state_code=USJurisdiction.CO,
            entity_type="Partnership",
            tax_rate=Decimal("0.05"),
            income_threshold=Decimal("100.00"),
            tax_threshold=Decimal("50.00"),
        )

        context = make_rule_context(withholding={("CO", "Partnership"): withholding_rule})

        self.service._apply_tax_logic(distribution, context)

        assert distribution.withholding_tax_amount is None
