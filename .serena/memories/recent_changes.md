# Recent Changes

## SALT Rules Template Download (Latest)
- Added new API endpoint `/api/template/salt-rules` for downloading SALT matrix template
- Created `salt_matrix_template.xlsx` with Withholding and Composite sheets containing dummy data
- Updated SaltRulesUpload page to use new template download endpoint
- Removed "What Happens Next?" workflow section to simplify upload interface
- Template includes proper formatting, example data, and comprehensive instructions

## Template Format Update (Previous)
- Updated Excel template to v1.3 format with 11 columns
- Changed from quarterly distribution format to state-specific distribution amounts (TX, NM, CO)
- Added exemption flag columns for withholding and composite exemptions per state
- Moved template file location from data/template/ to data/templates/
- Updated UI descriptions to reflect new column requirements
- Fixed Docker networking configuration for backend proxy

## Earlier Changes
- Complete MVP implementation with all core features
- Docker configuration fixes and health checks
- Dynamic column preview and validation improvements
- Sessions API endpoint added