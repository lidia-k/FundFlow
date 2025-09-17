"""SourceFile model for tracking uploaded Excel workbooks."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from ..database.connection import Base


class SourceFile(Base):
    """SourceFile entity for tracking uploaded Excel workbooks with deduplication."""

    __tablename__ = "source_files"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # File metadata
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False, unique=True)
    sha256_hash = Column(String(64), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)

    # Upload tracking
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    uploaded_by = Column(String(100), nullable=False)

    # Relationships
    rule_set = relationship("SaltRuleSet", back_populates="source_file", uselist=False)

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "file_size > 0 AND file_size <= 20971520",
            name="ck_source_file_size_valid"
        ),
        CheckConstraint(
            "content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'",
            name="ck_source_file_content_type_excel"
        ),
        CheckConstraint(
            "length(filename) <= 255",
            name="ck_source_file_filename_length"
        ),
        CheckConstraint(
            "length(sha256_hash) = 64",
            name="ck_source_file_hash_length"
        ),
        # Note: Unique constraint for sha256_hash per year/quarter would be handled at application level
        # as it requires joining with salt_rule_sets table
    )

    def __repr__(self) -> str:
        return f"<SourceFile(id='{self.id}', filename='{self.filename}', size={self.file_size})>"