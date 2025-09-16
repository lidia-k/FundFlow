"""Investor model for persistent investor entities."""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from ..database.connection import Base


class InvestorEntityType(Enum):
    """Investor entity type enumeration."""
    CORPORATION = "Corporation"
    EXEMPT_ORGANIZATION = "Exempt Organization"
    GOVERNMENT_BENEFIT_PLAN = "Government Benefit Plan"
    INDIVIDUAL = "Individual"
    JOINT_TENANCY_TENANCY_IN_COMMON = "Joint Tenancy / Tenancy in Common"
    LLC_TAXED_AS_PARTNERSHIP = "LLC_Taxed as Partnership"
    LLP = "LLP"
    LIMITED_PARTNERSHIP = "Limited Partnership"
    PARTNERSHIP = "Partnership"
    TRUST = "Trust"


class Investor(Base):
    """Investor entity representing persistent investor entities across uploads."""

    __tablename__ = "investors"

    id = Column(Integer, primary_key=True, index=True)
    investor_name = Column(String(255), nullable=False)
    investor_entity_type = Column(SQLEnum(InvestorEntityType), nullable=False)
    investor_tax_state = Column(String(2), nullable=False)  # 2-letter state code
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    distributions = relationship("Distribution", back_populates="investor")

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