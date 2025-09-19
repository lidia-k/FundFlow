# SALT Rules System Refactoring

## Recent Changes (2025-09-19)

### Removed Preview/Comparison Functionality
- **ComparisonService**: Deleted 430+ line service that handled rule set comparisons and diff previews
- **RulePreview Component**: Removed React component for previewing rule changes before publishing
- **API Endpoints Removed**:
  - `GET /{rule_set_id}/preview` - Rule set change preview
  - `POST /{rule_set_id}/publish` - Publish rule set with confirmation
  - `GET /` - List rule sets with filtering
- **Simplified API Surface**: Cleaned up unused imports and request models in salt_rules.py

### Impact
- Streamlined SALT rules system by removing draft/preview workflow
- Reduced complexity by ~700 lines of code
- Simplified rule management to direct operations without comparison features
- Removed route `/salt-rules/:ruleSetId/preview` from frontend routing

### Rationale
The preview/comparison functionality was complex and may not have been essential for the MVP workflow. This change focuses the system on core rule upload and management capabilities.