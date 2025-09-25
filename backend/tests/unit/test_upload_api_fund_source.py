"""Unit tests for Upload API with fund source data integration."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import UploadFile

from src.services.excel_service import ExcelParsingResult


class TestUploadAPIFundSource:
    """Test Upload API with fund source data integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_data_dir = Path(__file__).parent.parent / "test_data"

    @patch("src.api.upload.FundSourceDataService")
    @patch("src.api.upload.ExcelService")
    @patch("src.api.upload.SessionService")
    @patch("src.api.upload.UserService")
    @patch("src.api.upload.InvestorService")
    @patch("src.api.upload.FundService")
    @patch("src.api.upload.DistributionService")
    @patch("src.api.upload.TaxCalculationService")
    async def test_upload_with_fund_source_data_success(
        self,
        mock_tax_calc_service,
        mock_distribution_service,
        mock_fund_service,
        mock_investor_service,
        mock_user_service,
        mock_session_service,
        mock_excel_service,
        mock_fund_source_service,
    ):
        """Test successful upload with fund source data."""
        # Mock services
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1
        mock_session = MagicMock()
        mock_session.session_id = "session-123"
        mock_fund = MagicMock()
        mock_fund.fund_code = "FUND_A"

        # Mock service instances
        mock_user_service_instance = MagicMock()
        mock_user_service_instance.get_or_create_default_user.return_value = mock_user
        mock_user_service.return_value = mock_user_service_instance

        mock_session_service_instance = MagicMock()
        mock_session_service_instance.create_session.return_value = mock_session
        mock_session_service.return_value = mock_session_service_instance

        mock_fund_service_instance = MagicMock()
        mock_fund_service_instance.get_or_create_fund.return_value = mock_fund
        mock_fund_service.return_value = mock_fund_service_instance

        mock_fund_source_service_instance = MagicMock()
        mock_fund_source_service_instance.validate_fund_source_data_constraints.return_value = (
            []
        )
        mock_fund_source_service_instance.create_fund_source_data.return_value = [
            MagicMock(),
            MagicMock(),
        ]
        mock_fund_source_service.return_value = mock_fund_source_service_instance

        mock_investor_service_instance = MagicMock()
        mock_investor_service.return_value = mock_investor_service_instance

        mock_distribution_service_instance = MagicMock()
        mock_distribution_service_instance.create_distributions_for_investor.return_value = [
            MagicMock()
        ]
        mock_distribution_service.return_value = mock_distribution_service_instance

        mock_tax_calc_service_instance = MagicMock()
        mock_tax_calc_service.return_value = mock_tax_calc_service_instance

        # Mock Excel parsing result with fund source data
        mock_parsing_result = ExcelParsingResult(
            data=[
                {
                    "investor_name": "Alpha Partners LP",
                    "investor_entity_type": "Partnership",
                    "investor_tax_state": "TX",
                    "distributions": {"TX": 100000.00},
                    "withholding_exemptions": {},
                    "composite_exemptions": {},
                }
            ],
            errors=[],
            fund_info={
                "fund_code": "FUND_A",
                "period_quarter": "Q1",
                "period_year": "2025",
            },
            total_rows=1,
            valid_rows=1,
            fund_source_data=[
                {
                    "company_name": "TechCorp Inc",
                    "state_jurisdiction": "TX",
                    "fund_share_percentage": 45.5,
                    "total_distribution_amount": 500000.00,
                }
            ],
            fund_source_errors=[],
        )

        mock_excel_service_instance = MagicMock()
        mock_excel_service_instance.parse_excel_file.return_value = mock_parsing_result
        mock_excel_service.return_value = mock_excel_service_instance

        # Mock file upload
        file_content = b"fake excel content"
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "(Input Data) Fund A_Q1 2025 distribution data_v1.3.xlsx"
        mock_file.size = 1024
        mock_file.read = AsyncMock(return_value=file_content)

        # Import and test the upload function
        from src.api.upload import upload_file

        with (
            patch("tempfile.NamedTemporaryFile") as mock_temp_file,
            patch("builtins.open"),
            patch("os.unlink"),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.mkdir"),
        ):

            mock_temp_file_instance = MagicMock()
            mock_temp_file_instance.name = "/tmp/test_file.xlsx"
            mock_temp_file_instance.__enter__.return_value = mock_temp_file_instance
            mock_temp_file.return_value = mock_temp_file_instance

            result = await upload_file(file=mock_file, db=mock_db)

            # Verify result
            assert result["status"] == "completed"
            assert result["session_id"] == "session-123"
            assert result["fund_source_data_created"] == 2
            assert result["fund_source_data_present"] is True

            # Verify fund source data service was called
            mock_fund_source_service_instance.validate_fund_source_data_constraints.assert_called_once_with(
                mock_fund.fund_code,
                mock_parsing_result.fund_source_data,
                mock_session.session_id,
            )
            mock_fund_source_service_instance.create_fund_source_data.assert_called_once()

    @patch("src.api.upload.FundSourceDataService")
    @patch("src.api.upload.ExcelService")
    async def test_upload_fund_source_validation_errors(
        self, mock_excel_service, mock_fund_source_service
    ):
        """Test upload with fund source data validation errors."""
        # Mock parsing result with fund source errors in the main errors list
        mock_error = MagicMock()
        mock_error.severity = MagicMock()
        mock_error.severity.value = "ERROR"
        mock_error.row_number = 2
        mock_error.column_name = "Share (%)"
        mock_error.error_message = "Invalid percentage"
        mock_error.field_value = "invalid"

        mock_parsing_result = ExcelParsingResult(
            data=[],
            errors=[mock_error],  # Error in main errors list
            fund_info={
                "fund_code": "FUND_A",
                "period_quarter": "Q1",
                "period_year": "2025",
            },
            total_rows=1,
            valid_rows=0,
            fund_source_data=[
                {
                    "company_name": "TechCorp Inc",
                    "state_jurisdiction": "TX",
                    "fund_share_percentage": 45.5,
                    "total_distribution_amount": 500000.00,
                }
            ],
            fund_source_errors=[],
        )

        mock_excel_service_instance = MagicMock()
        mock_excel_service_instance.parse_excel_file.return_value = mock_parsing_result
        mock_excel_service.return_value = mock_excel_service_instance

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "(Input Data) Fund A_Q1 2025 distribution data_v1.3.xlsx"
        mock_file.size = 1024
        mock_file.read = AsyncMock(return_value=b"fake excel content")

        from src.api.upload import upload_file

        with (
            patch("tempfile.NamedTemporaryFile") as mock_temp_file,
            patch("os.unlink"),
            patch("pathlib.Path.exists", return_value=True),
        ):

            mock_temp_file_instance = MagicMock()
            mock_temp_file_instance.name = "/tmp/test_file.xlsx"
            mock_temp_file_instance.__enter__.return_value = mock_temp_file_instance
            mock_temp_file.return_value = mock_temp_file_instance

            mock_db = MagicMock()
            result = await upload_file(file=mock_file, db=mock_db)

            # Should return validation_failed due to fund source errors
            assert result["status"] == "validation_failed"
            assert "error_count" in result
            assert result["fund_source_data_present"] is True

    @patch("src.api.upload.FundSourceDataService")
    @patch("src.api.upload.ExcelService")
    @patch("src.api.upload.SessionService")
    @patch("src.api.upload.UserService")
    @patch("src.api.upload.FundService")
    async def test_upload_fund_source_constraint_validation_failure(
        self,
        mock_fund_service,
        mock_user_service,
        mock_session_service,
        mock_excel_service,
        mock_fund_source_service,
    ):
        """Test upload failure due to fund source constraint validation."""
        # Mock services for successful parsing but constraint failure
        mock_user = MagicMock()
        mock_user.id = 1
        mock_session = MagicMock()
        mock_session.session_id = "session-123"
        mock_fund = MagicMock()
        mock_fund.fund_code = "FUND_A"

        mock_user_service_instance = MagicMock()
        mock_user_service_instance.get_or_create_default_user.return_value = mock_user
        mock_user_service.return_value = mock_user_service_instance

        mock_session_service_instance = MagicMock()
        mock_session_service_instance.create_session.return_value = mock_session
        mock_session_service.return_value = mock_session_service_instance

        mock_fund_service_instance = MagicMock()
        mock_fund_service_instance.get_or_create_fund.return_value = mock_fund
        mock_fund_service.return_value = mock_fund_service_instance

        # Mock constraint validation failure
        mock_fund_source_service_instance = MagicMock()
        mock_fund_source_service_instance.validate_fund_source_data_constraints.return_value = [
            "Duplicate Company/State combination already exists: TechCorp Inc/TX"
        ]
        mock_fund_source_service.return_value = mock_fund_source_service_instance

        # Mock successful parsing
        mock_parsing_result = ExcelParsingResult(
            data=[
                {
                    "investor_name": "Alpha Partners LP",
                    "investor_entity_type": "Partnership",
                    "investor_tax_state": "TX",
                    "distributions": {"TX": 100000.00},
                    "withholding_exemptions": {},
                    "composite_exemptions": {},
                }
            ],
            errors=[],
            fund_info={
                "fund_code": "FUND_A",
                "period_quarter": "Q1",
                "period_year": "2025",
            },
            total_rows=1,
            valid_rows=1,
            fund_source_data=[
                {
                    "company_name": "TechCorp Inc",
                    "state_jurisdiction": "TX",
                    "fund_share_percentage": 45.5,
                    "total_distribution_amount": 500000.00,
                }
            ],
            fund_source_errors=[],
        )

        mock_excel_service_instance = MagicMock()
        mock_excel_service_instance.parse_excel_file.return_value = mock_parsing_result
        mock_excel_service.return_value = mock_excel_service_instance

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "(Input Data) Fund A_Q1 2025 distribution data_v1.3.xlsx"
        mock_file.size = 1024
        mock_file.read = AsyncMock(return_value=b"fake excel content")

        from fastapi import HTTPException

        from src.api.upload import upload_file

        with (
            patch("tempfile.NamedTemporaryFile") as mock_temp_file,
            patch("builtins.open"),
            patch("os.unlink"),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.mkdir"),
        ):

            mock_temp_file_instance = MagicMock()
            mock_temp_file_instance.name = "/tmp/test_file.xlsx"
            mock_temp_file_instance.__enter__.return_value = mock_temp_file_instance
            mock_temp_file.return_value = mock_temp_file_instance

            mock_db = MagicMock()

            # Should raise HTTPException due to constraint validation failure
            with pytest.raises(HTTPException) as exc_info:
                await upload_file(file=mock_file, db=mock_db)

            # The API catches HTTPExceptions and re-raises them as 500 errors
            assert exc_info.value.status_code == 500
            assert "Internal server error" in str(exc_info.value.detail)
            # The original error message should be in the details
            assert "Fund source data validation failed" in str(exc_info.value.detail)

            mock_fund_source_service_instance.validate_fund_source_data_constraints.assert_called_once_with(
                mock_fund.fund_code,
                mock_parsing_result.fund_source_data,
                mock_session.session_id,
            )

    @patch("src.api.upload.FundSourceDataService")
    @patch("src.api.upload.ExcelService")
    @patch("src.api.upload.SessionService")
    @patch("src.api.upload.UserService")
    @patch("src.api.upload.FundService")
    @patch("src.api.upload.InvestorService")
    @patch("src.api.upload.DistributionService")
    @patch("src.api.upload.TaxCalculationService")
    async def test_upload_backward_compatibility_no_fund_source(
        self,
        mock_tax_calc_service,
        mock_distribution_service,
        mock_investor_service,
        mock_fund_service,
        mock_user_service,
        mock_session_service,
        mock_excel_service,
        mock_fund_source_service,
    ):
        """Test upload backward compatibility with no fund source data."""
        # Mock services
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1
        mock_session = MagicMock()
        mock_session.session_id = "session-123"
        mock_fund = MagicMock()
        mock_fund.fund_code = "FUND_A"

        # Mock service instances
        mock_user_service_instance = MagicMock()
        mock_user_service_instance.get_or_create_default_user.return_value = mock_user
        mock_user_service.return_value = mock_user_service_instance

        mock_session_service_instance = MagicMock()
        mock_session_service_instance.create_session.return_value = mock_session
        mock_session_service.return_value = mock_session_service_instance

        mock_fund_service_instance = MagicMock()
        mock_fund_service_instance.get_or_create_fund.return_value = mock_fund
        mock_fund_service.return_value = mock_fund_service_instance

        mock_investor_service_instance = MagicMock()
        mock_investor_service.return_value = mock_investor_service_instance

        mock_distribution_service_instance = MagicMock()
        mock_distribution_service_instance.create_distributions_for_investor.return_value = [
            MagicMock()
        ]
        mock_distribution_service.return_value = mock_distribution_service_instance

        mock_tax_calc_service_instance = MagicMock()
        mock_tax_calc_service.return_value = mock_tax_calc_service_instance

        mock_fund_source_service_instance = MagicMock()
        mock_fund_source_service.return_value = mock_fund_source_service_instance

        # Mock Excel parsing result WITHOUT fund source data
        mock_parsing_result = ExcelParsingResult(
            data=[
                {
                    "investor_name": "Alpha Partners LP",
                    "investor_entity_type": "Partnership",
                    "investor_tax_state": "TX",
                    "distributions": {"TX": 100000.00},
                    "withholding_exemptions": {},
                    "composite_exemptions": {},
                }
            ],
            errors=[],
            fund_info={
                "fund_code": "FUND_A",
                "period_quarter": "Q1",
                "period_year": "2025",
            },
            total_rows=1,
            valid_rows=1,
            fund_source_data=[],  # Empty fund source data
            fund_source_errors=[],
        )

        mock_excel_service_instance = MagicMock()
        mock_excel_service_instance.parse_excel_file.return_value = mock_parsing_result
        mock_excel_service.return_value = mock_excel_service_instance

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "(Input Data) Fund D_Q4 2025 distribution data_v1.3.xlsx"
        mock_file.size = 1024
        mock_file.read = AsyncMock(return_value=b"fake excel content")

        from src.api.upload import upload_file

        with (
            patch("tempfile.NamedTemporaryFile") as mock_temp_file,
            patch("builtins.open"),
            patch("os.unlink"),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.mkdir"),
        ):

            mock_temp_file_instance = MagicMock()
            mock_temp_file_instance.name = "/tmp/test_file.xlsx"
            mock_temp_file_instance.__enter__.return_value = mock_temp_file_instance
            mock_temp_file.return_value = mock_temp_file_instance

            result = await upload_file(file=mock_file, db=mock_db)

            # Verify result
            assert result["status"] == "completed"
            assert result["session_id"] == "session-123"
            assert result["fund_source_data_created"] == 0  # No fund source data
            assert result["fund_source_data_present"] is False

            # Verify fund source data service was NOT called for validation/creation
            mock_fund_source_service_instance.validate_fund_source_data_constraints.assert_not_called()
            mock_fund_source_service_instance.create_fund_source_data.assert_not_called()

    @patch("src.api.upload.FundSourceDataService")
    @patch("src.api.upload.ExcelService")
    async def test_upload_fund_source_creation_exception(
        self, mock_excel_service, mock_fund_source_service
    ):
        """Test upload handling of fund source data creation exceptions."""
        # Mock successful parsing but exception during creation
        mock_parsing_result = ExcelParsingResult(
            data=[
                {
                    "investor_name": "Alpha Partners LP",
                    "investor_entity_type": "Partnership",
                    "investor_tax_state": "TX",
                    "distributions": {"TX": 100000.00},
                    "withholding_exemptions": {},
                    "composite_exemptions": {},
                }
            ],
            errors=[],
            fund_info={
                "fund_code": "FUND_A",
                "period_quarter": "Q1",
                "period_year": "2025",
            },
            total_rows=1,
            valid_rows=1,
            fund_source_data=[
                {
                    "company_name": "TechCorp Inc",
                    "state_jurisdiction": "TX",
                    "fund_share_percentage": 45.5,
                    "total_distribution_amount": 500000.00,
                }
            ],
            fund_source_errors=[],
        )

        mock_excel_service_instance = MagicMock()
        mock_excel_service_instance.parse_excel_file.return_value = mock_parsing_result
        mock_excel_service.return_value = mock_excel_service_instance

        # Mock fund source service to raise exception during creation
        mock_fund_source_service_instance = MagicMock()
        mock_fund_source_service_instance.validate_fund_source_data_constraints.return_value = (
            []
        )
        mock_fund_source_service_instance.create_fund_source_data.side_effect = (
            Exception("Database error")
        )
        mock_fund_source_service.return_value = mock_fund_source_service_instance

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "(Input Data) Fund A_Q1 2025 distribution data_v1.3.xlsx"
        mock_file.size = 1024
        mock_file.read = AsyncMock(return_value=b"fake excel content")

        from fastapi import HTTPException

        from src.api.upload import upload_file

        # Mock other required services
        with (
            patch("src.api.upload.UserService") as mock_user_service,
            patch("src.api.upload.SessionService") as mock_session_service,
            patch("src.api.upload.FundService") as mock_fund_service,
            patch("tempfile.NamedTemporaryFile") as mock_temp_file,
            patch("builtins.open"),
            patch("os.unlink"),
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.mkdir"),
        ):

            # Mock service setup
            mock_user_service.return_value.get_or_create_default_user.return_value = (
                MagicMock(id=1)
            )
            mock_session_service.return_value.create_session.return_value = MagicMock(
                session_id="session-123"
            )
            mock_fund_service.return_value.get_or_create_fund.return_value = MagicMock(
                fund_code="FUND_A"
            )

            mock_temp_file_instance = MagicMock()
            mock_temp_file_instance.name = "/tmp/test_file.xlsx"
            mock_temp_file_instance.__enter__.return_value = mock_temp_file_instance
            mock_temp_file.return_value = mock_temp_file_instance

            mock_db = MagicMock()

            # Should raise HTTPException due to creation failure
            with pytest.raises(HTTPException) as exc_info:
                await upload_file(file=mock_file, db=mock_db)

            # The API catches HTTPExceptions and re-raises them as 500 errors
            assert exc_info.value.status_code == 500
            assert "Internal server error" in str(exc_info.value.detail)
            assert "Failed to process fund source data" in str(exc_info.value.detail)
