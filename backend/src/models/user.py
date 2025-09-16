"""User model for FundFlow application."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from ..database.connection import Base


class User(Base):
    """User entity representing system users (Tax Leads)."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    sessions = relationship("UserSession", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', company='{self.company_name}')>"