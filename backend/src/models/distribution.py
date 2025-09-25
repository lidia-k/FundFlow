"""Distribution model for quarterly distribution amounts by jurisdiction."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from ..database.connection import Base
from .enums import USJurisdiction


class Distribution(Base):
    """Distribution entity representing quarterly distribution amounts by jurisdiction."""

    __tablename__ = "distributions"

    id = Column(Integer, primary_key=True, index=True)
    investor_id = Column(Integer, ForeignKey("investors.id"), nullable=False)
    session_id = Column(
        String(36), ForeignKey("user_sessions.session_id"), nullable=False
    )
    fund_code = Column(String(50), ForeignKey("funds.fund_code"), nullable=False)
    jurisdiction = Column(SQLEnum(USJurisdiction), nullable=False)
    amount = Column(
        Numeric(precision=12, scale=2), nullable=False, default=Decimal("0.00")
    )
    composite_exemption = Column(Boolean, nullable=False, default=False)
    withholding_exemption = Column(Boolean, nullable=False, default=False)
    composite_tax_amount = Column(Numeric(precision=12, scale=2), nullable=True)
    withholding_tax_amount = Column(Numeric(precision=12, scale=2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    investor = relationship("Investor", back_populates="distributions")
    session = relationship("UserSession", back_populates="distributions")
    fund = relationship("Fund", back_populates="distributions")

    def __repr__(self) -> str:
        return f"<Distribution(id={self.id}, investor_id={self.investor_id}, jurisdiction='{self.jurisdiction.value}', amount={self.amount})>"


# Create unique constraint on distribution per investor per period per jurisdiction
Index(
    "idx_distribution_unique",
    Distribution.investor_id,
    Distribution.fund_code,
    Distribution.jurisdiction,
    unique=True,
)
