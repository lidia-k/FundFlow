"""Tax calculation service for withholding and composite rules."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session, joinedload

from ..models.composite_rule import CompositeRule
from ..models.distribution import Distribution
from ..models.enums import InvestorEntityType, RuleSetStatus
from ..models.investor import Investor
from ..models.salt_rule_set import SaltRuleSet
from ..models.withholding_rule import WithholdingRule

RuleKey = tuple[str, str]


@dataclass
class RuleContext:
    """Resolved rule context for a single SALT rule set."""

    rule_set: SaltRuleSet
    composite_rules: dict[RuleKey, CompositeRule]
    withholding_rules: dict[RuleKey, WithholdingRule]

    def is_empty(self) -> bool:
        """Return True when no usable rules exist."""
        return not (self.composite_rules or self.withholding_rules)


class TaxCalculationService:
    """Applies composite and withholding tax calculations to distributions."""

    _CENT = Decimal("0.01")

    def __init__(self, db: Session) -> None:
        self.db = db

    def apply_for_session(self, session_id: str) -> None:
        """Apply withholding/composite tax calculations for a session."""
        distributions = (
            self.db.query(Distribution)
            .options(
                joinedload(Distribution.investor),
                joinedload(Distribution.fund),
            )
            .filter(Distribution.session_id == session_id)
            .all()
        )

        if not distributions:
            return

        active_rule_set = self._get_active_rule_set()
        if not active_rule_set:
            # Ensure stale values are cleared when no rules are active
            for distribution in distributions:
                distribution.composite_tax_amount = None
                distribution.withholding_tax_amount = None
            return

        rule_context = self._build_rule_context(active_rule_set)
        if rule_context.is_empty():
            for distribution in distributions:
                distribution.composite_tax_amount = None
                distribution.withholding_tax_amount = None
            return

        for distribution in distributions:
            self._apply_tax_logic(distribution, rule_context)

    def _get_active_rule_set(self) -> SaltRuleSet | None:
        """Return the current active SALT rule set if one exists."""
        return (
            self.db.query(SaltRuleSet)
            .filter(SaltRuleSet.status == RuleSetStatus.ACTIVE)
            .order_by(SaltRuleSet.effective_date.desc())
            .first()
        )

    def _build_rule_context(self, rule_set: SaltRuleSet) -> RuleContext:
        """Load withholding and composite rules for the active rule set."""
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

        withholding_lookup: dict[RuleKey, WithholdingRule] = {
            (rule.state_code.value, rule.entity_type): rule
            for rule in withholding_rules
        }
        composite_lookup: dict[RuleKey, CompositeRule] = {
            (rule.state_code.value, rule.entity_type): rule for rule in composite_rules
        }

        return RuleContext(
            rule_set=rule_set,
            composite_rules=composite_lookup,
            withholding_rules=withholding_lookup,
        )

    def get_rule_context(self) -> RuleContext | None:
        """Expose active rule context for reporting endpoints."""
        active_rule_set = self._get_active_rule_set()
        if not active_rule_set:
            return None

        rule_context = self._build_rule_context(active_rule_set)
        if rule_context.is_empty():
            return None
        return rule_context

    def _apply_tax_logic(
        self, distribution: Distribution, context: RuleContext
    ) -> None:
        """Apply exemption, composite, and withholding tax logic to a distribution."""
        # Reset amounts before recalculation to avoid stale data
        distribution.composite_tax_amount = None
        distribution.withholding_tax_amount = None

        investor: Investor | None = distribution.investor
        if investor is None:
            return

        investor_entity = investor.investor_entity_type
        investor_state = (
            investor.investor_tax_state.value
            if hasattr(investor.investor_tax_state, "value")
            else str(investor.investor_tax_state)
        )

        # Step 1: Handle exemptions
        if distribution.composite_exemption or distribution.withholding_exemption:
            return

        if investor_state and distribution.jurisdiction.value == investor_state:
            return

        entity_code = (
            investor_entity.coding
            if isinstance(investor_entity, InvestorEntityType)
            else str(investor_entity)
        )
        rule_key: RuleKey = (distribution.jurisdiction.value, entity_code)

        # Step 2: Composite tax (mandatory states only)
        composite_rule = context.composite_rules.get(rule_key)
        if composite_rule and composite_rule.mandatory_filing:
            if self._amount_exceeds_threshold(
                distribution.amount, composite_rule.income_threshold
            ):
                composite_tax = self._calculate_tax(
                    distribution.amount, composite_rule.tax_rate
                )
                if composite_tax is not None and composite_tax > Decimal("0.00"):
                    distribution.composite_tax_amount = composite_tax
                    return

        # Step 3: Withholding tax (only if composite not applied)
        withholding_rule = context.withholding_rules.get(rule_key)
        if not withholding_rule:
            return

        if not self._amount_exceeds_threshold(
            distribution.amount, withholding_rule.income_threshold
        ):
            return

        withholding_tax = self._calculate_tax(
            distribution.amount, withholding_rule.tax_rate
        )
        if withholding_tax is None:
            return

        # Apply per-partner withholding tax threshold rule (> threshold)
        if (
            withholding_rule.tax_threshold is not None
            and withholding_tax <= withholding_rule.tax_threshold
        ):
            return

        if withholding_tax > Decimal("0.00"):
            distribution.withholding_tax_amount = withholding_tax

    def _amount_exceeds_threshold(
        self, amount: Decimal, threshold: Decimal | None
    ) -> bool:
        """Return True when the amount exceeds a given threshold."""
        if threshold is None:
            return True
        return amount > threshold

    def _calculate_tax(
        self, amount: Decimal, rate: Decimal | None
    ) -> Decimal | None:
        """Calculate tax amount using the provided rate."""
        if rate is None:
            return None
        tax_amount = (amount * rate).quantize(self._CENT, rounding=ROUND_HALF_UP)
        return tax_amount
