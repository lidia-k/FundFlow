"""StateEntityTaxRuleResolved model for denormalized view combining withholding and composite rules."""

import uuid
from datetime import datetime

from sqlalchemy import (
    DECIMAL,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from ..database.connection import Base
from .enums import USJurisdiction


class StateEntityTaxRuleResolved(Base):
    """StateEntityTaxRuleResolved entity for denormalized view combining withholding and composite rules for fast calculations."""

    __tablename__ = "state_entity_tax_rules_resolved"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign key
    rule_set_id = Column(String(36), ForeignKey("salt_rule_sets.id"), nullable=False)

    # Rule identification
    state_code = Column(SQLEnum(USJurisdiction), nullable=False)
    entity_type = Column(String(50), nullable=False)

    # Withholding data
    withholding_rate = Column(DECIMAL(5, 4), nullable=False)
    withholding_income_threshold = Column(DECIMAL(12, 2), nullable=False)
    withholding_tax_threshold = Column(DECIMAL(12, 2), nullable=False)

    # Composite data
    composite_rate = Column(DECIMAL(5, 4), nullable=False)
    composite_income_threshold = Column(DECIMAL(12, 2), nullable=False)
    composite_mandatory_filing = Column(Boolean, nullable=False)
    composite_min_tax = Column(DECIMAL(12, 2), nullable=True)
    composite_max_tax = Column(DECIMAL(12, 2), nullable=True)

    # Effective dates
    effective_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=True)

    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    source_withholding_rule_id = Column(String(36), nullable=False)
    source_composite_rule_id = Column(String(36), nullable=False)

    # Relationships
    rule_set = relationship("SaltRuleSet", back_populates="resolved_rules")

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "withholding_rate >= 0.0000 AND withholding_rate <= 1.0000",
            name="ck_resolved_rule_withholding_rate_range",
        ),
        CheckConstraint(
            "withholding_income_threshold >= 0.00",
            name="ck_resolved_rule_withholding_income_threshold_positive",
        ),
        CheckConstraint(
            "withholding_tax_threshold >= 0.00",
            name="ck_resolved_rule_withholding_tax_threshold_positive",
        ),
        # Composite rate constraints
        CheckConstraint(
            "composite_rate >= 0.0000 AND composite_rate <= 1.0000",
            name="ck_resolved_rule_composite_rate_range",
        ),
        CheckConstraint(
            "composite_income_threshold >= 0.00",
            name="ck_resolved_rule_composite_income_threshold_positive",
        ),
        CheckConstraint(
            "composite_min_tax IS NULL OR composite_min_tax >= 0.00",
            name="ck_resolved_rule_composite_min_tax_positive",
        ),
        CheckConstraint(
            "composite_max_tax IS NULL OR composite_max_tax >= 0.00",
            name="ck_resolved_rule_composite_max_tax_positive",
        ),
        CheckConstraint(
            "composite_min_tax IS NULL OR composite_max_tax IS NULL OR composite_max_tax >= composite_min_tax",
            name="ck_resolved_rule_composite_max_gte_min_tax",
        ),
        # Unique constraint: one resolved rule per rule_set/state/entity combination
        UniqueConstraint(
            "rule_set_id",
            "state_code",
            "entity_type",
            name="uq_resolved_rule_set_state_entity",
        ),
    )

    def __repr__(self) -> str:
        return (
            "<StateEntityTaxRuleResolved(id='{self.id}', state='{self.state_code.value}', "
            "entity_type='{self.entity_type}', withholding_rate={self.withholding_rate}, "
            "composite_rate={self.composite_rate})>"
        )
