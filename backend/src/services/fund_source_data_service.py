"""Service for Fund Source Data operations."""

from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from ..models.enums import USJurisdiction
from ..models.fund import Fund
from ..models.fund_source_data import FundSourceData


class FundSourceDataService:
    """Service for managing fund source data operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_fund_source_data(
        self, fund: Fund, session_id: str, parsed_data: list[dict[str, Any]]
    ) -> list[FundSourceData]:
        """Create fund source data records from parsed Excel data."""
        fund_source_records = []

        for data in parsed_data:
            fund_source_record = FundSourceData(
                fund_code=fund.fund_code,
                company_name=data["company_name"],
                state_jurisdiction=USJurisdiction(data["state_jurisdiction"]),
                fund_share_percentage=Decimal(str(data["fund_share_percentage"])),
                total_distribution_amount=data["total_distribution_amount"],
                session_id=session_id,
            )

            self.db.add(fund_source_record)
            fund_source_records.append(fund_source_record)

        self.db.flush()
        return fund_source_records

    def get_fund_source_data_by_session(self, session_id: str) -> list[FundSourceData]:
        """Get all fund source data for a specific session."""
        return (
            self.db.query(FundSourceData)
            .filter(FundSourceData.session_id == session_id)
            .order_by(FundSourceData.company_name, FundSourceData.state_jurisdiction)
            .all()
        )

    def get_fund_source_data_by_fund(self, fund_code: str) -> list[FundSourceData]:
        """Get all fund source data for a specific fund."""
        return (
            self.db.query(FundSourceData)
            .filter(FundSourceData.fund_code == fund_code)
            .order_by(FundSourceData.company_name, FundSourceData.state_jurisdiction)
            .all()
        )

    def validate_fund_source_data_constraints(
        self,
        fund_code: str,
        parsed_data: list[dict[str, Any]],
        session_id: str | None = None,
    ) -> list[str]:
        """Validate business rules for fund source data."""
        validation_errors = []

        # Check for duplicate company/state combinations within the same fund/session
        existing_combinations = set()
        if session_id:
            existing_records = (
                self.db.query(FundSourceData)
                .filter(FundSourceData.fund_code == fund_code)
                .filter(FundSourceData.session_id == session_id)
                .all()
            )
        else:
            existing_records = []

        for record in existing_records:
            existing_combinations.add(
                (record.company_name, record.state_jurisdiction.value)
            )

        # Validate new data against existing data
        new_combinations = set()
        for data in parsed_data:
            combo_key = (data["company_name"], data["state_jurisdiction"])

            if combo_key in existing_combinations:
                validation_errors.append(
                    f"Duplicate Company/State combination already exists in fund: {combo_key[0]}/{combo_key[1]}"
                )
            elif combo_key in new_combinations:
                validation_errors.append(
                    f"Duplicate Company/State combination in upload data: {combo_key[0]}/{combo_key[1]}"
                )
            else:
                new_combinations.add(combo_key)

        return validation_errors

    def delete_fund_source_data_by_session(self, session_id: str) -> int:
        """Delete all fund source data for a specific session."""
        deleted_count = (
            self.db.query(FundSourceData)
            .filter(FundSourceData.session_id == session_id)
            .delete()
        )
        self.db.flush()
        return deleted_count
