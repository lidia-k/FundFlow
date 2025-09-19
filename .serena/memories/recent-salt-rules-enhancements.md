# Recent SALT Rules Enhancements

## Rule Set Deletion Feature (Commit 24c8819)

### Backend Changes
- **DELETE endpoint**: Added `/salt-rules/{rule_set_id}` endpoint with status validation
- **Data consistency**: Improved handling of duplicate filepath conflicts in FileService
- **Cascade deletion**: Proper cleanup of source files when deleting rule sets
- **Pydantic models**: Fixed response model with field aliases for camelCase frontend compatibility

### Frontend Changes  
- **Delete UI**: Added trash icon for non-active rule sets in dashboard
- **Confirmation modal**: Implemented warning dialog with rule set details
- **API integration**: Added delete method to saltRules API client

### Key Features
- Only draft/archived rule sets can be deleted (active rule sets protected)
- Proper error handling and user feedback
- Clean cascade deletion of associated data
- Enhanced logging for debugging file operations

### Technical Details
- Uses RuleSetService for business logic
- Handles unique constraint violations on file paths
- Responsive delete confirmation with loading states
- Maintains data integrity through transaction management