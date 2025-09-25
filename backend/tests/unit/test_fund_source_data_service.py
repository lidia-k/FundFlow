"""Unit tests for FundSourceDataService database operations."""

from decimal import Decimal
from unittest.mock import MagicMock

from src.models.enums import USJurisdiction
from src.models.fund import Fund
from src.models.fund_source_data import FundSourceData
from src.services.fund_source_data_service import FundSourceDataService


class TestFundSourceDataService:
    """Test FundSourceDataService database operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock()
        self.service = FundSourceDataService(self.mock_db)

        # Create mock fund
        self.mock_fund = MagicMock(spec=Fund)
        self.mock_fund.fund_code = "FUND_A"

    def test_create_fund_source_data_single_record(self):
        """Test creating a single fund source data record."""
        parsed_data = [
            {
                "company_name": "TechCorp Inc",
                "state_jurisdiction": "TX",
                "fund_share_percentage": Decimal("45.5"),
                "total_distribution_amount": Decimal("500000.00"),
            }
        ]

        result = self.service.create_fund_source_data(
            fund=self.mock_fund, session_id="session-123", parsed_data=parsed_data
        )

        # Verify database operations
        assert self.mock_db.add.call_count == 1
        self.mock_db.flush.assert_called_once()
        assert len(result) == 1

        # Check created record properties
        created_record = result[0]
        assert isinstance(created_record, FundSourceData)
        assert created_record.fund_code == "FUND_A"
        assert created_record.company_name == "TechCorp Inc"
        assert created_record.state_jurisdiction == USJurisdiction.TX
        assert created_record.fund_share_percentage == Decimal("45.5")
        assert created_record.total_distribution_amount == Decimal("500000.00")
        assert created_record.session_id == "session-123"

    def test_create_fund_source_data_multiple_records(self):
        """Test creating multiple fund source data records."""
        parsed_data = [
            {
                "company_name": "TechCorp Inc",
                "state_jurisdiction": "TX",
                "fund_share_percentage": Decimal("45.5"),
                "total_distribution_amount": Decimal("500000.00"),
            },
            {
                "company_name": "MedDevice LLC",
                "state_jurisdiction": "CA",
                "fund_share_percentage": Decimal("25.0"),
                "total_distribution_amount": Decimal("300000.00"),
            },
            {
                "company_name": "FinanceGroup LP",
                "state_jurisdiction": "NY",
                "fund_share_percentage": Decimal("15.5"),
                "total_distribution_amount": Decimal("200000.00"),
            },
        ]

        result = self.service.create_fund_source_data(
            fund=self.mock_fund, session_id="session-123", parsed_data=parsed_data
        )

        # Verify database operations
        assert self.mock_db.add.call_count == 3
        self.mock_db.flush.assert_called_once()
        assert len(result) == 3

        # Check all records were created with correct data
        for i, record in enumerate(result):
            assert isinstance(record, FundSourceData)
            assert record.fund_code == "FUND_A"
            assert record.company_name == parsed_data[i]["company_name"]
            assert (
                record.state_jurisdiction.value == parsed_data[i]["state_jurisdiction"]
            )
            assert record.session_id == "session-123"

    def test_create_fund_source_data_decimal_conversion(self):
        """Test that fund_share_percentage is properly converted to Decimal."""
        parsed_data = [
            {
                "company_name": "TechCorp Inc",
                "state_jurisdiction": "TX",
                "fund_share_percentage": 45.5,  # Float input
                "total_distribution_amount": Decimal("500000.00"),
            }
        ]

        result = self.service.create_fund_source_data(
            fund=self.mock_fund, session_id="session-123", parsed_data=parsed_data
        )

        created_record = result[0]
        assert created_record.fund_share_percentage == Decimal("45.5")
        assert isinstance(created_record.fund_share_percentage, Decimal)

    def test_get_fund_source_data_by_session(self):
        """Test retrieving fund source data by session ID."""
        mock_records = [MagicMock(spec=FundSourceData), MagicMock(spec=FundSourceData)]

        # Mock the query chain
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_records
        self.mock_db.query.return_value = mock_query

        result = self.service.get_fund_source_data_by_session("session-123")

        # Verify query was constructed correctly
        self.mock_db.query.assert_called_once_with(FundSourceData)
        mock_query.filter.assert_called_once()
        mock_query.order_by.assert_called_once()
        mock_query.all.assert_called_once()

        assert result == mock_records

    def test_get_fund_source_data_by_fund(self):
        """Test retrieving fund source data by fund code."""
        mock_records = [
            MagicMock(spec=FundSourceData),
            MagicMock(spec=FundSourceData),
            MagicMock(spec=FundSourceData),
        ]

        # Mock the query chain
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_records
        self.mock_db.query.return_value = mock_query

        result = self.service.get_fund_source_data_by_fund("FUND_A")

        # Verify query was constructed correctly
        self.mock_db.query.assert_called_once_with(FundSourceData)
        mock_query.filter.assert_called_once()
        mock_query.order_by.assert_called_once()
        mock_query.all.assert_called_once()

        assert result == mock_records

    def test_validate_fund_source_data_constraints_no_conflicts(self):
        """Test constraint validation with no conflicts."""
        # Mock existing records query to return empty list
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query

        parsed_data = [
            {"company_name": "TechCorp Inc", "state_jurisdiction": "TX"},
            {"company_name": "MedDevice LLC", "state_jurisdiction": "CA"},
        ]

        validation_errors = self.service.validate_fund_source_data_constraints(
            "FUND_A", parsed_data
        )

        assert len(validation_errors) == 0

    def test_validate_fund_source_data_constraints_existing_conflict(self):
        """Test constraint validation with existing record conflict."""
        # Mock existing record with conflicting company/state
        mock_existing_record = MagicMock(spec=FundSourceData)
        mock_existing_record.company_name = "TechCorp Inc"
        mock_existing_record.state_jurisdiction = MagicMock()
        mock_existing_record.state_jurisdiction.value = "TX"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_existing_record]
        self.mock_db.query.return_value = mock_query

        parsed_data = [
            {
                "company_name": "TechCorp Inc",
                "state_jurisdiction": "TX",  # Conflicts with existing record
            },
            {"company_name": "MedDevice LLC", "state_jurisdiction": "CA"},
        ]

        validation_errors = self.service.validate_fund_source_data_constraints(
            "FUND_A", parsed_data
        )

        assert len(validation_errors) == 1
        assert "TechCorp Inc/TX" in validation_errors[0]
        assert "already exists in fund" in validation_errors[0]

    def test_validate_fund_source_data_constraints_new_data_conflict(self):
        """Test constraint validation with conflicts within new data."""
        # Mock existing records query to return empty list
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query

        parsed_data = [
            {"company_name": "TechCorp Inc", "state_jurisdiction": "TX"},
            {
                "company_name": "TechCorp Inc",
                "state_jurisdiction": "TX",  # Duplicate within new data
            },
            {"company_name": "MedDevice LLC", "state_jurisdiction": "CA"},
        ]

        validation_errors = self.service.validate_fund_source_data_constraints(
            "FUND_A", parsed_data
        )

        assert len(validation_errors) == 1
        assert "TechCorp Inc/TX" in validation_errors[0]
        assert "in upload data" in validation_errors[0]

    def test_validate_fund_source_data_constraints_multiple_conflicts(self):
        """Test constraint validation with multiple types of conflicts."""
        # Mock existing record
        mock_existing_record = MagicMock(spec=FundSourceData)
        mock_existing_record.company_name = "ExistingCorp"
        mock_existing_record.state_jurisdiction = MagicMock()
        mock_existing_record.state_jurisdiction.value = "NY"

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_existing_record]
        self.mock_db.query.return_value = mock_query

        parsed_data = [
            {
                "company_name": "ExistingCorp",
                "state_jurisdiction": "NY",  # Conflicts with existing
            },
            {"company_name": "TechCorp Inc", "state_jurisdiction": "TX"},
            {
                "company_name": "TechCorp Inc",
                "state_jurisdiction": "TX",  # Duplicate within new data
            },
        ]

        validation_errors = self.service.validate_fund_source_data_constraints(
            "FUND_A", parsed_data
        )

        assert len(validation_errors) == 2
        error_messages = " ".join(validation_errors)
        assert "ExistingCorp/NY" in error_messages
        assert "TechCorp Inc/TX" in error_messages

    def test_delete_fund_source_data_by_session(self):
        """Test deleting fund source data by session ID."""
        # Mock the query and delete operation
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.delete.return_value = 3  # 3 records deleted
        self.mock_db.query.return_value = mock_query

        result = self.service.delete_fund_source_data_by_session("session-123")

        # Verify query was constructed correctly
        self.mock_db.query.assert_called_once_with(FundSourceData)
        mock_query.filter.assert_called_once()
        mock_query.delete.assert_called_once()
        self.mock_db.flush.assert_called_once()

        assert result == 3

    def test_delete_fund_source_data_by_session_no_records(self):
        """Test deleting fund source data when no records exist."""
        # Mock the query and delete operation to return 0
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.delete.return_value = 0  # No records deleted
        self.mock_db.query.return_value = mock_query

        result = self.service.delete_fund_source_data_by_session("nonexistent-session")

        # Verify query was constructed correctly
        self.mock_db.query.assert_called_once_with(FundSourceData)
        mock_query.filter.assert_called_once()
        mock_query.delete.assert_called_once()
        self.mock_db.flush.assert_called_once()

        assert result == 0
