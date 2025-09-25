"""Distribution processing service with exemptions."""

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session, joinedload

from ..models.distribution import Distribution
from ..models.enums import USJurisdiction
from ..models.fund import Fund
from ..models.investor import Investor


class DistributionService:
    """Service for processing distribution records with exemption fields."""

    def __init__(self, db: Session):
        self.db = db

    def create_distributions_for_investor(
        self,
        investor: Investor,
        session_id: str,
        fund: Fund,
        parsed_row: dict[str, Any],
    ) -> list[Distribution]:
        """
        Create distribution records for an investor based on parsed Excel row.

        Creates one record per jurisdiction if amount > 0.
        Uses dynamic state-based data from Excel parsing.
        """
        distributions = []

        # Process each state that has distribution data
        distributions_data = parsed_row.get("distributions", {})
        withholding_exemptions = parsed_row.get("withholding_exemptions", {})
        composite_exemptions = parsed_row.get("composite_exemptions", {})

        for state_code, amount in distributions_data.items():
            if amount > 0:
                # Convert state code to USJurisdiction enum
                try:
                    jurisdiction = USJurisdiction(state_code)
                except ValueError:
                    # Skip invalid state codes
                    continue

                # Get exemption flags for this state
                withholding_exemption = withholding_exemptions.get(state_code, False)
                composite_exemption = composite_exemptions.get(state_code, False)

                distribution = Distribution(
                    investor_id=investor.id,
                    session_id=session_id,
                    fund_code=fund.fund_code,
                    jurisdiction=jurisdiction,
                    amount=amount,
                    composite_exemption=composite_exemption,
                    withholding_exemption=withholding_exemption,
                )
                distribution.fund = fund
                distributions.append(distribution)

        # Add to database
        for distribution in distributions:
            self.db.add(distribution)

        return distributions

    def get_distributions_by_session(self, session_id: str) -> list[Distribution]:
        """Get all distributions for a session."""
        return (
            self.db.query(Distribution)
            .options(
                joinedload(Distribution.investor),
                joinedload(Distribution.fund),
            )
            .filter(Distribution.session_id == session_id)
            .all()
        )

    def get_distributions_by_fund_period(
        self, fund_code: str, period_quarter: str, period_year: int
    ) -> list[Distribution]:
        """Get all distributions for a specific fund and period."""
        return (
            self.db.query(Distribution)
            .join(Distribution.fund)
            .filter(
                Fund.fund_code == fund_code,
                Fund.period_quarter == period_quarter,
                Fund.period_year == period_year,
            )
            .all()
        )

    def calculate_total_distributions(
        self, fund_code: str, period_quarter: str, period_year: int
    ) -> dict[str, Decimal]:
        """Calculate total distribution amounts by jurisdiction."""
        distributions = self.get_distributions_by_fund_period(
            fund_code, period_quarter, period_year
        )

        totals = {"TOTAL": Decimal("0.00")}

        for dist in distributions:
            jurisdiction_key = dist.jurisdiction.value
            if jurisdiction_key not in totals:
                totals[jurisdiction_key] = Decimal("0.00")
            totals[jurisdiction_key] += dist.amount
            totals["TOTAL"] += dist.amount

        return totals

    def get_exemption_summary(
        self, fund_code: str, period_quarter: str, period_year: int
    ) -> dict[str, dict[str, int]]:
        """Get summary of exemptions by jurisdiction."""
        distributions = self.get_distributions_by_fund_period(
            fund_code, period_quarter, period_year
        )

        summary = {}

        for dist in distributions:
            jurisdiction_key = dist.jurisdiction.value
            if jurisdiction_key not in summary:
                summary[jurisdiction_key] = {
                    "composite_exemptions": 0,
                    "withholding_exemptions": 0,
                    "total_investors": 0,
                }

            summary[jurisdiction_key]["total_investors"] += 1

            if dist.composite_exemption:
                summary[jurisdiction_key]["composite_exemptions"] += 1

            if dist.withholding_exemption:
                summary[jurisdiction_key]["withholding_exemptions"] += 1

        return summary
