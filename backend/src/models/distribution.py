"""Distribution model for quarterly distribution amounts by jurisdiction."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from ..database.connection import Base
from .enums import USJurisdiction


class Distribution(Base):
    """Distribution entity representing quarterly distribution amounts by jurisdiction."""

    __tablename__ = "distributions"

    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(Integer, ForeignKey("investors.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("user_sessions.session_id"), nullable=False)
    fund_code = Column(String(50), nullable=False)
    period_quarter = Column(String(2), nullable=False)  # Q1, Q2, Q3, Q4
    period_year = Column(Integer, nullable=False)
    jurisdiction = Column(SQLEnum(USJurisdiction), nullable=False)
    amount = Column(Numeric(precision=12, scale=2), nullable=False, default=Decimal('0.00'))
    composite_exemption = Column(Boolean, nullable=False, default=False)
    withholding_exemption = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    investor = relationship("Investor", back_populates="distributions")
    session = relationship("UserSession", back_populates="distributions")

    def __repr__(self) -> str:
        return f"<Distribution(id={self.id}, investor_id={self.investor_id}, jurisdiction='{self.jurisdiction.value}', amount={self.amount})>"


# Create unique constraint on distribution per investor per period per jurisdiction
Index(
    "idx_distribution_unique",
    Distribution.investor_id,
    Distribution.fund_code,
    Distribution.period_quarter,
    Distribution.period_year,
    Distribution.jurisdiction,
    unique=True
)