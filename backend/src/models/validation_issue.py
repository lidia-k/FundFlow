"""ValidationIssue model for structured validation error and warning collection."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, CheckConstraint, Enum as SQLEnum
from sqlalchemy.orm import relationship
from ..database.connection import Base
from .enums import IssueSeverity


class ValidationIssue(Base):
    """ValidationIssue entity for structured validation error and warning collection."""

    __tablename__ = "validation_issues"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign key
    rule_set_id = Column(String(36), ForeignKey("salt_rule_sets.id"), nullable=False)

    # Error location
    sheet_name = Column(String(255), nullable=False)
    row_number = Column(Integer, nullable=False)
    column_name = Column(String(50), nullable=True)

    # Error details
    error_code = Column(String(50), nullable=False)
    severity = Column(SQLEnum(IssueSeverity), nullable=False)
    message = Column(String(1000), nullable=False)
    field_value = Column(String(500), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    rule_set = relationship("SaltRuleSet", back_populates="validation_issues")

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "row_number > 0",
            name="ck_validation_issue_row_number_positive"
        ),
        CheckConstraint(
            "length(sheet_name) <= 255",
            name="ck_validation_issue_sheet_name_length"
        ),
        CheckConstraint(
            "length(message) <= 1000",
            name="ck_validation_issue_message_length"
        ),
        CheckConstraint(
            "length(error_code) > 0",
            name="ck_validation_issue_error_code_not_empty"
        ),
    )

    def __repr__(self) -> str:
        return f"<ValidationIssue(id='{self.id}', severity='{self.severity.value}', error_code='{self.error_code}', sheet='{self.sheet_name}', row={self.row_number})>"