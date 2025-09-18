# Recent FundFlow Changes

## Latest Changes (2025-09-19)
**feat(salt-rules): implement auto-detection and UI improvements**

### Key Improvements
- **Auto-Detection**: Upload endpoint now automatically detects year/quarter from current date
- **Simplified API**: Removed manual year/quarter form parameters from upload process
- **Database Fixes**: Fixed constraint violations by updating row_number validation
- **UI Enhancements**: Updated dashboard to use correct status values (draft/active/archived)
- **Better Error Handling**: Improved error messages and display in frontend dashboard

### Technical Changes
- Backend: Enhanced upload API, fixed validation service constraints, improved file service enum handling
- Frontend: Updated dashboard status mapping, improved error display, corrected type definitions
- Testing: Added comprehensive SALT matrix test files and integration tests

### User Experience Impact
- Streamlined upload process with automatic date detection
- More accurate status displays in dashboard
- Better error feedback during operations

## Previous Commit: dc92cb8 (2025-09-19)
**feat(core): implement session deletion and file upload improvements**

### Backend Changes
- Removed file hash deduplication system from upload workflow
- Added session deletion API endpoint (`DELETE /sessions/{session_id}`) with cascade delete
- Enhanced Excel service with improved composite exemption column detection
- Removed redundant file-preview endpoint from results API
- Updated session service to handle session deletion with related data cleanup

### Frontend Changes  
- Added DeleteConfirmationModal component for session management
- Updated API client with session delete capability
- Improved dashboard session handling

### Data Updates
- Added new sample data file in v1.3 Excel format for testing
- Updated CSV sample data format

### Development Tools
- Added MCP tool configurations (codex-cli, bash source commands)

The branch is now ahead of origin by 1 commit and ready for push if needed.