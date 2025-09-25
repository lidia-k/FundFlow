"""Unit tests for the simplified ValidationService implementation."""

from unittest.mock import MagicMock

from src.services.validation_service import ValidationService


class TestValidationService:
    def setup_method(self) -> None:
        self.service = ValidationService(db=MagicMock())

    def test_get_errors_by_session_returns_empty_list(self) -> None:
        assert self.service.get_errors_by_session("session-1") == []

    def test_get_error_summary_returns_zeroed_structure(self) -> None:
        summary = self.service.get_error_summary("session-1")
        assert summary == {
            "totalErrors": 0,
            "errorsByType": {},
            "errorsBySheet": {},
        }

    def test_export_errors_to_csv_data_returns_headers_only(self) -> None:
        csv_data = self.service.export_errors_to_csv_data("session-1")
        assert csv_data.strip() == "error_type,sheet_name,row_number,message"
