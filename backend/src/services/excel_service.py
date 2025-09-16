"""Excel file validation and parsing service."""

import re
import hashlib
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from ..models.validation_error import ErrorSeverity


class ExcelValidationError:
    """Represents a validation error found in Excel processing."""

    def __init__(
        self,
        row_number: int,
        column_name: str,
        error_code: str,
        error_message: str,
        severity: ErrorSeverity,
        field_value: Optional[str] = None
    ):
        self.row_number = row_number
        self.column_name = column_name
        self.error_code = error_code
        self.error_message = error_message
        self.severity = severity
        self.field_value = field_value


class ExcelParsingResult:
    """Result of Excel parsing operation."""

    def __init__(
        self,
        data: List[Dict[str, Any]],
        errors: List[ExcelValidationError],
        fund_info: Dict[str, str],
        total_rows: int,
        valid_rows: int
    ):
        self.data = data
        self.errors = errors
        self.fund_info = fund_info
        self.total_rows = total_rows
        self.valid_rows = valid_rows


class ExcelService:
    """Service for Excel file validation and parsing."""

    # Required column headers
    REQUIRED_HEADERS = [
        "Investor Name",
        "Investor Entity Type",
        "Investor Tax State",
        "Distribution \\nTX and NM",
        "Distribution \\nCO",
        "CO Composite Exemption",
        "CO Withholding Exemption",
        "NM Composite Exemption",
        "NM Withholding Exemption"
    ]

    # Valid entity types
    VALID_ENTITY_TYPES = {
        "Corporation",
        "Exempt Organization",
        "Government Benefit Plan",
        "Individual",
        "Joint Tenancy / Tenancy in Common",
        "LLC_Taxed as Partnership",
        "LLP",
        "Limited Partnership",
        "Partnership",
        "Trust"
    }

    # Valid US state codes
    VALID_STATE_CODES = {
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"
    }

    def __init__(self):
        self.errors: List[ExcelValidationError] = []

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def extract_fund_info_from_filename(self, filename: str) -> Optional[Dict[str, str]]:
        """Extract fund code, quarter, and year from filename."""
        pattern = r"^(.+)_Q([1-4]) (\d{4}) distribution data\.(xlsx|xls)$"
        match = re.match(pattern, filename)

        if not match:
            return None

        fund_code, quarter, year, extension = match.groups()
        return {
            "fund_code": fund_code.strip(),
            "period_quarter": f"Q{quarter}",
            "period_year": year,
            "file_extension": extension
        }

    def validate_file_size(self, file_path: Path) -> bool:
        """Validate file size (max 10MB)."""
        file_size = file_path.stat().st_size
        max_size = 10 * 1024 * 1024  # 10MB

        if file_size > max_size:
            self.errors.append(ExcelValidationError(
                row_number=0,
                column_name="file",
                error_code="FILE_SIZE_EXCEEDED",
                error_message=f"File size {file_size} bytes exceeds 10MB limit",
                severity=ErrorSeverity.ERROR
            ))
            return False
        return True

    def normalize_header(self, header: str) -> str:
        """Normalize header by trimming and collapsing whitespace."""
        return re.sub(r'\s+', ' ', str(header).strip())

    def validate_headers(self, df: pd.DataFrame) -> bool:
        """Validate that all required headers are present."""
        normalized_headers = [self.normalize_header(col) for col in df.columns]

        missing_headers = []
        for required_header in self.REQUIRED_HEADERS:
            normalized_required = self.normalize_header(required_header)
            if normalized_required not in normalized_headers:
                missing_headers.append(required_header)

        if missing_headers:
            for header in missing_headers:
                self.errors.append(ExcelValidationError(
                    row_number=0,
                    column_name=header,
                    error_code="MISSING_HEADER",
                    error_message=f"Required column header '{header}' is missing",
                    severity=ErrorSeverity.ERROR
                ))
            return False
        return True

    def parse_numeric_value(self, value: Any, column_name: str, row_num: int) -> Decimal:
        """Parse numeric value with thousands separators and parentheses."""
        if pd.isna(value) or value == "":
            return Decimal('0.00')

        str_value = str(value).strip()

        # Handle parentheses (negative values - which are invalid)
        if str_value.startswith('(') and str_value.endswith(')'):
            self.errors.append(ExcelValidationError(
                row_number=row_num,
                column_name=column_name,
                error_code="NEGATIVE_AMOUNT",
                error_message=f"Negative amount {str_value} is not allowed",
                severity=ErrorSeverity.ERROR,
                field_value=str_value
            ))
            return Decimal('0.00')

        # Remove thousands separators and spaces
        cleaned_value = re.sub(r'[,\s]', '', str_value)

        try:
            return Decimal(cleaned_value)
        except (InvalidOperation, ValueError):
            self.errors.append(ExcelValidationError(
                row_number=row_num,
                column_name=column_name,
                error_code="INVALID_NUMBER_FORMAT",
                error_message=f"Invalid number format: {str_value}",
                severity=ErrorSeverity.ERROR,
                field_value=str_value
            ))
            return Decimal('0.00')

    def parse_exemption_value(self, value: Any) -> bool:
        """Parse exemption field value to boolean."""
        if pd.isna(value) or value == "":
            return False

        str_value = str(value).strip().lower()
        return str_value == "exemption"

    def validate_row_data(self, row_data: Dict[str, Any], row_num: int) -> bool:
        """Validate individual row data."""
        is_valid = True

        # Validate investor name
        investor_name = str(row_data.get('Investor Name', '')).strip()
        if not investor_name:
            self.errors.append(ExcelValidationError(
                row_number=row_num,
                column_name='Investor Name',
                error_code="EMPTY_FIELD",
                error_message="Investor Name cannot be empty",
                severity=ErrorSeverity.ERROR
            ))
            is_valid = False

        # Validate entity type
        entity_type = str(row_data.get('Investor Entity Type', '')).strip()
        if entity_type not in self.VALID_ENTITY_TYPES:
            self.errors.append(ExcelValidationError(
                row_number=row_num,
                column_name='Investor Entity Type',
                error_code="INVALID_ENTITY_TYPE",
                error_message=f"Invalid entity type: {entity_type}",
                severity=ErrorSeverity.ERROR,
                field_value=entity_type
            ))
            is_valid = False

        # Validate tax state
        tax_state = str(row_data.get('Investor Tax State', '')).strip().upper()
        if tax_state not in self.VALID_STATE_CODES:
            self.errors.append(ExcelValidationError(
                row_number=row_num,
                column_name='Investor Tax State',
                error_code="INVALID_STATE_CODE",
                error_message=f"Invalid state code: {tax_state}",
                severity=ErrorSeverity.ERROR,
                field_value=tax_state
            ))
            is_valid = False

        # Parse and validate distribution amounts
        tx_nm_amount = self.parse_numeric_value(
            row_data.get('Distribution \\nTX and NM'), 'Distribution TX and NM', row_num
        )
        co_amount = self.parse_numeric_value(
            row_data.get('Distribution \\nCO'), 'Distribution CO', row_num
        )

        # At least one distribution must be > 0
        if tx_nm_amount <= 0 and co_amount <= 0:
            self.errors.append(ExcelValidationError(
                row_number=row_num,
                column_name='Distribution Amounts',
                error_code="ZERO_DISTRIBUTIONS",
                error_message="At least one distribution amount must be greater than 0",
                severity=ErrorSeverity.ERROR
            ))
            is_valid = False

        return is_valid

    def parse_excel_file(self, file_path: Path, original_filename: str) -> ExcelParsingResult:
        """Parse Excel file and validate data."""
        self.errors = []  # Reset errors

        # Validate file size
        if not self.validate_file_size(file_path):
            return ExcelParsingResult([], self.errors, {}, 0, 0)

        # Extract fund info from filename
        fund_info = self.extract_fund_info_from_filename(original_filename)
        if not fund_info:
            self.errors.append(ExcelValidationError(
                row_number=0,
                column_name="filename",
                error_code="INVALID_FILENAME",
                error_message=f"Filename '{original_filename}' does not match required pattern",
                severity=ErrorSeverity.ERROR
            ))
            return ExcelParsingResult([], self.errors, {}, 0, 0)

        try:
            # Read Excel file (first worksheet)
            df = pd.read_excel(file_path, sheet_name=0)

            # Check row limit
            if len(df) > 50000:
                self.errors.append(ExcelValidationError(
                    row_number=0,
                    column_name="file",
                    error_code="ROW_LIMIT_EXCEEDED",
                    error_message=f"File has {len(df)} rows, exceeding 50,000 row limit",
                    severity=ErrorSeverity.ERROR
                ))
                return ExcelParsingResult([], self.errors, fund_info, len(df), 0)

            # Validate headers
            if not self.validate_headers(df):
                return ExcelParsingResult([], self.errors, fund_info, len(df), 0)

            # Normalize column names
            df.columns = [self.normalize_header(col) for col in df.columns]

            # Process each row
            valid_data = []
            valid_row_count = 0

            for idx, row in df.iterrows():
                row_num = idx + 2  # Excel row number (1-indexed + header)
                row_data = row.to_dict()

                if self.validate_row_data(row_data, row_num):
                    # Parse and clean data
                    parsed_row = {
                        'investor_name': str(row_data['Investor Name']).strip(),
                        'investor_entity_type': str(row_data['Investor Entity Type']).strip(),
                        'investor_tax_state': str(row_data['Investor Tax State']).strip().upper(),
                        'distribution_tx_nm': self.parse_numeric_value(
                            row_data['Distribution TX and NM'], 'Distribution TX and NM', row_num
                        ),
                        'distribution_co': self.parse_numeric_value(
                            row_data['Distribution CO'], 'Distribution CO', row_num
                        ),
                        'co_composite_exemption': self.parse_exemption_value(
                            row_data['CO Composite Exemption']
                        ),
                        'co_withholding_exemption': self.parse_exemption_value(
                            row_data['CO Withholding Exemption']
                        ),
                        'nm_composite_exemption': self.parse_exemption_value(
                            row_data['NM Composite Exemption']
                        ),
                        'nm_withholding_exemption': self.parse_exemption_value(
                            row_data['NM Withholding Exemption']
                        ),
                        'row_number': row_num
                    }
                    valid_data.append(parsed_row)
                    valid_row_count += 1

            return ExcelParsingResult(
                data=valid_data,
                errors=self.errors,
                fund_info=fund_info,
                total_rows=len(df),
                valid_rows=valid_row_count
            )

        except Exception as e:
            self.errors.append(ExcelValidationError(
                row_number=0,
                column_name="file",
                error_code="FAILED_PARSING",
                error_message=f"Failed to parse Excel file: {str(e)}",
                severity=ErrorSeverity.ERROR
            ))
            return ExcelParsingResult([], self.errors, fund_info or {}, 0, 0)