"""Distribution processing service with exemptions."""

from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.distribution import Distribution, JurisdictionType
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
        """
        distributions = []

        # Create TX_NM distribution if amount > 0
        tx_nm_amount = parsed_row['distribution_tx_nm']
        if tx_nm_amount > 0:
            tx_nm_distribution = Distribution(
                investor_id=investor.id,
                session_id=session_id,
                fund_code=fund_code,
                period_quarter=period_quarter,
                period_year=period_year,
                jurisdiction=JurisdictionType.TX_NM,
                amount=tx_nm_amount,
                composite_exemption=parsed_row['nm_composite_exemption'],
                withholding_exemption=parsed_row['nm_withholding_exemption']
            )
            distributions.append(tx_nm_distribution)

        # Create CO distribution if amount > 0
        co_amount = parsed_row['distribution_co']
        if co_amount > 0:
            co_distribution = Distribution(
                investor_id=investor.id,
                session_id=session_id,
                fund_code=fund_code,
                period_quarter=period_quarter,
                period_year=period_year,
                jurisdiction=JurisdictionType.CO,
                amount=co_amount,
                composite_exemption=parsed_row['co_composite_exemption'],
                withholding_exemption=parsed_row['co_withholding_exemption']
            )
            distributions.append(co_distribution)

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

        totals = {
            "TX_NM": Decimal('0.00'),
            "CO": Decimal('0.00'),
            "TOTAL": Decimal('0.00')
        }

        for dist in distributions:
            jurisdiction_key = dist.jurisdiction.value
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

        summary = {
            "TX_NM": {
                "composite_exemptions": 0,
                "withholding_exemptions": 0,
                "total_investors": 0
            },
            "CO": {
                "composite_exemptions": 0,
                "withholding_exemptions": 0,
                "total_investors": 0
            }
        }

        for dist in distributions:
            jurisdiction_key = dist.jurisdiction.value
            summary[jurisdiction_key]["total_investors"] += 1

            if dist.composite_exemption:
                summary[jurisdiction_key]["composite_exemptions"] += 1

            if dist.withholding_exemption:
                summary[jurisdiction_key]["withholding_exemptions"] += 1

        return summary