"""Unit coverage for commitment percentage parsing in ExcelService."""

from decimal import Decimal
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

import pandas as pd
import pytest

from src.services.excel_service import ExcelService


def _make_dataframe(overrides: Optional[Dict[str, object]] = None) -> pd.DataFrame:
    base_row = {
        "Investor Name": "Alpha Capital",
        "Investor Entity Type": "Corporation",
        "Investor Tax State": "TX",
        "Commitment Percentage": "12.5%",
        "Distribution TX": 1000,
    }
    if overrides:
        base_row.update(overrides)
    return pd.DataFrame([base_row])


def _run_parse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dataframe_factory: Callable[[], pd.DataFrame],
) -> Tuple[ExcelService, pd.DataFrame]:
    fake_file = tmp_path / "input.xlsx"
    fake_file.write_bytes(b"ignored by mock")

    df = dataframe_factory()
    monkeypatch.setattr(pd, "read_excel", lambda *args, **kwargs: df)

    service = ExcelService()
    result = service.parse_excel_file(
        fake_file,
        "(Input Data) FundAlpha_Q1 2024 distribution data_v1.3.xlsx",
    )
    return service, result


def test_commitment_percentage_parses_and_quantizes(tmp_path, monkeypatch):
    _, result = _run_parse(tmp_path, monkeypatch, lambda: _make_dataframe())

    assert result.valid_rows == 1
    assert result.errors == []
    assert result.data[0]["commitment_percentage"] == Decimal("12.5000")


def test_missing_commitment_percentage_is_error(tmp_path, monkeypatch):
    _, result = _run_parse(
        tmp_path,
        monkeypatch,
        lambda: _make_dataframe({"Commitment Percentage": ""}),
    )

    assert result.valid_rows == 0
    assert any(
        error.error_code == "EMPTY_FIELD"
        and error.column_name == "Commitment Percentage"
        for error in result.errors
    )


def test_duplicate_investor_rows_raise_error(tmp_path, monkeypatch):
    def dataframe():
        return pd.concat(
            [
                _make_dataframe(),
                _make_dataframe({"Commitment Percentage": "15%"}),
            ],
            ignore_index=True,
        )

    _, result = _run_parse(tmp_path, monkeypatch, dataframe)

    assert result.valid_rows == 1
    assert any(error.error_code == "DUPLICATE_INVESTOR" for error in result.errors)


def test_commitment_percentage_out_of_range(tmp_path, monkeypatch):
    _, result = _run_parse(
        tmp_path,
        monkeypatch,
        lambda: _make_dataframe({"Commitment Percentage": "120"}),
    )

    assert result.valid_rows == 0
    assert any(
        error.error_code == "PERCENTAGE_OUT_OF_RANGE"
        for error in result.errors
    )
