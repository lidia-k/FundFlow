# Quickstart Guide - Epic 2A SALT Rules Ingestion

## Overview
This guide walks through the complete SALT rules workflow from Excel upload to published rule set, demonstrating all major features and validation scenarios.

## Prerequisites
- FundFlow development environment running (make dev)
- Admin user credentials
- Sample SALT rules Excel workbook (provided in test fixtures)
- Browser with developer tools for API inspection

## Test Scenario: Upload 2025 Q1 SALT Rules

### Step 1: Environment Setup
```bash
# Start development environment
cd /Users/lidia/FundFlow
make dev

# Verify services are healthy
curl http://localhost:8000/api/health
curl http://localhost:3000/health

# Login as admin user (for API token)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@fundflow.test", "password": "admin123"}'
```

**Expected**: All health checks pass, auth token received

### Step 2: Access Admin SALT Rules UI
1. Navigate to http://localhost:3000/admin/salt-rules
2. Verify admin authentication required
3. Login with admin credentials
4. See empty rule sets list (initially)

**Expected**: Admin dashboard loads with upload interface

### Step 3: Upload Valid SALT Rules Workbook
1. Use file picker or drag-drop interface
2. Select test file: `fixtures/excel/valid_salt_rules_2025_q1.xlsx`
3. Set Year: 2025, Quarter: Q1
4. Click "Upload and Parse"
5. Monitor progress indicator

**Expected**:
- File uploads successfully
- Parsing completes without errors
- Draft rule set created with ID
- Navigation to rule set detail page

### Step 4: Review Validation Results
1. Check validation summary:
   - Total issues: 0 errors, 2 warnings
   - Can publish: true
2. Download validation report as CSV
3. Review specific warnings (e.g., coverage gaps)

**Expected**:
- Validation issues displayed in filterable grid
- CSV export contains warning details
- Publish button enabled (no blocking errors)

### Step 5: Preview Parsed Rules
1. Navigate to "Preview" tab
2. Filter by rule type: Withholding
3. Search for specific state: CA
4. Review parsed rule data:
   - State: CA, Entity: INDIVIDUAL
   - Rate: 5.75% (0.0575)
   - Income Threshold: $1,000,000
   - Tax Threshold: $57,500

**Expected**:
- Rules display correctly parsed values
- Filtering and search work properly
- Pagination handles large rule sets

### Step 6: Compare with Active Rules (if exists)
1. Navigate to "Diff" tab
2. Review changes vs current active rule set:
   - Added: 15 new rules
   - Changed: 8 rate updates
   - Removed: 2 obsolete rules
3. Drill down into specific changes

**Expected**:
- Diff accurately shows all changes
- Field-level differences highlighted
- Summary counts match detailed changes

### Step 7: Publish Rule Set
1. Return to rule set overview
2. Click "Publish Rule Set"
3. Confirm publication in modal dialog
4. Wait for processing completion
5. Verify status change to "active"

**Expected**:
- Publication succeeds atomically
- Previous active rule set archived (if exists)
- Resolved rules table generated
- Audit log entry created

### Step 8: Verify Published Rules
1. Check rule set list shows new active rule set
2. Verify effective dates:
   - New: 2025-01-01 to null
   - Previous: 2024-10-01 to 2024-12-31
3. Test calculation engine API:
```bash
# Get active rule set
curl http://localhost:8000/api/salt-rules/active

# Get resolved rules for CA INDIVIDUAL
curl "http://localhost:8000/api/salt-rules/resolved/123?state_code=CA&entity_type_code=INDIVIDUAL"
```

**Expected**:
- API returns active rule set data
- Resolved rules contain both withholding and composite data
- Provenance IDs trace back to source rules

## Error Scenarios

### Scenario A: Invalid File Upload
1. Attempt to upload `.pdf` file
2. Verify error: "UNSUPPORTED_FILE_TYPE"
3. Try oversized file (>20MB)
4. Verify error: "FILE_TOO_LARGE"

### Scenario B: Missing Required Sheets
1. Upload Excel with only "Withholding" sheet
2. Verify error: "MISSING_SHEET: Composite sheet required"
3. Cannot proceed to staging phase

### Scenario C: Data Validation Errors
1. Upload file with invalid state code "XX"
2. Review validation issues:
   - Row 5, Withholding sheet
   - Error: "UNKNOWN_REFERENCE: Unknown state code: XX"
3. Verify publish button disabled
4. Export errors as CSV for correction

### Scenario D: Duplicate Upload Detection
1. Upload same file again for 2025 Q1
2. Verify response: "IDEMPOTENT_NOOP"
3. No new rule set created
4. Banner shows existing rule set link

### Scenario E: Publication Conflict
1. Create two draft rule sets for same period
2. Publish first one successfully
3. Attempt to publish second one
4. Verify error unless force_archive_active=true

## API Testing Checklist

### Upload API
```bash
# Valid upload
curl -X POST http://localhost:8000/api/admin/salt-rules/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@fixtures/excel/valid_salt_rules_2025_q1.xlsx" \
  -F "year=2025" \
  -F "quarter=Q1"

# Expected: 201 Created with rule set details
```

### Validation Issues API
```bash
# Get all issues
curl http://localhost:8000/api/admin/salt-rules/123/validation-issues \
  -H "Authorization: Bearer $TOKEN"

# Get only errors as CSV
curl "http://localhost:8000/api/admin/salt-rules/123/validation-issues?severity=error&format=csv" \
  -H "Authorization: Bearer $TOKEN"
```

### Preview API
```bash
# Get withholding rules for CA
curl "http://localhost:8000/api/admin/salt-rules/123/preview?rule_type=withholding&state_code=CA" \
  -H "Authorization: Bearer $TOKEN"
```

### Diff API
```bash
# Compare with active
curl http://localhost:8000/api/admin/salt-rules/123/diff \
  -H "Authorization: Bearer $TOKEN"
```

### Publish API
```bash
# Publish rule set
curl -X POST http://localhost:8000/api/admin/salt-rules/123/publish \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force_archive_active": false}'
```

### Engine APIs
```bash
# Get active rule set
curl http://localhost:8000/api/salt-rules/active

# Get resolved rules
curl http://localhost:8000/api/salt-rules/resolved/123
```

## Performance Validation

### Large File Handling
1. Upload file with 2000+ rules
2. Verify processing completes within 30 minutes
3. Monitor memory usage during parsing
4. Check database query performance

### Concurrent Access
1. Multiple admin users access same rule set
2. Verify data consistency
3. Test optimistic locking on status changes

### Query Performance
1. Measure resolved rules lookup time
2. Should be <2 seconds for any query
3. Test with full production data volume

## Success Criteria

✅ **File Upload**: Excel files parsed correctly, validation errors caught
✅ **Data Integrity**: All rules stored accurately in database
✅ **Validation**: Comprehensive error detection with clear messages
✅ **Versioning**: Draft→Active workflow with proper archiving
✅ **Performance**: Large files processed within time constraints
✅ **API Contract**: All endpoints match OpenAPI specification
✅ **User Experience**: Intuitive admin interface with progress feedback
✅ **Audit Trail**: Complete logging of all operations
✅ **Calculation Ready**: Resolved rules table optimized for Epic 2B

## Troubleshooting

### Common Issues
- **Upload timeout**: Check file size limit and network connectivity
- **Validation stuck**: Review Excel file format and required sheets
- **Publish failed**: Verify no blocking validation errors exist
- **Performance slow**: Check database indexes and query optimization

### Debug Commands
```bash
# Check backend logs
docker-compose logs backend

# Database inspection
sqlite3 backend/data/fundflow.db ".tables"
sqlite3 backend/data/fundflow.db "SELECT * FROM salt_rule_sets ORDER BY id DESC LIMIT 5;"

# File system check
ls -la backend/uploads/salt_rules/

# Process monitoring
htop  # Check memory/CPU usage during processing
```