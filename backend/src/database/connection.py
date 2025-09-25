"""Database connection and session management."""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def _ensure_distribution_tax_columns(engine, database_url: str) -> None:
    """Ensure new tax columns exist on the distributions table for legacy databases."""
    with engine.connect() as connection:
        if "sqlite" in database_url:
            existing_columns = {
                row[1] for row in connection.execute(text("PRAGMA table_info(distributions);"))
            }

            if "composite_tax_amount" not in existing_columns:
                connection.execute(
                    text("ALTER TABLE distributions ADD COLUMN composite_tax_amount NUMERIC(12,2)")
                )

            if "withholding_tax_amount" not in existing_columns:
                connection.execute(
                    text("ALTER TABLE distributions ADD COLUMN withholding_tax_amount NUMERIC(12,2)")
                )
        else:
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS distributions ADD COLUMN IF NOT EXISTS composite_tax_amount NUMERIC(12,2)"
                )
            )
            connection.execute(
                text(
                    "ALTER TABLE IF EXISTS distributions ADD COLUMN IF NOT EXISTS withholding_tax_amount NUMERIC(12,2)"
                )
            )

        connection.commit()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/fundflow.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("DEBUG", "false").lower() == "true"
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    _ensure_distribution_tax_columns(engine, DATABASE_URL)
