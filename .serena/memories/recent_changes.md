# Recent Changes

## Dynamic Column-Based Rule Parsing Implementation (Latest)
- Refactored Excel processor to support new EY SALT matrix format with dynamic entity type columns
- Replaced hardcoded column mapping with prefix-based column detection system
- Added state name field to database models alongside state abbreviation
- Implemented one-to-many rule conversion (single row to multiple entity-specific rules)
- Simplified validation by removing unused checks for better performance
- Added ADR-0002 documenting state-level data duplication design decision

## Previous Changes
- Implemented immediate file validation during upload process
- Added early error reporting to prevent invalid data from reaching database
- Simplified composite rule model by removing optional tax amount fields
- Updated frontend to handle validation failures with proper error messaging
- Enhanced file preview modal with dynamic column detection
- Fixed Dashboard 404 error by adding sessions API endpoint