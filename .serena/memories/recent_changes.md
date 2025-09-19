# Recent Changes

## SALT Rules Validation Improvements (Latest)
- Implemented immediate file validation during upload process
- Added early error reporting to prevent invalid data from reaching database
- Simplified composite rule model by removing optional tax amount fields
- Updated frontend to handle validation failures with proper error messaging
- Removed separate validation endpoint in favor of upfront validation
- Added rule counts to upload response for better user visibility

## Previous Changes
- Enhanced file preview modal with dynamic column detection
- Fixed Dashboard 404 error by adding sessions API endpoint
- Implemented v1.3 format support with flexible column detection
- Completed MVP implementation with all Phase 3.1-3.7 tasks
- Fixed Docker configuration and dependency conflicts