"""WithholdingRule model for tax withholding rates and thresholds."""

import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, Enum as SQLEnum, DECIMAL
from sqlalchemy.orm import relationship
from ..database.connection import Base
from .enums import USJurisdiction


class WithholdingRule(Base):
    """WithholdingRule entity for tax withholding rates and thresholds by state and entity type."""

    __tablename__ = "withholding_rules"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign key
    rule_set_id = Column(String(36), ForeignKey("salt_rule_sets.id"), nullable=False)

    # Rule identification
    state_code = Column(SQLEnum(USJurisdiction), nullable=False)
    entity_type = Column(String(50), nullable=False)

    # Tax calculations
    tax_rate = Column(DECIMAL(5, 4), nullable=False)
    income_threshold = Column(DECIMAL(12, 2), nullable=False)
    tax_threshold = Column(DECIMAL(12, 2), nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    rule_set = relationship("SaltRuleSet", back_populates="withholding_rules")

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "tax_rate >= 0.0000 AND tax_rate <= 1.0000",
            name="ck_withholding_rule_tax_rate_range"
        ),
        CheckConstraint(
            "income_threshold >= 0.00",
            name="ck_withholding_rule_income_threshold_positive"
        ),
        CheckConstraint(
            "tax_threshold >= 0.00",
            name="ck_withholding_rule_tax_threshold_positive"
        ),
        # Unique constraint: one rule per rule_set/state/entity combination
        UniqueConstraint(
            "rule_set_id", "state_code", "entity_type",
            name="uq_withholding_rule_set_state_entity"
        ),
    )

    def __repr__(self) -> str:
        return f"<WithholdingRule(id='{self.id}', state='{self.state_code.value}', entity_type='{self.entity_type}', rate={self.tax_rate})>"