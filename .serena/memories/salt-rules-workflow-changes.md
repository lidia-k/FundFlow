# SALT Rules Workflow Changes

## Recent Updates (Sept 19, 2025)

### Workflow Simplification
- **Removed draft/pending workflow**: Rule sets are now auto-published on upload
- **Status types**: Only `active` and `archived` statuses remain
- **Auto-archival**: Previous active rule sets are automatically archived when new ones are uploaded

### API Changes
- **Removed**: `POST /{rule_set_id}/publish` endpoint (redundant)
- **Added**: Simplified `GET /salt-rules` list endpoint with pagination
- **Cleaned up**: Removed `PublishRequest` type and unused publish logic

### Frontend Updates
- **Dashboard stats**: "Pending" section replaced with "Archived" 
- **Icon update**: Using `ArchiveBoxIcon` for archived rule sets
- **Status filtering**: Shows proper count of archived vs active rule sets

### Technical Details
- Upload endpoint automatically sets status to `ACTIVE` and `published_at` timestamp
- Previous active rule sets are moved to `ARCHIVED` status during upload
- List endpoint supports pagination with `limit` and `offset` parameters
- Frontend properly filters and displays rule sets by status

This change streamlines the user experience by eliminating unnecessary workflow steps while maintaining data integrity.