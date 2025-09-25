"""FundSourceData model for company/state distribution breakdown."""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Numeric,
    DateTime,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.orm import relationship

from ..database.connection import Base
from .enums import USJurisdiction


class FundSourceData(Base):
    """Source distribution data for a fund broken down by company and state."""

    __tablename__ = "fund_source_data"

    id = Column(Integer, primary_key=True)
    fund_code = Column(String(50), ForeignKey("funds.fund_code"), nullable=False)
    company_name = Column(String(255), nullable=False)
    state_jurisdiction = Column(SQLEnum(USJurisdiction), nullable=False)
    fund_share_percentage = Column(Numeric(precision=6, scale=4), nullable=False)
    total_distribution_amount = Column(Numeric(precision=12, scale=2), nullable=False)
    session_id = Column(String(36), ForeignKey("user_sessions.session_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    fund = relationship("Fund", back_populates="fund_source_data")
    session = relationship("UserSession")

    __table_args__ = (
        Index(
            "idx_fund_source_unique",
            fund_code,
            company_name,
            state_jurisdiction,
            unique=True,
        ),
        Index("idx_fund_source_lookup", fund_code, state_jurisdiction),
    )


__all__ = ["FundSourceData"]
