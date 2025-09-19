"""SaltRuleSet model for version control of SALT rule collections."""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, DateTime, Date, ForeignKey, Text, CheckConstraint, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import relationship
from ..database.connection import Base
from .enums import RuleSetStatus, Quarter


class SaltRuleSet(Base):
    """SaltRuleSet entity for version control of SALT rule collections with lifecycle management."""

    __tablename__ = "salt_rule_sets"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Version information
    year = Column(Integer, nullable=False)
    quarter = Column(SQLEnum(Quarter), nullable=False)
    version = Column(String(20), nullable=False)
    status = Column(SQLEnum(RuleSetStatus), nullable=False, default=RuleSetStatus.ACTIVE)

    # Lifecycle dates
    effective_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)

    # User tracking
    created_by = Column(String(100), nullable=False)

    # Metadata
    description = Column(Text, nullable=True)
    rule_count_withholding = Column(Integer, nullable=False, default=0)
    rule_count_composite = Column(Integer, nullable=False, default=0)

    # Foreign key
    source_file_id = Column(String(36), ForeignKey("source_files.id"), nullable=False)

    # Relationships
    source_file = relationship("SourceFile", back_populates="rule_set")
    withholding_rules = relationship("WithholdingRule", back_populates="rule_set", cascade="all, delete-orphan")
    composite_rules = relationship("CompositeRule", back_populates="rule_set", cascade="all, delete-orphan")
    validation_issues = relationship("ValidationIssue", back_populates="rule_set", cascade="all, delete-orphan")
    resolved_rules = relationship("StateEntityTaxRuleResolved", back_populates="rule_set", cascade="all, delete-orphan")

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "year >= 2020 AND year <= 2030",
            name="ck_salt_rule_set_year_range"
        ),
        CheckConstraint(
            "rule_count_withholding >= 0",
            name="ck_salt_rule_set_withholding_count_positive"
        ),
        CheckConstraint(
            "rule_count_composite >= 0",
            name="ck_salt_rule_set_composite_count_positive"
        ),
        # Unique constraint: only one active rule set per year/quarter
        UniqueConstraint(
            "year", "quarter", "status",
            name="uq_salt_rule_set_active_year_quarter"
        ),
    )

    def __repr__(self) -> str:
        return f"<SaltRuleSet(id='{self.id}', year={self.year}, quarter='{self.quarter.value}', status='{self.status.value}')>"