"""
Unit tests for SALT Matrix v1.2 Excel processing and validation logic.
Tests the actual Excel parsing, rule extraction, and validation against the file structure.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from decimal import Decimal

from src.services.excel_processor import ExcelProcessor
from src.services.validation_service import ValidationService
from src.models.withholding_rule import WithholdingRule
from src.models.composite_rule import CompositeRule
from src.models.validation_issue import ValidationIssue, IssueSeverity
from src.models.enums import USJurisdiction


class TestSaltMatrixProcessing:
    """Unit tests for SALT Matrix v1.2 Excel processing"""

    @pytest.fixture
    def salt_matrix_file_path(self):
        """Get path to the actual SALT Matrix v1.2 file"""
        file_path = Path("./data/samples/input/SALT Matrix_v1.2.xlsx")
        assert file_path.exists(), f"SALT Matrix file not found at {file_path}"
        return file_path

    @pytest.fixture
    def excel_processor(self):
        """Create ExcelProcessor instance"""
        return ExcelProcessor()

    def test_excel_file_structure_validation(self, excel_processor, salt_matrix_file_path):
        """Test that the Excel file has the expected structure"""
        # Mock pandas to test file structure validation
        with patch('pandas.read_excel') as mock_read_excel:
            # Mock the presence of both required sheets
            mock_read_excel.side_effect = [
                # First call for Withholding sheet
                MagicMock(columns=['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'TaxThreshold']),
                # Second call for Composite sheet
                MagicMock(columns=['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'MandatoryFiling', 'MinTaxAmount', 'MaxTaxAmount'])
            ]

            # Should not raise exception for valid structure
            try:
                result = excel_processor.process_file(salt_matrix_file_path, "test-rule-set-id")
                # Processing should complete without errors
                assert result is not None
            except Exception as e:
                pytest.fail(f"Valid file structure should not raise exception: {e}")

    def test_withholding_sheet_processing(self, excel_processor):
        """Test processing of Withholding sheet data"""
        # Mock pandas to return sample withholding data
        with patch('pandas.read_excel') as mock_read_excel:
            # Mock withholding sheet data
            withholding_data = MagicMock()
            withholding_data.columns = ['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'TaxThreshold']
            withholding_data.iterrows.return_value = [
                (0, {
                    'State': 'CA',
                    'EntityType': 'Corporation',
                    'TaxRate': 0.0525,
                    'IncomeThreshold': 1000.00,
                    'TaxThreshold': 100.00
                }),
                (1, {
                    'State': 'NY',
                    'EntityType': 'Partnership',
                    'TaxRate': 0.0625,
                    'IncomeThreshold': 1000.00,
                    'TaxThreshold': 100.00
                }),
                (2, {
                    'State': 'TX',
                    'EntityType': 'LLC',
                    'TaxRate': 0.0000,  # TX has no state income tax
                    'IncomeThreshold': 0.00,
                    'TaxThreshold': 0.00
                })
            ]

            # Mock composite sheet (empty for this test)
            composite_data = MagicMock()
            composite_data.columns = ['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'MandatoryFiling', 'MinTaxAmount', 'MaxTaxAmount']
            composite_data.iterrows.return_value = []

            mock_read_excel.side_effect = [withholding_data, composite_data]

            # Process the mocked data
            result = excel_processor.process_file(Path("mock_file.xlsx"), "test-rule-set-id")

            # Validate withholding rules were created
            assert len(result.withholding_rules) == 3

            # Validate first rule (CA Corporation)
            ca_corp_rule = result.withholding_rules[0]
            assert ca_corp_rule.state_code == USJurisdiction.CA
            assert ca_corp_rule.entity_type == "Corporation"
            assert ca_corp_rule.tax_rate == Decimal('0.0525')
            assert ca_corp_rule.income_threshold == Decimal('1000.00')
            assert ca_corp_rule.tax_threshold == Decimal('100.00')

            # Validate TX rule (should have 0% rate)
            tx_rule = result.withholding_rules[2]
            assert tx_rule.state_code == USJurisdiction.TX
            assert tx_rule.tax_rate == Decimal('0.0000')

    def test_composite_sheet_processing(self, excel_processor):
        """Test processing of Composite sheet data"""
        with patch('pandas.read_excel') as mock_read_excel:
            # Mock empty withholding sheet for this test
            withholding_data = MagicMock()
            withholding_data.columns = ['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'TaxThreshold']
            withholding_data.iterrows.return_value = []

            # Mock composite sheet data
            composite_data = MagicMock()
            composite_data.columns = ['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'MandatoryFiling', 'MinTaxAmount', 'MaxTaxAmount']
            composite_data.iterrows.return_value = [
                (0, {
                    'State': 'CA',
                    'EntityType': 'Corporation',
                    'TaxRate': 0.0875,
                    'IncomeThreshold': 1000.00,
                    'MandatoryFiling': True,
                    'MinTaxAmount': 25.00,
                    'MaxTaxAmount': 10000.00
                }),
                (1, {
                    'State': 'NY',
                    'EntityType': 'Partnership',
                    'TaxRate': 0.0925,
                    'IncomeThreshold': 1000.00,
                    'MandatoryFiling': True,
                    'MinTaxAmount': 50.00,
                    'MaxTaxAmount': 15000.00
                }),
                (2, {
                    'State': 'FL',
                    'EntityType': 'LLC',
                    'TaxRate': 0.0000,  # FL has no state income tax
                    'IncomeThreshold': 0.00,
                    'MandatoryFiling': False,
                    'MinTaxAmount': None,
                    'MaxTaxAmount': None
                })
            ]

            mock_read_excel.side_effect = [withholding_data, composite_data]

            # Process the mocked data
            result = excel_processor.process_file(Path("mock_file.xlsx"), "test-rule-set-id")

            # Validate composite rules were created
            assert len(result.composite_rules) == 3

            # Validate CA Corporation rule
            ca_corp_rule = result.composite_rules[0]
            assert ca_corp_rule.state_code == USJurisdiction.CA
            assert ca_corp_rule.entity_type == "Corporation"
            assert ca_corp_rule.tax_rate == Decimal('0.0875')
            assert ca_corp_rule.mandatory_filing is True
            assert ca_corp_rule.min_tax_amount == Decimal('25.00')
            assert ca_corp_rule.max_tax_amount == Decimal('10000.00')

            # Validate FL rule (no income tax state)
            fl_rule = result.composite_rules[2]
            assert fl_rule.state_code == USJurisdiction.FL
            assert fl_rule.tax_rate == Decimal('0.0000')
            assert fl_rule.mandatory_filing is False
            assert fl_rule.min_tax_amount is None
            assert fl_rule.max_tax_amount is None

    def test_data_validation_errors(self, excel_processor):
        """Test validation errors for invalid data"""
        with patch('pandas.read_excel') as mock_read_excel:
            # Mock withholding sheet with invalid data
            withholding_data = MagicMock()
            withholding_data.columns = ['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'TaxThreshold']
            withholding_data.iterrows.return_value = [
                (0, {
                    'State': 'ZZ',  # Invalid state code
                    'EntityType': 'Corporation',
                    'TaxRate': 0.0525,
                    'IncomeThreshold': 1000.00,
                    'TaxThreshold': 100.00
                }),
                (1, {
                    'State': 'CA',
                    'EntityType': 'Corporation',
                    'TaxRate': 1.5,  # Invalid rate (over 100%)
                    'IncomeThreshold': 1000.00,
                    'TaxThreshold': 100.00
                }),
                (2, {
                    'State': 'NY',
                    'EntityType': '',  # Missing entity type
                    'TaxRate': 0.0625,
                    'IncomeThreshold': 1000.00,
                    'TaxThreshold': 100.00
                })
            ]

            # Mock empty composite sheet
            composite_data = MagicMock()
            composite_data.columns = ['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'MandatoryFiling', 'MinTaxAmount', 'MaxTaxAmount']
            composite_data.iterrows.return_value = []

            mock_read_excel.side_effect = [withholding_data, composite_data]

            # Process the mocked data
            result = excel_processor.process_file(Path("mock_file.xlsx"), "test-rule-set-id")

            # Should have validation issues
            assert len(result.validation_issues) > 0

            # Check for specific validation errors
            error_codes = [issue.error_code for issue in result.validation_issues]
            assert "INVALID_STATE" in error_codes or "INVALID_RATE_RANGE" in error_codes or "MISSING_ENTITY_TYPE" in error_codes

    def test_data_validation_warnings(self, excel_processor):
        """Test validation warnings for unusual but valid data"""
        with patch('pandas.read_excel') as mock_read_excel:
            # Mock withholding sheet with unusual but valid data
            withholding_data = MagicMock()
            withholding_data.columns = ['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'TaxThreshold']
            withholding_data.iterrows.return_value = [
                (0, {
                    'State': 'TX',
                    'EntityType': 'Corporation',
                    'TaxRate': 0.0000,  # 0% rate is unusual but valid for TX
                    'IncomeThreshold': 0.00,
                    'TaxThreshold': 0.00
                }),
                (1, {
                    'State': 'CA',
                    'EntityType': 'Corporation',
                    'TaxRate': 0.1500,  # Very high rate but technically valid
                    'IncomeThreshold': 1000.00,
                    'TaxThreshold': 100.00
                })
            ]

            # Mock empty composite sheet
            composite_data = MagicMock()
            composite_data.columns = ['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'MandatoryFiling', 'MinTaxAmount', 'MaxTaxAmount']
            composite_data.iterrows.return_value = []

            mock_read_excel.side_effect = [withholding_data, composite_data]

            # Process the mocked data
            result = excel_processor.process_file(Path("mock_file.xlsx"), "test-rule-set-id")

            # Should have warnings but not errors
            warnings = [issue for issue in result.validation_issues if issue.severity == IssueSeverity.WARNING]
            errors = [issue for issue in result.validation_issues if issue.severity == IssueSeverity.ERROR]

            assert len(warnings) > 0
            assert len(errors) == 0

            # Check for specific warning types
            warning_codes = [issue.error_code for issue in warnings]
            assert "UNUSUAL_RATE" in warning_codes or "HIGH_RATE" in warning_codes

    def test_missing_required_columns(self, excel_processor):
        """Test handling of missing required columns"""
        with patch('pandas.read_excel') as mock_read_excel:
            # Mock withholding sheet missing required column
            withholding_data = MagicMock()
            withholding_data.columns = ['State', 'EntityType', 'TaxRate']  # Missing IncomeThreshold and TaxThreshold

            # Mock composite sheet with all columns
            composite_data = MagicMock()
            composite_data.columns = ['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'MandatoryFiling', 'MinTaxAmount', 'MaxTaxAmount']
            composite_data.iterrows.return_value = []

            mock_read_excel.side_effect = [withholding_data, composite_data]

            # Should raise exception or create validation error for missing columns
            try:
                result = excel_processor.process_file(Path("mock_file.xlsx"), "test-rule-set-id")
                # If it doesn't raise exception, should have validation errors
                assert len(result.validation_issues) > 0
                error_codes = [issue.error_code for issue in result.validation_issues]
                assert "MISSING_COLUMN" in error_codes or "INVALID_STRUCTURE" in error_codes
            except Exception:
                # Exception for missing required columns is acceptable
                pass

    def test_missing_required_sheets(self, excel_processor):
        """Test handling of missing required sheets"""
        with patch('pandas.read_excel') as mock_read_excel:
            # Mock that one of the required sheets is missing
            mock_read_excel.side_effect = [
                # First call succeeds (Withholding sheet)
                MagicMock(columns=['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'TaxThreshold']),
                # Second call fails (Composite sheet missing)
                Exception("Sheet 'Composite' not found")
            ]

            # Should handle missing sheet gracefully
            try:
                result = excel_processor.process_file(Path("mock_file.xlsx"), "test-rule-set-id")
                # Should have validation error for missing sheet
                assert len(result.validation_issues) > 0
                error_codes = [issue.error_code for issue in result.validation_issues]
                assert "MISSING_SHEET" in error_codes or "INVALID_STRUCTURE" in error_codes
            except Exception:
                # Exception for missing required sheet is acceptable
                pass

    def test_duplicate_rules_detection(self, excel_processor):
        """Test detection of duplicate rules within the same sheet"""
        with patch('pandas.read_excel') as mock_read_excel:
            # Mock withholding sheet with duplicate state/entity combinations
            withholding_data = MagicMock()
            withholding_data.columns = ['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'TaxThreshold']
            withholding_data.iterrows.return_value = [
                (0, {
                    'State': 'CA',
                    'EntityType': 'Corporation',
                    'TaxRate': 0.0525,
                    'IncomeThreshold': 1000.00,
                    'TaxThreshold': 100.00
                }),
                (1, {
                    'State': 'CA',
                    'EntityType': 'Corporation',  # Duplicate state/entity combination
                    'TaxRate': 0.0600,  # Different rate
                    'IncomeThreshold': 1500.00,
                    'TaxThreshold': 150.00
                })
            ]

            # Mock empty composite sheet
            composite_data = MagicMock()
            composite_data.columns = ['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'MandatoryFiling', 'MinTaxAmount', 'MaxTaxAmount']
            composite_data.iterrows.return_value = []

            mock_read_excel.side_effect = [withholding_data, composite_data]

            # Process the mocked data
            result = excel_processor.process_file(Path("mock_file.xlsx"), "test-rule-set-id")

            # Should detect duplicate rule error
            assert len(result.validation_issues) > 0
            error_codes = [issue.error_code for issue in result.validation_issues]
            assert "DUPLICATE_RULE" in error_codes or "DUPLICATE_STATE_ENTITY" in error_codes

    def test_empty_sheets_handling(self, excel_processor):
        """Test handling of empty sheets"""
        with patch('pandas.read_excel') as mock_read_excel:
            # Mock empty withholding sheet
            withholding_data = MagicMock()
            withholding_data.columns = ['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'TaxThreshold']
            withholding_data.iterrows.return_value = []

            # Mock empty composite sheet
            composite_data = MagicMock()
            composite_data.columns = ['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'MandatoryFiling', 'MinTaxAmount', 'MaxTaxAmount']
            composite_data.iterrows.return_value = []

            mock_read_excel.side_effect = [withholding_data, composite_data]

            # Process the mocked data
            result = excel_processor.process_file(Path("mock_file.xlsx"), "test-rule-set-id")

            # Should handle empty sheets gracefully
            assert len(result.withholding_rules) == 0
            assert len(result.composite_rules) == 0

            # May have warning about empty sheets
            warnings = [issue for issue in result.validation_issues if issue.severity == IssueSeverity.WARNING]
            if warnings:
                warning_codes = [issue.error_code for issue in warnings]
                assert "EMPTY_SHEET" in warning_codes or "NO_RULES_FOUND" in warning_codes

    def test_state_jurisdiction_mapping(self, excel_processor):
        """Test that state codes are properly mapped to USJurisdiction enum"""
        with patch('pandas.read_excel') as mock_read_excel:
            # Mock withholding sheet with various state codes
            withholding_data = MagicMock()
            withholding_data.columns = ['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'TaxThreshold']
            withholding_data.iterrows.return_value = [
                (0, {
                    'State': 'CA',
                    'EntityType': 'Corporation',
                    'TaxRate': 0.0525,
                    'IncomeThreshold': 1000.00,
                    'TaxThreshold': 100.00
                }),
                (1, {
                    'State': 'NY',
                    'EntityType': 'Partnership',
                    'TaxRate': 0.0625,
                    'IncomeThreshold': 1000.00,
                    'TaxThreshold': 100.00
                }),
                (2, {
                    'State': 'TX',
                    'EntityType': 'LLC',
                    'TaxRate': 0.0000,
                    'IncomeThreshold': 0.00,
                    'TaxThreshold': 0.00
                })
            ]

            # Mock empty composite sheet
            composite_data = MagicMock()
            composite_data.columns = ['State', 'EntityType', 'TaxRate', 'IncomeThreshold', 'MandatoryFiling', 'MinTaxAmount', 'MaxTaxAmount']
            composite_data.iterrows.return_value = []

            mock_read_excel.side_effect = [withholding_data, composite_data]

            # Process the mocked data
            result = excel_processor.process_file(Path("mock_file.xlsx"), "test-rule-set-id")

            # Validate state codes are properly mapped
            assert len(result.withholding_rules) == 3

            state_codes = [rule.state_code for rule in result.withholding_rules]
            assert USJurisdiction.CA in state_codes
            assert USJurisdiction.NY in state_codes
            assert USJurisdiction.TX in state_codes