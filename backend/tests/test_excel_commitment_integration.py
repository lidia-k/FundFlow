"""Integration test covering Excel parsing through commitment persistence."""

from decimal import Decimal
from pathlib import Path

import pandas as pd

from src.models.investor_fund_commitment import InvestorFundCommitment
from src.services.excel_service import ExcelService
from src.services.fund_service import FundService
from src.services.investor_service import InvestorService


def _dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Investor Name": "Beta Holdings",
                "Investor Entity Type": "Corporation",
                "Investor Tax State": "CO",
                "Commitment Percentage": "25.75%",
                "Distribution CO": 1500,
            }
        ]
    )


def test_excel_flow_creates_investor_commitment(db_session, tmp_path, monkeypatch):
    fake_file = tmp_path / "commitment_input.xlsx"
    fake_file.write_bytes(b"ignored")

    monkeypatch.setattr(pd, "read_excel", lambda *args, **kwargs: _dataframe())

    service = ExcelService()

    result = service.parse_excel_file(
        fake_file,
        "(Input Data) FundBeta_Q2 2024 distribution data_v1.3.xlsx",
    )

    assert result.errors == []
    assert result.valid_rows == 1

    fund_service = FundService(db_session)
    investor_service = InvestorService(db_session)

    fund = fund_service.get_or_create_fund(
        result.fund_info["fund_code"],
        result.fund_info["period_quarter"],
        int(result.fund_info["period_year"]),
    )

    for row in result.data:
        investor = investor_service.find_or_create_investor(
            row["investor_name"],
            row["investor_entity_type"],
            row["investor_tax_state"],
        )
        investor_service.upsert_commitment(
            investor=investor,
            fund=fund,
            commitment_percentage=row["commitment_percentage"],
        )

    stored = db_session.query(InvestorFundCommitment).all()
    assert len(stored) == 1
    assert stored[0].commitment_percentage == Decimal("25.7500")
    assert stored[0].fund_code == result.fund_info["fund_code"]
