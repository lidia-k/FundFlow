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

    # Required base columns for each sheet
    WITHHOLDING_BASE_COLUMNS = ["State", "State Abbrev"]
    COMPOSITE_BASE_COLUMNS = ["State", "State Abbrev"]

    # Column prefixes for entity types and special columns
    WITHHOLDING_ENTITY_PREFIX = "NONRESIDENT / CORPORATE WITHHOLDING_"
    COMPOSITE_ENTITY_PREFIX = "Composite Rates_"

    # Special columns to extract (constructed from prefixes)
    WITHHOLDING_INCOME_THRESHOLD_COL = WITHHOLDING_ENTITY_PREFIX + "Per Partner Income Threshold"
    WITHHOLDING_TAX_THRESHOLD_COL = WITHHOLDING_ENTITY_PREFIX + "Per Partner W/H Tax Threshold"
    COMPOSITE_INCOME_THRESHOLD_COL = COMPOSITE_ENTITY_PREFIX + "Income Threshold"
    COMPOSITE_MANDATORY_FILING_COL = COMPOSITE_ENTITY_PREFIX + "Mandatory Composite"

    # Columns to ignore (constructed from prefixes)
    WITHHOLDING_IGNORED_COL = WITHHOLDING_ENTITY_PREFIX + "Aggregate Income Threshold"
    COMPOSITE_IGNORED_COL = COMPOSITE_ENTITY_PREFIX + "Inclusion in the composite exempts the partner from withholding"

    # Valid state codes (from USJurisdiction enum)
    VALID_STATE_CODES = {state.value for state in USJurisdiction}

    # Valid entity type coding values (from InvestorEntityType enum)
    VALID_ENTITY_TYPES = InvestorEntityType.get_unique_codings()

    def __init__(self):
        self.validation_issues: List[ValidationIssue] = []
        self.rule_set_id: Optional[str] = None

    def get_entity_type_columns(self, sheet_name: str, df: pd.DataFrame) -> Dict[str, str]:
        """Extract entity type columns and map them to coding values.

        Returns:
            Dict mapping column names to entity type coding values
        """
        entity_columns = {}

        if sheet_name == "Withholding":
            prefix = self.WITHHOLDING_ENTITY_PREFIX
            special_cols = [self.WITHHOLDING_INCOME_THRESHOLD_COL, self.WITHHOLDING_TAX_THRESHOLD_COL, self.WITHHOLDING_IGNORED_COL]
        elif sheet_name == "Composite":
            prefix = self.COMPOSITE_ENTITY_PREFIX
            special_cols = [self.COMPOSITE_INCOME_THRESHOLD_COL, self.COMPOSITE_MANDATORY_FILING_COL, self.COMPOSITE_IGNORED_COL]
        else:
            return entity_columns

        # Find columns with the entity prefix
        for col in df.columns:
            if col.startswith(prefix):
                if col in special_cols:
                    continue

                # Extract entity type from column name
                entity_display = col[len(prefix):]

                # Map to entity type coding value
                if entity_display not in self.VALID_ENTITY_TYPES:
                    raise ValueError(f"Invalid entity type '{entity_display}' found in column '{col}' of {sheet_name} sheet. Must be one of: {', '.join(self.VALID_ENTITY_TYPES)}")
                else: 
                    entity_columns[col] = entity_display

        return entity_columns

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
                    # Remove rows where State and State Abbrev are both NaN
                    df = df.dropna(subset=["State", "State Abbrev"], how='all')
                    dataframes[sheet_name] = df

            logger.info(f"Successfully loaded Excel file with {len(dataframes)} sheets")
            return dataframes

        except Exception as e:
            logger.error(f"Failed to load Excel file {file_path}: {str(e)}")
            raise

    def validate_sheet_structure(self, sheet_name: str, df: pd.DataFrame) -> List[ValidationIssue]:
        """Validate that sheet has required base columns and expected entity type columns."""
        issues = []

        if sheet_name == "Withholding":
            required_base_columns = self.WITHHOLDING_BASE_COLUMNS
            expected_special_columns = [self.WITHHOLDING_INCOME_THRESHOLD_COL, self.WITHHOLDING_TAX_THRESHOLD_COL]
        elif sheet_name == "Composite":
            required_base_columns = self.COMPOSITE_BASE_COLUMNS
            expected_special_columns = [self.COMPOSITE_INCOME_THRESHOLD_COL, self.COMPOSITE_MANDATORY_FILING_COL]
        else:
            return issues  # Skip validation for non-required sheets

        # Check for missing base columns
        missing_base_columns = set(required_base_columns) - set(df.columns)
        for column in missing_base_columns:
            issues.append(ValidationIssue(
                rule_set_id=self.rule_set_id,
                sheet_name=sheet_name,
                row_number=1,  # Header row
                column_name=column,
                error_code="MISSING_BASE_COLUMN",
                severity=IssueSeverity.ERROR,
                message=f"Required base column '{column}' is missing from {sheet_name} sheet",
                field_value=None
            ))

        # Check for missing special columns
        missing_special_columns = set(expected_special_columns) - set(df.columns)
        for column in missing_special_columns:
            issues.append(ValidationIssue(
                rule_set_id=self.rule_set_id,
                sheet_name=sheet_name,
                row_number=1,  # Header row
                column_name=column,
                error_code="MISSING_SPECIAL_COLUMN",
                severity=IssueSeverity.ERROR,
                message=f"Required special column '{column}' is missing from {sheet_name} sheet",
                field_value=None
            ))

        # Check for entity type columns
        entity_columns = self.get_entity_type_columns(sheet_name, df)
        if not entity_columns:
            issues.append(ValidationIssue(
                rule_set_id=self.rule_set_id,
                sheet_name=sheet_name,
                row_number=1,  # Header row
                column_name="Entity Type Columns",
                error_code="NO_ENTITY_COLUMNS",
                severity=IssueSeverity.ERROR,
                message=f"No entity type columns found in {sheet_name} sheet. Expected columns with prefix '{self.WITHHOLDING_ENTITY_PREFIX if sheet_name == 'Withholding' else self.COMPOSITE_ENTITY_PREFIX}'",
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
        """Validate state abbreviations against USJurisdiction enum."""
        issues = []

        if "State Abbrev" not in df.columns:
            return issues

        for idx, state_code in df["State Abbrev"].items():
            if pd.isna(state_code):
                continue

            state_str = str(state_code).strip().upper()
            if state_str not in self.VALID_STATE_CODES:
                issues.append(ValidationIssue(
                    rule_set_id=self.rule_set_id,
                    sheet_name=sheet_name,
                    row_number=idx + 2,
                    column_name="State Abbrev",
                    error_code="INVALID_STATE_ABBREV",
                    severity=IssueSeverity.ERROR,
                    message=f"Invalid state abbreviation '{state_str}'. Must be valid US state abbreviation.",
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

    def convert_row_to_withholding_rules(self, row: pd.Series, rule_set_id: str, df: pd.DataFrame) -> List[WithholdingRule]:
        """Convert DataFrame row to multiple WithholdingRule objects (one per entity type)."""
        rules = []

        # Extract state information
        state_name = str(row['State']).strip()
        state_abbrev = str(row['State Abbrev']).strip().upper()

        try:
            state_code = USJurisdiction(state_abbrev)
        except ValueError:
            # Invalid state code - should be caught by validation
            state_code = USJurisdiction.CA  # Default fallback

        # Extract state-level thresholds
        income_threshold = Decimal('0.00')
        tax_threshold = Decimal('0.00')

        if self.WITHHOLDING_INCOME_THRESHOLD_COL in df.columns:
            income_val = row.get(self.WITHHOLDING_INCOME_THRESHOLD_COL)
            if not pd.isna(income_val):
                try:
                    income_threshold = Decimal(str(income_val))
                except (ValueError, InvalidOperation):
                    pass

        if self.WITHHOLDING_TAX_THRESHOLD_COL in df.columns:
            tax_val = row.get(self.WITHHOLDING_TAX_THRESHOLD_COL)
            if not pd.isna(tax_val):
                try:
                    tax_threshold = Decimal(str(tax_val))
                except (ValueError, InvalidOperation):
                    pass

        # Get entity type columns for this sheet
        entity_columns = self.get_entity_type_columns("Withholding", df)

        # Create a rule for each entity type that has a tax rate
        for col_name, entity_coding in entity_columns.items():
            rate_value = row.get(col_name)
            if not pd.isna(rate_value):
                try:
                    tax_rate = Decimal(str(rate_value))
                    if tax_rate >= Decimal('0.0000'):  # Allow zero rates
                        rules.append(WithholdingRule(
                            rule_set_id=rule_set_id,
                            state=state_name,
                            state_code=state_code,
                            entity_type=entity_coding,
                            tax_rate=tax_rate,
                            income_threshold=income_threshold,
                            tax_threshold=tax_threshold
                        ))
                except (ValueError, InvalidOperation):
                    # Skip invalid rates
                    continue

        return rules

    def convert_row_to_composite_rules(self, row: pd.Series, rule_set_id: str, df: pd.DataFrame) -> List[CompositeRule]:
        """Convert DataFrame row to multiple CompositeRule objects (one per entity type)."""
        rules = []

        # Extract state information
        state_name = str(row['State']).strip()
        state_abbrev = str(row['State Abbrev']).strip().upper()

        try:
            state_code = USJurisdiction(state_abbrev)
        except ValueError:
            # Invalid state code - should be caught by validation
            state_code = USJurisdiction.CA  # Default fallback

        # Extract state-level data
        income_threshold = Decimal('0.00')
        mandatory_filing = False

        if self.COMPOSITE_INCOME_THRESHOLD_COL in df.columns:
            income_val = row.get(self.COMPOSITE_INCOME_THRESHOLD_COL)
            if not pd.isna(income_val):
                try:
                    income_threshold = Decimal(str(income_val))
                except (ValueError, InvalidOperation):
                    pass

        if self.COMPOSITE_MANDATORY_FILING_COL in df.columns:
            mandatory_val = row.get(self.COMPOSITE_MANDATORY_FILING_COL)
            if not pd.isna(mandatory_val):
                val = str(mandatory_val).lower().strip()
                mandatory_filing = val in ['true', '1', 'yes', 'y', 'mandatory']

        # Get entity type columns for this sheet
        entity_columns = self.get_entity_type_columns("Composite", df)

        # Create a rule for each entity type that has a tax rate
        for col_name, entity_coding in entity_columns.items():
            rate_value = row.get(col_name)
            if not pd.isna(rate_value):
                try:
                    tax_rate = Decimal(str(rate_value))
                    if tax_rate >= Decimal('0.0000'):  # Allow zero rates
                        rules.append(CompositeRule(
                            rule_set_id=rule_set_id,
                            state=state_name,
                            state_code=state_code,
                            entity_type=entity_coding,
                            tax_rate=tax_rate,
                            income_threshold=income_threshold,
                            mandatory_filing=mandatory_filing
                        ))
                except (ValueError, InvalidOperation):
                    # Skip invalid rates
                    continue

        return rules

    def validate_file(self, file_path: Union[str, Path]) -> ExcelValidationResult:
        """Validate Excel file structure and basic content without processing rules.

        Fails fast - returns immediately upon first validation error.
        """
        self.validation_issues = []
        self.rule_set_id = "validation"  # Temporary ID for validation

        try:
            # Load Excel file
            dataframes = self.load_excel_file(file_path)

            # Check for missing required sheets first - fail immediately if any are missing
            missing_sheets = set(self.REQUIRED_SHEETS) - set(dataframes.keys())
            if missing_sheets:
                # Return immediately on missing sheets
                sheet_name = list(missing_sheets)[0]  # Get first missing sheet
                error = {
                    "sheet": "FILE",
                    "row": 1,
                    "column": None,
                    "error_code": "MISSING_REQUIRED_SHEET",
                    "message": f"Required sheet '{sheet_name}' is missing from the workbook",
                    "field_value": sheet_name
                }
                logger.error(f"File validation failed: Missing required sheet: {sheet_name}")
                return ExcelValidationResult(is_valid=False, errors=[error])

            # Validate each required sheet - fail fast on first error
            for sheet_name in self.REQUIRED_SHEETS:
                df = dataframes[sheet_name]

                # Check sheet structure first
                structure_issues = self.validate_sheet_structure(sheet_name, df)
                if structure_issues:
                    # Return immediately on first structure error
                    issue = structure_issues[0]
                    error = {
                        "sheet": issue.sheet_name,
                        "row": issue.row_number,
                        "column": issue.column_name,
                        "error_code": issue.error_code,
                        "message": issue.message,
                        "field_value": issue.field_value
                    }
                    logger.error(f"File validation failed: {issue.message}")
                    return ExcelValidationResult(is_valid=False, errors=[error])

                # Check state codes
                state_issues = self.validate_state_codes(sheet_name, df)
                if state_issues:
                    # Return immediately on first state code error
                    issue = state_issues[0]
                    error = {
                        "sheet": issue.sheet_name,
                        "row": issue.row_number,
                        "column": issue.column_name,
                        "error_code": issue.error_code,
                        "message": issue.message,
                        "field_value": issue.field_value
                    }
                    logger.error(f"File validation failed: {issue.message}")
                    return ExcelValidationResult(is_valid=False, errors=[error])

            # If we get here, validation passed
            logger.info("File validation completed successfully")
            return ExcelValidationResult(is_valid=True, errors=[])

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
                self.validation_issues.extend(self.validate_state_codes("Withholding", withholding_df))

                # Convert to WithholdingRule objects if no critical errors
                error_count = sum(1 for issue in self.validation_issues
                                if issue.severity == IssueSeverity.ERROR and issue.sheet_name == "Withholding")

                if error_count == 0 and rule_set_id:
                    for idx, row in withholding_df.iterrows():
                        try:
                            # Convert one row to multiple rules (one per entity type)
                            row_rules = self.convert_row_to_withholding_rules(row, rule_set_id, withholding_df)
                            withholding_rules.extend(row_rules)
                            rules_processed["withholding"] += len(row_rules)
                        except Exception as e:
                            self.validation_issues.append(ValidationIssue(
                                rule_set_id=self.rule_set_id,
                                sheet_name="Withholding",
                                row_number=idx + 2,
                                error_code="CONVERSION_ERROR",
                                severity=IssueSeverity.ERROR,
                                message=f"Failed to convert row to WithholdingRules: {str(e)}",
                                field_value=None
                            ))

            # Process Composite sheet
            if "Composite" in dataframes:
                composite_df = dataframes["Composite"]

                # Validate sheet structure and data
                self.validation_issues.extend(self.validate_sheet_structure("Composite", composite_df))
                self.validation_issues.extend(self.validate_state_codes("Composite", composite_df))

                # Convert to CompositeRule objects if no critical errors
                error_count = sum(1 for issue in self.validation_issues
                                if issue.severity == IssueSeverity.ERROR and issue.sheet_name == "Composite")

                if error_count == 0 and rule_set_id:
                    for idx, row in composite_df.iterrows():
                        try:
                            # Convert one row to multiple rules (one per entity type)
                            row_rules = self.convert_row_to_composite_rules(row, rule_set_id, composite_df)
                            composite_rules.extend(row_rules)
                            rules_processed["composite"] += len(row_rules)
                        except Exception as e:
                            self.validation_issues.append(ValidationIssue(
                                rule_set_id=self.rule_set_id,
                                sheet_name="Composite",
                                row_number=idx + 2,
                                error_code="CONVERSION_ERROR",
                                severity=IssueSeverity.ERROR,
                                message=f"Failed to convert row to CompositeRules: {str(e)}",
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