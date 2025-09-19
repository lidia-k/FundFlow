# Recent Changes

## Code Cleanup (2025-09-19)
- Removed unused service: upload_validation_service.py
- Cleaned up unused imports across API and service files
- Removed unused methods: get_storage_stats, get_rule_set_statistics, validate_entity_types
- Added vulture dependency for dead code detection
- Updated Claude settings to allow vulture commands