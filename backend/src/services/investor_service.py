"""Investor upsert service for finding or creating investor entities."""

from typing import Optional
from sqlalchemy.orm import Session
from ..models.investor import Investor, InvestorEntityType


class InvestorService:
    """Service for managing investor entities with persistence logic."""

    def __init__(self, db: Session):
        self.db = db

    def find_or_create_investor(
        self,
        investor_name: str,
        investor_entity_type: str,
        investor_tax_state: str
    ) -> Investor:
        """
        Find existing investor or create new one.

        Uses (investor_name, investor_entity_type, investor_tax_state) as unique key.
        """
        # Convert entity type string to enum
        try:
            entity_type_enum = InvestorEntityType(investor_entity_type)
        except ValueError:
            raise ValueError(f"Invalid investor entity type: {investor_entity_type}")

        # Try to find existing investor (case-insensitive)
        existing_investor = self.db.query(Investor).filter(
            Investor.investor_name.ilike(investor_name),
            Investor.investor_entity_type == entity_type_enum,
            Investor.investor_tax_state.ilike(investor_tax_state)
        ).first()

        if existing_investor:
            return existing_investor

        # Create new investor
        new_investor = Investor(
            investor_name=investor_name.strip(),
            investor_entity_type=entity_type_enum,
            investor_tax_state=investor_tax_state.upper()
        )

        self.db.add(new_investor)
        self.db.flush()  # Get the ID without committing
        return new_investor

    def get_investor_by_id(self, investor_id: int) -> Optional[Investor]:
        """Get investor by ID."""
        return self.db.query(Investor).filter(Investor.id == investor_id).first()


