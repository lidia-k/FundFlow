# Recent Changes to FundFlow

## File Validation and Preview Enhancement (Latest)

### Key Improvements
- **Immediate Upload Validation**: Files are now validated before any database entries are created, preventing corruption from invalid data
- **File Preview Modal**: Users can click on filenames in the Dashboard to preview raw Excel content before processing
- **Enhanced Error Handling**: Detailed validation error messages with row-specific feedback during upload
- **New API Endpoints**: 
  - `/results/{session_id}/file-preview` - Preview raw uploaded Excel content
  - `/results/{session_id}/preview` - Preview processed calculation results

### Technical Changes
- Backend: Enhanced upload.py with early validation, new results.py endpoints
- Frontend: FilePreviewModal component, improved Dashboard interaction, better error display
- Configuration: Updated Claude settings for additional development tools access

### User Experience Impact
- Faster feedback on file validation errors
- Ability to inspect uploaded files before processing
- Clearer error messages with specific row and column information
- Prevents incomplete/corrupted sessions from being created