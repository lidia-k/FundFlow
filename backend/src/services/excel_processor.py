"""Excel processing service for SALT rule workbooks with pandas/openpyxl."""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from decimal import Decimal, InvalidOperation
import pandas as pd
from openpyxl import load_workbook

from ..models.validation_issue import ValidationIssue, IssueSeverity
from ..models.withholding_rule import WithholdingRule
from ..models.composite_rule import CompositeRule
from ..models.enums import USJurisdiction, InvestorEntityType

logger = logging.getLogger(__name__)


class ExcelValidationResult:
    """Result of Excel file validation (without processing rules)."""

    def __init__(self, is_valid: bool, errors: List[Dict[str, Any]]):
        self.is_valid = is_valid
        self.errors = errors


class ExcelProcessingResult:
    """Result of Excel processing operation."""

    def __init__(
        self,
        withholding_rules: List[WithholdingRule],
        composite_rules: List[CompositeRule],
        validation_issues: List[ValidationIssue],
        rules_processed: Dict[str, int]
    ):
        self.withholding_rules = withholding_rules
        self.composite_rules = composite_rules
        self.validation_issues = validation_issues
        self.rules_processed = rules_processed


class ExcelProcessor:
    """Service for processing SALT rule Excel workbooks."""

    # Required sheets in the workbook
    REQUIRED_SHEETS = ["Withholding", "Composite"]

    # Required columns for each sheet
    WITHHOLDING_COLUMNS = [
        "State", "EntityType", "TaxRate", "IncomeThreshold", "TaxThreshold"
    ]

    COMPOSITE_COLUMNS = [
        "State", "EntityType", "TaxRate", "IncomeThreshold", "MandatoryFiling"
    ]

    # Valid state codes (from USJurisdiction enum)
    VALID_STATE_CODES = {state.value for state in USJurisdiction}

    # Valid entity type coding values (from InvestorEntityType enum)
    VALID_ENTITY_TYPES = InvestorEntityType.get_unique_codings()

    def __init__(self):
        self.validation_issues: List[ValidationIssue] = []
        self.rule_set_id: Optional[str] = None

    def load_excel_file(self, file_path: Union[str, Path]) -> Dict[str, pd.DataFrame]:
        """Load Excel file and return dataframes for each sheet."""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Excel file not found: {file_path}")

            # Read all sheets using pandas
            dataframes = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')

            # Check for required sheets
            missing_sheets = set(self.REQUIRED_SHEETS) - set(dataframes.keys())
            if missing_sheets:
                raise ValueError(f"Missing required sheets: {missing_sheets}")

            # Clean up dataframes - remove empty rows
            for sheet_name, df in dataframes.items():
                if sheet_name in self.REQUIRED_SHEETS:
                    # Remove rows where all key columns are NaN
                    if sheet_name == "Withholding":
                        df = df.dropna(subset=["State", "EntityType"], how='all')
                    elif sheet_name == "Composite":
                        df = df.dropna(subset=["State", "EntityType"], how='all')

                    dataframes[sheet_name] = df

            logger.info(f"Successfully loaded Excel file with {len(dataframes)} sheets")
            return dataframes

        except Exception as e:
            logger.error(f"Failed to load Excel file {file_path}: {str(e)}")
            raise

    def validate_sheet_structure(self, sheet_name: str, df: pd.DataFrame) -> List[ValidationIssue]:
        """Validate that sheet has required columns."""
        issues = []

        if sheet_name == "Withholding":
            required_columns = self.WITHHOLDING_COLUMNS
        elif sheet_name == "Composite":
            required_columns = self.COMPOSITE_COLUMNS
        else:
            return issues  # Skip validation for non-required sheets

        # Check for missing columns
        missing_columns = set(required_columns) - set(df.columns)
        for column in missing_columns:
            issues.append(ValidationIssue(
                rule_set_id=self.rule_set_id,
                sheet_name=sheet_name,
                row_number=1,  # Header row
                column_name=column,
                error_code="MISSING_COLUMN",
                severity=IssueSeverity.ERROR,
                message=f"Required column '{column}' is missing from {sheet_name} sheet",
                field_value=None
            ))

        return issues

    def validate_data_types(self, sheet_name: str, df: pd.DataFrame) -> List[ValidationIssue]:
        """Validate data types in sheet columns."""
        issues = []

        # Define expected data types per sheet
        if sheet_name == "Withholding":
            numeric_columns = ["TaxRate", "IncomeThreshold", "TaxThreshold"]
            string_columns = ["State", "EntityType"]
        elif sheet_name == "Composite":
            numeric_columns = ["TaxRate", "IncomeThreshold"]
            string_columns = ["State", "EntityType"]
            boolean_columns = ["MandatoryFiling"]
        else:
            return issues

        # Validate numeric columns
        for col in numeric_columns:
            if col not in df.columns:
                continue

            for idx, value in df[col].items():
                if pd.isna(value):
                    continue

                try:
                    float(value)
                except (ValueError, TypeError):
                    issues.append(ValidationIssue(
                        rule_set_id=self.rule_set_id,
                        sheet_name=sheet_name,
                        row_number=idx + 2,  # +2 for 1-indexed and header row
                        column_name=col,
                        error_code="INVALID_DATA_TYPE",
                        severity=IssueSeverity.ERROR,
                        message=f"Invalid numeric value '{value}' in column '{col}'",
                        field_value=str(value)
                    ))

        # Validate string columns
        for col in string_columns:
            if col not in df.columns:
                continue

            for idx, value in df[col].items():
                if pd.isna(value) or value == "":
                    issues.append(ValidationIssue(
                        rule_set_id=self.rule_set_id,
                        sheet_name=sheet_name,
                        row_number=idx + 2,
                        column_name=col,
                        error_code="EMPTY_REQUIRED_FIELD",
                        severity=IssueSeverity.ERROR,
                        message=f"Required field '{col}' is empty",
                        field_value=str(value) if not pd.isna(value) else None
                    ))

        # Validate boolean columns (for Composite sheet)
        if sheet_name == "Composite":
            for col in boolean_columns:
                if col not in df.columns:
                    continue

                for idx, value in df[col].items():
                    if pd.isna(value):
                        continue

                    if not isinstance(value, bool) and str(value).lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
                        issues.append(ValidationIssue(
                            rule_set_id=self.rule_set_id,
                            sheet_name=sheet_name,
                            row_number=idx + 2,
                            column_name=col,
                            error_code="INVALID_DATA_TYPE",
                            severity=IssueSeverity.ERROR,
                            message=f"Invalid boolean value '{value}' in column '{col}'",
                            field_value=str(value)
                        ))

        return issues

    def validate_state_codes(self, sheet_name: str, df: pd.DataFrame) -> List[ValidationIssue]:
        """Validate state codes against USJurisdiction enum."""
        issues = []

        if "State" not in df.columns:
            return issues

        for idx, state_code in df["State"].items():
            if pd.isna(state_code):
                continue

            state_str = str(state_code).strip().upper()
            if state_str not in self.VALID_STATE_CODES:
                issues.append(ValidationIssue(
                    rule_set_id=self.rule_set_id,
                    sheet_name=sheet_name,
                    row_number=idx + 2,
                    column_name="State",
                    error_code="INVALID_STATE",
                    severity=IssueSeverity.ERROR,
                    message=f"Invalid state code '{state_str}'. Must be valid US state abbreviation.",
                    field_value=state_str
                ))

        return issues

    def validate_entity_types(self, sheet_name: str, df: pd.DataFrame) -> List[ValidationIssue]:
        """Validate entity types against InvestorEntityType enum coding values."""
        issues = []

        if "EntityType" not in df.columns:
            return issues

        for idx, entity_type in df["EntityType"].items():
            if pd.isna(entity_type):
                continue

            entity_str = str(entity_type).strip()
            if entity_str not in self.VALID_ENTITY_TYPES:
                issues.append(ValidationIssue(
                    rule_set_id=self.rule_set_id,
                    sheet_name=sheet_name,
                    row_number=idx + 2,
                    column_name="EntityType",
                    error_code="INVALID_ENTITY_TYPE",
                    severity=IssueSeverity.ERROR,
                    message=f"Invalid entity type '{entity_str}'. Must be valid SALT entity type coding.",
                    field_value=entity_str
                ))

        return issues

    def validate_rate_ranges(self, sheet_name: str, df: pd.DataFrame) -> List[ValidationIssue]:
        """Validate tax rate ranges (0.0000 to 1.0000)."""
        issues = []

        if "TaxRate" not in df.columns:
            return issues

        for idx, rate in df["TaxRate"].items():
            if pd.isna(rate):
                continue

            try:
                rate_decimal = Decimal(str(rate))
                if rate_decimal < Decimal('0.0000') or rate_decimal > Decimal('1.0000'):
                    issues.append(ValidationIssue(
                        rule_set_id=self.rule_set_id,
                        sheet_name=sheet_name,
                        row_number=idx + 2,
                        column_name="TaxRate",
                        error_code="INVALID_RATE_RANGE",
                        severity=IssueSeverity.ERROR,
                        message=f"Tax rate {rate_decimal} is outside valid range (0.0000 to 1.0000)",
                        field_value=str(rate_decimal)
                    ))
            except (ValueError, InvalidOperation):
                # This will be caught by data type validation
                pass

        return issues

    def validate_duplicate_rules(self, sheet_name: str, df: pd.DataFrame) -> List[ValidationIssue]:
        """Validate for duplicate state/entity combinations."""
        issues = []

        if "State" not in df.columns or "EntityType" not in df.columns:
            return issues

        # Create composite key for state+entity
        df_clean = df.dropna(subset=["State", "EntityType"])
        df_clean['composite_key'] = df_clean['State'].astype(str) + '+' + df_clean['EntityType'].astype(str)

        # Find duplicates
        duplicates = df_clean[df_clean.duplicated(subset=['composite_key'], keep=False)]

        for idx, row in duplicates.iterrows():
            issues.append(ValidationIssue(
                rule_set_id=self.rule_set_id,
                sheet_name=sheet_name,
                row_number=idx + 2,
                column_name="State+EntityType",
                error_code="DUPLICATE_RULE",
                severity=IssueSeverity.ERROR,
                message=f"Duplicate rule for State '{row['State']}' and EntityType '{row['EntityType']}'",
                field_value=row['composite_key']
            ))

        return issues

    def convert_to_withholding_rule(self, row: pd.Series, rule_set_id: str) -> WithholdingRule:
        """Convert DataFrame row to WithholdingRule model."""
        try:
            state_code = USJurisdiction(str(row['State']).strip().upper())
        except ValueError:
            # Invalid state code - should be caught by validation
            state_code = USJurisdiction.CA  # Default fallback

        return WithholdingRule(
            rule_set_id=rule_set_id,
            state_code=state_code,
            entity_type=str(row['EntityType']).strip(),
            tax_rate=Decimal(str(row['TaxRate'])),
            income_threshold=Decimal(str(row['IncomeThreshold'])),
            tax_threshold=Decimal(str(row['TaxThreshold']))
        )

    def convert_to_composite_rule(self, row: pd.Series, rule_set_id: str) -> CompositeRule:
        """Convert DataFrame row to CompositeRule model."""
        try:
            state_code = USJurisdiction(str(row['State']).strip().upper())
        except ValueError:
            # Invalid state code - should be caught by validation
            state_code = USJurisdiction.CA  # Default fallback

        # Parse boolean value for mandatory filing
        mandatory_filing = False
        if not pd.isna(row['MandatoryFiling']):
            val = str(row['MandatoryFiling']).lower()
            mandatory_filing = val in ['true', '1', 'yes', 'y']

        return CompositeRule(
            rule_set_id=rule_set_id,
            state_code=state_code,
            entity_type=str(row['EntityType']).strip(),
            tax_rate=Decimal(str(row['TaxRate'])),
            income_threshold=Decimal(str(row['IncomeThreshold'])),
            mandatory_filing=mandatory_filing
        )

    def validate_file(self, file_path: Union[str, Path]) -> ExcelValidationResult:
        """Validate Excel file structure and basic content without processing rules."""
        self.validation_issues = []
        self.rule_set_id = "validation"  # Temporary ID for validation

        try:
            # Load Excel file
            dataframes = self.load_excel_file(file_path)

            # Check for missing required sheets first - fail immediately if any are missing
            missing_sheets = set(self.REQUIRED_SHEETS) - set(dataframes.keys())
            if missing_sheets:
                errors = []
                for sheet_name in missing_sheets:
                    errors.append({
                        "sheet": "FILE",
                        "row": 1,
                        "column": None,
                        "error_code": "MISSING_REQUIRED_SHEET",
                        "message": f"Required sheet '{sheet_name}' is missing from the workbook",
                        "field_value": sheet_name
                    })

                logger.error(f"File validation failed: Missing required sheets: {missing_sheets}")
                return ExcelValidationResult(is_valid=False, errors=errors)

            # Validate each required sheet
            for sheet_name in self.REQUIRED_SHEETS:
                df = dataframes[sheet_name]

                # Run all validation checks
                self.validation_issues.extend(self.validate_sheet_structure(sheet_name, df))
                self.validation_issues.extend(self.validate_data_types(sheet_name, df))
                self.validation_issues.extend(self.validate_state_codes(sheet_name, df))
                self.validation_issues.extend(self.validate_entity_types(sheet_name, df))
                self.validation_issues.extend(self.validate_rate_ranges(sheet_name, df))
                self.validation_issues.extend(self.validate_duplicate_rules(sheet_name, df))

            # Convert validation issues to error format
            errors = []
            for issue in self.validation_issues:
                if issue.severity == IssueSeverity.ERROR:
                    errors.append({
                        "sheet": issue.sheet_name,
                        "row": issue.row_number,
                        "column": issue.column_name,
                        "error_code": issue.error_code,
                        "message": issue.message,
                        "field_value": issue.field_value
                    })

            is_valid = len(errors) == 0

            logger.info(f"File validation completed. Valid: {is_valid}, Errors: {len(errors)}")

            return ExcelValidationResult(is_valid=is_valid, errors=errors)

        except Exception as e:
            logger.error(f"File validation failed: {str(e)}")
            return ExcelValidationResult(
                is_valid=False,
                errors=[{
                    "sheet": "FILE",
                    "row": 1,
                    "column": None,
                    "error_code": "VALIDATION_FAILED",
                    "message": f"File validation failed: {str(e)}",
                    "field_value": None
                }]
            )

    def process_file(self, file_path: Union[str, Path], rule_set_id: str = None) -> ExcelProcessingResult:
        """Process complete Excel file and return structured results."""
        self.validation_issues = []
        self.rule_set_id = rule_set_id

        try:
            # Load Excel file
            dataframes = self.load_excel_file(file_path)

            withholding_rules = []
            composite_rules = []
            rules_processed = {"withholding": 0, "composite": 0}

            # Process Withholding sheet
            if "Withholding" in dataframes:
                withholding_df = dataframes["Withholding"]

                # Validate sheet structure and data
                self.validation_issues.extend(self.validate_sheet_structure("Withholding", withholding_df))
                self.validation_issues.extend(self.validate_data_types("Withholding", withholding_df))
                self.validation_issues.extend(self.validate_state_codes("Withholding", withholding_df))
                self.validation_issues.extend(self.validate_entity_types("Withholding", withholding_df))
                self.validation_issues.extend(self.validate_rate_ranges("Withholding", withholding_df))
                self.validation_issues.extend(self.validate_duplicate_rules("Withholding", withholding_df))

                # Convert to WithholdingRule objects if no critical errors
                error_count = sum(1 for issue in self.validation_issues
                                if issue.severity == IssueSeverity.ERROR and issue.sheet_name == "Withholding")

                if error_count == 0 and rule_set_id:
                    for idx, row in withholding_df.iterrows():
                        try:
                            rule = self.convert_to_withholding_rule(row, rule_set_id)
                            withholding_rules.append(rule)
                            rules_processed["withholding"] += 1
                        except Exception as e:
                            self.validation_issues.append(ValidationIssue(
                                rule_set_id=self.rule_set_id,
                                sheet_name="Withholding",
                                row_number=idx + 2,
                                error_code="CONVERSION_ERROR",
                                severity=IssueSeverity.ERROR,
                                message=f"Failed to convert row to WithholdingRule: {str(e)}",
                                field_value=None
                            ))

            # Process Composite sheet
            if "Composite" in dataframes:
                composite_df = dataframes["Composite"]

                # Validate sheet structure and data
                self.validation_issues.extend(self.validate_sheet_structure("Composite", composite_df))
                self.validation_issues.extend(self.validate_data_types("Composite", composite_df))
                self.validation_issues.extend(self.validate_state_codes("Composite", composite_df))
                self.validation_issues.extend(self.validate_entity_types("Composite", composite_df))
                self.validation_issues.extend(self.validate_rate_ranges("Composite", composite_df))
                self.validation_issues.extend(self.validate_duplicate_rules("Composite", composite_df))

                # Convert to CompositeRule objects if no critical errors
                error_count = sum(1 for issue in self.validation_issues
                                if issue.severity == IssueSeverity.ERROR and issue.sheet_name == "Composite")

                if error_count == 0 and rule_set_id:
                    for idx, row in composite_df.iterrows():
                        try:
                            rule = self.convert_to_composite_rule(row, rule_set_id)
                            composite_rules.append(rule)
                            rules_processed["composite"] += 1
                        except Exception as e:
                            self.validation_issues.append(ValidationIssue(
                                rule_set_id=self.rule_set_id,
                                sheet_name="Composite",
                                row_number=idx + 2,
                                error_code="CONVERSION_ERROR",
                                severity=IssueSeverity.ERROR,
                                message=f"Failed to convert row to CompositeRule: {str(e)}",
                                field_value=None
                            ))

            logger.info(f"Excel processing completed. Rules processed: {rules_processed}, "
                       f"Validation issues: {len(self.validation_issues)}")

            return ExcelProcessingResult(
                withholding_rules=withholding_rules,
                composite_rules=composite_rules,
                validation_issues=self.validation_issues,
                rules_processed=rules_processed
            )

        except Exception as e:
            logger.error(f"Excel processing failed: {str(e)}")
            # Add critical error to validation issues
            self.validation_issues.append(ValidationIssue(
                rule_set_id=self.rule_set_id,
                sheet_name="FILE",
                row_number=1,  # Changed from 0 to 1 to satisfy constraint
                error_code="PROCESSING_FAILED",
                severity=IssueSeverity.ERROR,
                message=f"Excel file processing failed: {str(e)}",
                field_value=None
            ))

            return ExcelProcessingResult(
                withholding_rules=[],
                composite_rules=[],
                validation_issues=self.validation_issues,
                rules_processed={"withholding": 0, "composite": 0}
            )