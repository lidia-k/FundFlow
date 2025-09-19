"""
Unit tests for Excel processing service logic
Task: T011 - Unit test Excel processing service logic
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from pathlib import Path
from src.services.excel_processor import ExcelProcessor
from src.models.validation_issue import ValidationIssue, IssueSeverity


class TestExcelProcessorService:
    """Test Excel processing service business logic"""

    def test_excel_processor_initialization(self):
        """Test ExcelProcessor service initialization"""
        # This should fail initially as ExcelProcessor service doesn't exist yet
        processor = ExcelProcessor()
        assert processor is not None

    def test_load_excel_file_success(self):
        """Test successful Excel file loading"""
        processor = ExcelProcessor()

        # Mock pandas read_excel
        mock_dataframes = {
            "Withholding": pd.DataFrame({
                "State": ["CA", "NY", "TX"],
                "EntityType": ["Corporation", "Partnership", "Individual"],
                "TaxRate": [0.0525, 0.0625, 0.0000],
                "IncomeThreshold": [1000.00, 1000.00, 0.00],
                "TaxThreshold": [100.00, 100.00, 0.00]
            }),
            "Composite": pd.DataFrame({
                "State": ["CA", "NY", "TX"],
                "EntityType": ["Corporation", "Partnership", "Individual"],
                "TaxRate": [0.0625, 0.0700, 0.0000],
                "IncomeThreshold": [1000.00, 1000.00, 0.00],
                "MandatoryFiling": [True, True, False]
            })
        }

        with patch('pandas.read_excel', return_value=mock_dataframes):
            result = processor.load_excel_file("/fake/path/file.xlsx")

        assert "Withholding" in result
        assert "Composite" in result
        assert len(result["Withholding"]) == 3
        assert len(result["Composite"]) == 3

    def test_load_excel_file_missing_sheets(self):
        """Test Excel file loading with missing required sheets"""
        processor = ExcelProcessor()

        # Mock pandas read_excel with missing sheets
        mock_dataframes = {
            "SomeOtherSheet": pd.DataFrame()
        }

        with patch('pandas.read_excel', return_value=mock_dataframes):
            with pytest.raises(ValueError, match="Missing required sheets"):
                processor.load_excel_file("/fake/path/file.xlsx")

    def test_validate_withholding_sheet_structure(self):
        """Test withholding sheet structure validation"""
        processor = ExcelProcessor()

        # Valid structure
        valid_df = pd.DataFrame({
            "State": ["CA", "NY"],
            "EntityType": ["Corporation", "Partnership"],
            "TaxRate": [0.0525, 0.0625],
            "IncomeThreshold": [1000.00, 1000.00],
            "TaxThreshold": [100.00, 100.00]
        })

        validation_issues = processor.validate_sheet_structure("Withholding", valid_df)
        assert len(validation_issues) == 0

        # Invalid structure - missing column
        invalid_df = pd.DataFrame({
            "State": ["CA", "NY"],
            "EntityType": ["Corporation", "Partnership"],
            "TaxRate": [0.0525, 0.0625]
            # Missing IncomeThreshold and TaxThreshold
        })

        validation_issues = processor.validate_sheet_structure("Withholding", invalid_df)
        assert len(validation_issues) > 0
        assert any(issue.error_code == "MISSING_COLUMN" for issue in validation_issues)

    def test_validate_composite_sheet_structure(self):
        """Test composite sheet structure validation"""
        processor = ExcelProcessor()

        # Valid structure
        valid_df = pd.DataFrame({
            "State": ["CA", "NY"],
            "EntityType": ["Corporation", "Partnership"],
            "TaxRate": [0.0625, 0.0700],
            "IncomeThreshold": [1000.00, 1000.00],
            "MandatoryFiling": [True, True]
        })

        validation_issues = processor.validate_sheet_structure("Composite", valid_df)
        assert len(validation_issues) == 0

        # Invalid structure - missing column
        invalid_df = pd.DataFrame({
            "State": ["CA", "NY"],
            "EntityType": ["Corporation", "Partnership"]
            # Missing required columns
        })

        validation_issues = processor.validate_sheet_structure("Composite", invalid_df)
        assert len(validation_issues) > 0
        assert any(issue.error_code == "MISSING_COLUMN" for issue in validation_issues)

    def test_validate_data_types(self):
        """Test data type validation"""
        processor = ExcelProcessor()

        # Valid data types
        valid_df = pd.DataFrame({
            "State": ["CA", "NY"],
            "EntityType": ["Corporation", "Partnership"],
            "TaxRate": [0.0525, 0.0625],
            "IncomeThreshold": [1000.00, 1000.00],
            "TaxThreshold": [100.00, 100.00]
        })

        validation_issues = processor.validate_data_types("Withholding", valid_df)
        assert len(validation_issues) == 0

        # Invalid data types
        invalid_df = pd.DataFrame({
            "State": ["CA", "NY"],
            "EntityType": ["Corporation", "Partnership"],
            "TaxRate": ["invalid", "0.0625"],  # String in numeric field
            "IncomeThreshold": [1000.00, "invalid"],  # String in numeric field
            "TaxThreshold": [100.00, 100.00]
        })

        validation_issues = processor.validate_data_types("Withholding", invalid_df)
        assert len(validation_issues) > 0
        assert any(issue.error_code == "INVALID_DATA_TYPE" for issue in validation_issues)

    def test_validate_state_codes(self):
        """Test state code validation"""
        processor = ExcelProcessor()

        # Valid state codes
        valid_df = pd.DataFrame({
            "State": ["CA", "NY", "TX", "FL"],
            "EntityType": ["Corporation"] * 4,
            "TaxRate": [0.0525] * 4,
            "IncomeThreshold": [1000.00] * 4,
            "TaxThreshold": [100.00] * 4
        })

        validation_issues = processor.validate_state_codes("Withholding", valid_df)
        assert len(validation_issues) == 0

        # Invalid state codes
        invalid_df = pd.DataFrame({
            "State": ["CA", "ZZ", "XX"],  # ZZ and XX are invalid
            "EntityType": ["Corporation"] * 3,
            "TaxRate": [0.0525] * 3,
            "IncomeThreshold": [1000.00] * 3,
            "TaxThreshold": [100.00] * 3
        })

        validation_issues = processor.validate_state_codes("Withholding", invalid_df)
        assert len(validation_issues) == 2  # Two invalid state codes
        assert all(issue.error_code == "INVALID_STATE" for issue in validation_issues)

    def test_validate_entity_types(self):
        """Test entity type validation"""
        processor = ExcelProcessor()

        # Valid entity types
        valid_types = ["Corporation", "Partnership", "Individual", "Trust", "S Corporation", "Exempt Org", "IRA"]
        valid_df = pd.DataFrame({
            "State": ["CA"] * len(valid_types),
            "EntityType": valid_types,
            "TaxRate": [0.0525] * len(valid_types),
            "IncomeThreshold": [1000.00] * len(valid_types),
            "TaxThreshold": [100.00] * len(valid_types)
        })

        validation_issues = processor.validate_entity_types("Withholding", valid_df)
        assert len(validation_issues) == 0

        # Invalid entity types
        invalid_df = pd.DataFrame({
            "State": ["CA", "NY"],
            "EntityType": ["Corporation", "InvalidType"],  # InvalidType is not valid
            "TaxRate": [0.0525, 0.0625],
            "IncomeThreshold": [1000.00, 1000.00],
            "TaxThreshold": [100.00, 100.00]
        })

        validation_issues = processor.validate_entity_types("Withholding", invalid_df)
        assert len(validation_issues) == 1
        assert validation_issues[0].error_code == "INVALID_ENTITY_TYPE"

    def test_validate_rate_ranges(self):
        """Test tax rate range validation"""
        processor = ExcelProcessor()

        # Valid tax rates
        valid_df = pd.DataFrame({
            "State": ["CA", "NY", "TX"],
            "EntityType": ["Corporation"] * 3,
            "TaxRate": [0.0000, 0.0525, 1.0000],  # Valid range 0-1
            "IncomeThreshold": [1000.00] * 3,
            "TaxThreshold": [100.00] * 3
        })

        validation_issues = processor.validate_rate_ranges("Withholding", valid_df)
        assert len(validation_issues) == 0

        # Invalid tax rates
        invalid_df = pd.DataFrame({
            "State": ["CA", "NY", "TX"],
            "EntityType": ["Corporation"] * 3,
            "TaxRate": [-0.01, 0.0525, 1.01],  # Negative and >100%
            "IncomeThreshold": [1000.00] * 3,
            "TaxThreshold": [100.00] * 3
        })

        validation_issues = processor.validate_rate_ranges("Withholding", invalid_df)
        assert len(validation_issues) == 2  # Two invalid rates
        assert all(issue.error_code == "INVALID_RATE_RANGE" for issue in validation_issues)

    def test_validate_duplicate_rules(self):
        """Test duplicate rule validation"""
        processor = ExcelProcessor()

        # No duplicates
        valid_df = pd.DataFrame({
            "State": ["CA", "NY", "TX"],
            "EntityType": ["Corporation", "Corporation", "Partnership"],
            "TaxRate": [0.0525, 0.0625, 0.0000],
            "IncomeThreshold": [1000.00, 1000.00, 0.00],
            "TaxThreshold": [100.00, 100.00, 0.00]
        })

        validation_issues = processor.validate_duplicate_rules("Withholding", valid_df)
        assert len(validation_issues) == 0

        # With duplicates
        duplicate_df = pd.DataFrame({
            "State": ["CA", "CA", "NY"],
            "EntityType": ["Corporation", "Corporation", "Partnership"],  # CA+Corporation appears twice
            "TaxRate": [0.0525, 0.0525, 0.0625],
            "IncomeThreshold": [1000.00, 1000.00, 1000.00],
            "TaxThreshold": [100.00, 100.00, 100.00]
        })

        validation_issues = processor.validate_duplicate_rules("Withholding", duplicate_df)
        assert len(validation_issues) > 0
        assert any(issue.error_code == "DUPLICATE_RULE" for issue in validation_issues)

    def test_process_file_complete_workflow(self):
        """Test complete file processing workflow"""
        processor = ExcelProcessor()

        # Mock successful file processing
        mock_dataframes = {
            "Withholding": pd.DataFrame({
                "State": ["CA", "NY"],
                "EntityType": ["Corporation", "Partnership"],
                "TaxRate": [0.0525, 0.0625],
                "IncomeThreshold": [1000.00, 1000.00],
                "TaxThreshold": [100.00, 100.00]
            }),
            "Composite": pd.DataFrame({
                "State": ["CA", "NY"],
                "EntityType": ["Corporation", "Partnership"],
                "TaxRate": [0.0625, 0.0700],
                "IncomeThreshold": [1000.00, 1000.00],
                "MandatoryFiling": [True, True]
            })
        }

        with patch('pandas.read_excel', return_value=mock_dataframes):
            result = processor.process_file("/fake/path/file.xlsx")

        assert "withholding_rules" in result
        assert "composite_rules" in result
        assert "validation_issues" in result
        assert len(result["withholding_rules"]) == 2
        assert len(result["composite_rules"]) == 2