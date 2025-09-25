#!/usr/bin/env python3
"""Create test Excel files for fund source data testing."""

from pathlib import Path

import pandas as pd


def create_test_excel_files():
    """Create test Excel files with various scenarios."""

    test_data_dir = Path(__file__).parent

    # Main sheet data (common for all test files)
    main_sheet_data = {
        "Investor Name": ["Alpha Partners LP", "Beta Investment LLC", "Gamma Fund Inc"],
        "Investor Entity Type": ["Partnership", "LLC", "Corporation"],
        "Investor Tax State": ["TX", "CA", "NY"],
        "Commitment Percentage": [25.5, 30.0, 44.5],
        "Distribution TX": [100000.00, 150000.00, 200000.00],
        "Distribution CA": [50000.00, 75000.00, 100000.00],
        "TX Withholding Exemption": ["", "X", ""],
        "CA Withholding Exemption": ["X", "", "X"],
        "TX Composite Exemption": ["", "", "X"],
        "CA Composite Exemption": ["X", "X", ""],
    }

    # Test file 1: Valid fund source data
    fund_source_data_valid = {
        "Company": ["TechCorp Inc", "MedDevice LLC", "FinanceGroup LP", "TechCorp Inc"],
        "State": ["TX", "CA", "NY", "CA"],
        "Share (%)": [45.5, 25.0, 15.5, 14.0],
        "Distribution": [500000.00, 300000.00, 200000.00, 150000.00],
    }

    filename1 = (
        test_data_dir / "(Input Data) Fund A_Q1 2025 distribution data_v1.3.xlsx"
    )
    with pd.ExcelWriter(filename1, engine="openpyxl") as writer:
        pd.DataFrame(main_sheet_data).to_excel(writer, sheet_name="Sheet1", index=False)
        pd.DataFrame(fund_source_data_valid).to_excel(
            writer, sheet_name="Fund Source Data", index=False
        )

    # Test file 2: Invalid fund source data (duplicates, invalid percentages)
    fund_source_data_invalid = {
        "Company": [
            "TechCorp Inc",
            "TechCorp Inc",  # Duplicate company/state
            "MedDevice LLC",
            "BadCompany",
        ],
        "State": ["TX", "TX", "ZZ", "CA"],  # Duplicate company/state  # Invalid state
        "Share (%)": [
            120.0,  # Invalid percentage > 100
            25.0,
            -5.0,  # Invalid negative percentage
            "invalid",  # Invalid format
        ],
        "Distribution": [
            500000.00,
            300000.00,
            -100000.00,  # Invalid negative amount
            0.00,  # Invalid zero amount
        ],
    }

    filename2 = (
        test_data_dir / "(Input Data) Fund B_Q2 2025 distribution data_v1.3.xlsx"
    )
    with pd.ExcelWriter(filename2, engine="openpyxl") as writer:
        pd.DataFrame(main_sheet_data).to_excel(writer, sheet_name="Sheet1", index=False)
        pd.DataFrame(fund_source_data_invalid).to_excel(
            writer, sheet_name="Fund Source Data", index=False
        )

    # Test file 3: Missing fund source data headers
    fund_source_data_missing_headers = {
        "CompanyName": ["TechCorp Inc"],  # Wrong header name
        "State": ["TX"],
        "Percentage": [45.5],  # Wrong header name
        # Missing Distribution column
    }

    filename3 = (
        test_data_dir / "(Input Data) Fund C_Q3 2025 distribution data_v1.3.xlsx"
    )
    with pd.ExcelWriter(filename3, engine="openpyxl") as writer:
        pd.DataFrame(main_sheet_data).to_excel(writer, sheet_name="Sheet1", index=False)
        pd.DataFrame(fund_source_data_missing_headers).to_excel(
            writer, sheet_name="Fund Source Data", index=False
        )

    # Test file 4: Single sheet (backward compatibility)
    filename4 = (
        test_data_dir / "(Input Data) Fund D_Q4 2025 distribution data_v1.3.xlsx"
    )
    with pd.ExcelWriter(filename4, engine="openpyxl") as writer:
        pd.DataFrame(main_sheet_data).to_excel(writer, sheet_name="Sheet1", index=False)

    # Test file 5: Empty fund source data sheet
    filename5 = (
        test_data_dir / "(Input Data) Fund E_Q1 2024 distribution data_v1.3.xlsx"
    )
    with pd.ExcelWriter(filename5, engine="openpyxl") as writer:
        pd.DataFrame(main_sheet_data).to_excel(writer, sheet_name="Sheet1", index=False)
        pd.DataFrame(
            {"Company": [], "State": [], "Share (%)": [], "Distribution": []}
        ).to_excel(writer, sheet_name="Fund Source Data", index=False)

    print("Test Excel files created successfully!")
    print(f"Files created in: {test_data_dir}")

    # List created files
    for xlsx_file in test_data_dir.glob("*.xlsx"):
        print(f"  - {xlsx_file.name}")


if __name__ == "__main__":
    create_test_excel_files()
