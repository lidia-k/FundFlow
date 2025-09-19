"""CompositeRule model for composite tax rates and filing requirements."""

import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, CheckConstraint, UniqueConstraint, Enum as SQLEnum, DECIMAL
from sqlalchemy.orm import relationship
from ..database.connection import Base
from .enums import USJurisdiction


class CompositeRule(Base):
    """CompositeRule entity for composite tax rates and filing requirements by state and entity type."""

    __tablename__ = "composite_rules"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign key
    rule_set_id = Column(String(36), ForeignKey("salt_rule_sets.id"), nullable=False)

    # Rule identification
    state = Column(String(100), nullable=False)  # From "State" column
    state_code = Column(SQLEnum(USJurisdiction), nullable=False)  # From "State Abbrev" column
    entity_type = Column(String(50), nullable=False)  # Entity type coding (Partnership, Corporation, etc.)

    # Tax calculations
    tax_rate = Column(DECIMAL(5, 4), nullable=False)
    # TODO: State-level data duplicated across entity types (see ADR-0002)
    # income_threshold and mandatory_filing are state-level but stored per entity
    # for v1.2 prototype simplicity. Consider normalization in v1.3.
    income_threshold = Column(DECIMAL(12, 2), nullable=False)  # From "Composite Rates_Income Threshold"
    mandatory_filing = Column(Boolean, nullable=False)         # From "Composite Rates_Mandatory Composite"

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    rule_set = relationship("SaltRuleSet", back_populates="composite_rules")

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "tax_rate >= 0.0000 AND tax_rate <= 1.0000",
            name="ck_composite_rule_tax_rate_range"
        ),
        CheckConstraint(
            "income_threshold >= 0.00",
            name="ck_composite_rule_income_threshold_positive"
        ),
        # Unique constraint: one rule per rule_set/state/entity combination
        UniqueConstraint(
            "rule_set_id", "state_code", "entity_type",
            name="uq_composite_rule_set_state_entity"
        ),
    )

    def __repr__(self) -> str:
        return f"<CompositeRule(id='{self.id}', state='{self.state_code.value}', entity_type='{self.entity_type}', rate={self.tax_rate})>"