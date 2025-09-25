"""Association model between investors and funds with commitment percentage."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import relationship

from ..database.connection import Base


class InvestorFundCommitment(Base):
    """Investor commitment percentage for a specific fund."""

    __tablename__ = "investor_fund_commitments"

    investor_id = Column(Integer, ForeignKey("investors.id"), primary_key=True)
    fund_code = Column(String(50), ForeignKey("funds.fund_code"), primary_key=True)
    commitment_percentage = Column(Numeric(precision=6, scale=4), nullable=False)
    effective_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    investor = relationship("Investor", back_populates="fund_commitments")
    fund = relationship("Fund", back_populates="investor_commitments")

    __table_args__ = (Index("idx_commitment_lookup", fund_code),)

    def __repr__(self) -> str:
        return (
            f"<InvestorFundCommitment(investor_id={self.investor_id}, fund_code='{self.fund_code}', "
            f"commitment_percentage={Decimal(self.commitment_percentage)})>"
        )


__all__ = ["InvestorFundCommitment"]
