"""Service helpers for Fund model operations."""

from datetime import datetime

from sqlalchemy.orm import Session

from ..models.fund import Fund


class FundService:
    """Provide minimal fund lookup and creation helpers."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_fund(
        self,
        fund_code: str,
        period_quarter: str,
        period_year: int,
    ) -> Fund:
        """Fetch existing fund by code or create a new record with period metadata."""
        fund = self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
        if fund:
            if fund.period_quarter != period_quarter or fund.period_year != period_year:
                raise ValueError("Existing fund has mismatched period metadata.")
            return fund

        fund = Fund(
            fund_code=fund_code,
            period_quarter=period_quarter,
            period_year=period_year,
            created_at=datetime.utcnow(),
        )
        self.db.add(fund)
        self.db.flush()
        return fund

    def get_fund(self, fund_code: str) -> Fund | None:
        """Return fund by code if it exists."""
        return self.db.query(Fund).filter(Fund.fund_code == fund_code).first()
