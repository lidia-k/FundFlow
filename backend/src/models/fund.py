"""Fund model storing period metadata and relationships."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Index
from sqlalchemy.orm import relationship

from ..database.connection import Base


class Fund(Base):
    """Fund entity storing period metadata for distributions."""

    __tablename__ = "funds"

    fund_code = Column(String(50), primary_key=True)
    period_quarter = Column(String(2), nullable=False)
    period_year = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    fund_source_data = relationship("FundSourceData", back_populates="fund")
    investor_commitments = relationship("InvestorFundCommitment", back_populates="fund")
    distributions = relationship("Distribution", back_populates="fund")

    __table_args__ = (
        Index(
            "idx_fund_period_unique",
            fund_code,
            period_quarter,
            period_year,
            unique=True,
        ),
    )


__all__ = ["Fund"]
