# Test Fixtures

This directory contains test files used by the E2E tests.

## Files

- `test_data.xlsx` - Valid Excel file with sample investor data
- `invalid_data.xlsx` - Excel file with validation errors
- `large_data.xlsx` - Large Excel file for size testing

## Creating Test Files

To create actual Excel test files for the E2E tests, you can:

1. Download the template from the running application
2. Fill in test data according to the requirements
3. Save as the appropriate filename

### Sample Test Data Structure

Valid test data should include:
- Investor Name: Test Investor LLC
- Investor Entity Type: LLC
- Investor Tax State: NY
- Fund Code: FUND001
- Period Quarter: Q4
- Period Year: 2023
- Jurisdiction: STATE
- Amount: 100000.00
- Composite Exemption: No
- Withholding Exemption: Exemption

Invalid test data should include validation errors like:
- Missing required fields
- Invalid state codes
- Invalid entity types
- Non-numeric amounts
- Invalid date formats