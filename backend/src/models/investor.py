"""Investor model for persistent investor entities."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from ..database.connection import Base
from .enums import USJurisdiction, InvestorEntityType


class Investor(Base):
    """Investor entity representing persistent investor entities across uploads."""

    __tablename__ = "investors"

    id = Column(Integer, primary_key=True, index=True)
    investor_name = Column(String(255), nullable=False)
    investor_entity_type = Column(SQLEnum(InvestorEntityType), nullable=False)
    investor_tax_state = Column(SQLEnum(USJurisdiction), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    distributions = relationship("Distribution", back_populates="investor")
    fund_commitments = relationship("InvestorFundCommitment", back_populates="investor")

    @property
    def funds(self):
        """Return funds this investor has commitments in."""
        return [commitment.fund for commitment in self.fund_commitments]

    def __repr__(self) -> str:
        return f"<Investor(id={self.id}, name='{self.investor_name}', type='{self.investor_entity_type.value}', state='{self.investor_tax_state}')>"


# Create unique constraint on investor identity
Index(
    "idx_investor_identity",
    Investor.investor_name,
    Investor.investor_entity_type,
    Investor.investor_tax_state,
    unique=True
)
