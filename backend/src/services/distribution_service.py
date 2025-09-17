"""Distribution processing service with exemptions."""

from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.distribution import Distribution
from ..models.enums import USJurisdiction
from ..models.investor import Investor


class DistributionService:
    """Service for processing distribution records with exemption fields."""

    def __init__(self, db: Session):
        self.db = db

    def create_distributions_for_investor(
        self,
        investor: Investor,
        session_id: str,
        fund_code: str,
        period_quarter: str,
        period_year: int,
        parsed_row: Dict[str, Any]
    ) -> List[Distribution]:
        """
        Create distribution records for an investor based on parsed Excel row.

        Creates one record per jurisdiction if amount > 0.
        Uses dynamic state-based data from Excel parsing.
        """
        distributions = []

        # Process each state that has distribution data
        distributions_data = parsed_row.get('distributions', {})
        withholding_exemptions = parsed_row.get('withholding_exemptions', {})
        composite_exemptions = parsed_row.get('composite_exemptions', {})

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
                    fund_code=fund_code,
                    period_quarter=period_quarter,
                    period_year=period_year,
                    jurisdiction=jurisdiction,
                    amount=amount,
                    composite_exemption=composite_exemption,
                    withholding_exemption=withholding_exemption
                )
                distributions.append(distribution)

        # Add to database
        for distribution in distributions:
            self.db.add(distribution)

        return distributions

    def get_distributions_by_session(self, session_id: str) -> List[Distribution]:
        """Get all distributions for a session."""
        return self.db.query(Distribution).filter(
            Distribution.session_id == session_id
        ).all()

    def get_distributions_by_investor(
        self,
        investor_id: int,
        fund_code: Optional[str] = None,
        period_quarter: Optional[str] = None,
        period_year: Optional[int] = None
    ) -> List[Distribution]:
        """Get distributions for an investor with optional filters."""
        query = self.db.query(Distribution).filter(
            Distribution.investor_id == investor_id
        )

        if fund_code:
            query = query.filter(Distribution.fund_code == fund_code)

        if period_quarter:
            query = query.filter(Distribution.period_quarter == period_quarter)

        if period_year:
            query = query.filter(Distribution.period_year == period_year)

        return query.all()

    def get_distributions_by_fund_period(
        self,
        fund_code: str,
        period_quarter: str,
        period_year: int
    ) -> List[Distribution]:
        """Get all distributions for a specific fund and period."""
        return self.db.query(Distribution).filter(
            Distribution.fund_code == fund_code,
            Distribution.period_quarter == period_quarter,
            Distribution.period_year == period_year
        ).all()

    def calculate_total_distributions(
        self,
        fund_code: str,
        period_quarter: str,
        period_year: int
    ) -> Dict[str, Decimal]:
        """Calculate total distribution amounts by jurisdiction."""
        distributions = self.get_distributions_by_fund_period(
            fund_code, period_quarter, period_year
        )

        totals = {"TOTAL": Decimal('0.00')}

        for dist in distributions:
            jurisdiction_key = dist.jurisdiction.value
            if jurisdiction_key not in totals:
                totals[jurisdiction_key] = Decimal('0.00')
            totals[jurisdiction_key] += dist.amount
            totals["TOTAL"] += dist.amount

        return totals

    def get_exemption_summary(
        self,
        fund_code: str,
        period_quarter: str,
        period_year: int
    ) -> Dict[str, Dict[str, int]]:
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
                    "total_investors": 0
                }

            summary[jurisdiction_key]["total_investors"] += 1

            if dist.composite_exemption:
                summary[jurisdiction_key]["composite_exemptions"] += 1

            if dist.withholding_exemption:
                summary[jurisdiction_key]["withholding_exemptions"] += 1

        return summary