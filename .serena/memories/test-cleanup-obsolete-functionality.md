# Test Cleanup - Obsolete Functionality Removal

## Overview (Sept 19, 2025)
Comprehensive cleanup of test suite to remove tests for functionality that no longer exists after simplifying SALT rules workflow.

## Tests Removed/Updated

### Completely Removed
- **test_publish_endpoint.py** (279 lines) - Tested `POST /{rule_set_id}/publish` endpoint that was removed

### Simplified/Updated

#### test_list_endpoint.py
- Removed complex filtering tests (status, year, quarter filters)
- Updated to test simplified offset/limit pagination only
- Removed page-based pagination tests
- Updated response schema validation to match new endpoint structure

#### test_salt_matrix_endpoints.py  
- Removed 4 publish-related test methods:
  - `test_publish_endpoint_success()`
  - `test_publish_endpoint_validation_errors_block()`
  - `test_publish_endpoint_not_found()`
  - `test_publish_endpoint_wrong_status()`
- Removed filtering tests that tested removed year/quarter/status filters

#### test_complete_workflow.py
- Complete rewrite (287 lines)
- Removed manual publish steps from workflow tests
- Updated to test auto-publish behavior during upload
- Tests now verify rule sets are automatically active after successful upload
- Workflow changed from: upload → validate → publish → verify
- To: upload → auto-publish → verify

## Technical Changes
- All tests now align with simplified API where rule sets auto-publish on upload
- List endpoint tests only validate basic offset/limit pagination
- No frontend tests affected (no publish functionality existed in frontend tests)
- Tests properly mock the auto-archival of existing active rule sets

## Result
Test suite now accurately reflects current API implementation:
- Rule sets auto-published (status=ACTIVE) on successful upload
- Previous active rule sets automatically archived
- No separate publish endpoint
- Simple pagination without complex filtering