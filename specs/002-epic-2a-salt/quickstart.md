# Quickstart: SALT Rules Ingestion & Publishing

**Phase 1 Output** | **Date**: 2025-09-17

## End-to-End Workflow Test

This quickstart validates the complete SALT rules administration workflow from Excel upload through rule set publishing.

### Prerequisites

**Test Environment**:
```bash
# Start development environment
make dev

# Verify services are healthy
docker-compose ps
curl http://localhost:8000/api/health
curl http://localhost:3000/health
```

**Test Data**:
- `data/test_files/ey_salt_rules_2025q1_valid.xlsx` - Valid rule workbook
- `data/test_files/ey_salt_rules_2025q1_errors.xlsx` - Contains validation errors
- Admin credentials for authentication

### Step 1: Upload Valid Rule Workbook

**Objective**: Upload Excel file and initiate validation pipeline

```bash
# Upload valid EY SALT rule workbook
curl -X POST http://localhost:8000/api/salt-rules/upload \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F "file=@data/test_files/ey_salt_rules_2025q1_valid.xlsx" \
  -F "year=2025" \
  -F "quarter=Q1" \
  -F "description=Test upload for 2025 Q1 rules"

# Expected Response (201 Created):
{
  "ruleSetId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "draft",
  "uploadedFile": {
    "id": "file-uuid",
    "filename": "ey_salt_rules_2025q1_valid.xlsx",
    "fileSize": 1048576,
    "sha256Hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
    "uploadTimestamp": "2025-09-17T10:00:00Z"
  },
  "validationStarted": true
}
```

**Validation Criteria**:
- ✅ Status code 201 Created
- ✅ Response contains `ruleSetId`
- ✅ File SHA256 hash computed correctly
- ✅ Rule set status is "draft"

### Step 2: Check Validation Results

**Objective**: Verify validation completed successfully with zero errors

```bash
# Poll validation status (may take 10-30 seconds)
RULE_SET_ID="550e8400-e29b-41d4-a716-446655440000"

curl -X GET "http://localhost:8000/api/salt-rules/$RULE_SET_ID/validation" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected Response (200 OK):
{
  "ruleSetId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "summary": {
    "totalIssues": 0,
    "errorCount": 0,
    "warningCount": 0,
    "rulesProcessed": {
      "withholding": 51,
      "composite": 51
    }
  },
  "issues": [],
  "csvDownloadUrl": "/api/salt-rules/550e8400-e29b-41d4-a716-446655440000/validation.csv"
}
```

**Validation Criteria**:
- ✅ Validation status is "completed"
- ✅ Error count is 0 (no blocking errors)
- ✅ Both withholding and composite rules processed
- ✅ CSV download URL provided

### Step 3: Preview Rule Changes

**Objective**: Compare draft rules against currently active rule set

```bash
# Preview staged rules with diff comparison
curl -X GET "http://localhost:8000/api/salt-rules/$RULE_SET_ID/preview" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected Response (200 OK):
{
  "ruleSetId": "550e8400-e29b-41d4-a716-446655440000",
  "comparison": {
    "added": [
      {
        "ruleType": "withholding",
        "state": "CA",
        "entityType": "corporation",
        "changes": [
          {
            "field": "taxRate",
            "oldValue": null,
            "newValue": "0.0575"
          }
        ]
      }
    ],
    "modified": [
      {
        "ruleType": "composite",
        "state": "NY",
        "entityType": "partnership",
        "changes": [
          {
            "field": "taxRate",
            "oldValue": "0.0625",
            "newValue": "0.0650"
          },
          {
            "field": "incomeThreshold",
            "oldValue": "1000.00",
            "newValue": "1500.00"
          }
        ]
      }
    ],
    "removed": []
  },
  "summary": {
    "rulesAdded": 1,
    "rulesModified": 1,
    "rulesRemoved": 0,
    "fieldsChanged": 3
  }
}
```

**Validation Criteria**:
- ✅ Comparison shows expected rule changes
- ✅ Field-level differences identified
- ✅ Summary counts match detailed changes

### Step 4: Publish Rule Set

**Objective**: Activate rule set for use in calculations

```bash
# Publish rule set (archives any existing active rule set)
curl -X POST "http://localhost:8000/api/salt-rules/$RULE_SET_ID/publish" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "effectiveDate": "2025-01-01",
    "confirmArchive": true
  }'

# Expected Response (200 OK):
{
  "ruleSetId": "550e8400-e29b-41d4-a716-446655440000",
  "status": "active",
  "effectiveDate": "2025-01-01",
  "archivedRuleSet": "previous-rule-set-uuid",
  "resolvedRulesGenerated": 102
}
```

**Validation Criteria**:
- ✅ Rule set status changed to "active"
- ✅ Effective date set correctly
- ✅ Previous rule set archived (if existed)
- ✅ Resolved rules table populated

### Step 5: Verify Active Rule Set

**Objective**: Confirm published rule set is available for calculations

```bash
# List active rule sets
curl -X GET "http://localhost:8000/api/salt-rules?status=active&year=2025&quarter=Q1" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected Response (200 OK):
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "year": 2025,
      "quarter": "Q1",
      "version": "1.0.0",
      "status": "active",
      "effectiveDate": "2025-01-01",
      "publishedAt": "2025-09-17T10:05:00Z",
      "ruleCount": {
        "withholding": 51,
        "composite": 51
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "totalPages": 1
  }
}
```

**Validation Criteria**:
- ✅ Exactly one active rule set for 2025 Q1
- ✅ Published timestamp present
- ✅ Rule counts correct

## Error Handling Test

### Upload File with Validation Errors

**Objective**: Verify validation error detection and reporting

```bash
# Upload file with known validation errors
curl -X POST http://localhost:8000/api/salt-rules/upload \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F "file=@data/test_files/ey_salt_rules_2025q1_errors.xlsx" \
  -F "year=2025" \
  -F "quarter=Q2"

# Get validation results
ERROR_RULE_SET_ID="error-rule-set-uuid"
curl -X GET "http://localhost:8000/api/salt-rules/$ERROR_RULE_SET_ID/validation" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected Response with errors:
{
  "status": "completed",
  "summary": {
    "totalIssues": 3,
    "errorCount": 2,
    "warningCount": 1
  },
  "issues": [
    {
      "sheetName": "Withholding",
      "rowNumber": 15,
      "columnName": "State",
      "errorCode": "INVALID_STATE",
      "severity": "error",
      "message": "Invalid state code 'ZZ' - must be valid US state",
      "fieldValue": "ZZ"
    },
    {
      "sheetName": "Composite",
      "rowNumber": 23,
      "columnName": "TaxRate",
      "errorCode": "INVALID_RATE",
      "severity": "error",
      "message": "Tax rate -0.05 cannot be negative",
      "fieldValue": "-0.05"
    }
  ]
}

# Attempt to publish rule set with errors
curl -X POST "http://localhost:8000/api/salt-rules/$ERROR_RULE_SET_ID/publish" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"effectiveDate": "2025-04-01"}'

# Expected Response (400 Bad Request):
{
  "error": "VALIDATION_ERRORS_PRESENT",
  "message": "Cannot publish rule set with validation errors",
  "details": {
    "errorCount": 2,
    "blockingErrors": [
      "INVALID_STATE",
      "INVALID_RATE"
    ]
  }
}
```

**Validation Criteria**:
- ✅ Validation errors detected and reported
- ✅ Publishing blocked when errors present
- ✅ Error messages include row/sheet context

## Duplicate Detection Test

**Objective**: Verify SHA256-based duplicate file detection

```bash
# Upload same file again for same year/quarter
curl -X POST http://localhost:8000/api/salt-rules/upload \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F "file=@data/test_files/ey_salt_rules_2025q1_valid.xlsx" \
  -F "year=2025" \
  -F "quarter=Q1"

# Expected Response (409 Conflict):
{
  "error": "DUPLICATE_FILE",
  "message": "File with same content already uploaded for 2025 Q1",
  "existingRuleSetId": "550e8400-e29b-41d4-a716-446655440000",
  "duplicateDetection": {
    "sha256Hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
    "uploadedAt": "2025-09-17T10:00:00Z"
  }
}
```

**Validation Criteria**:
- ✅ Duplicate file detected by SHA256 hash
- ✅ Reference to existing rule set provided
- ✅ Appropriate HTTP status code (409)

## Frontend Integration Test

**Objective**: Verify admin interface displays workflow correctly

```bash
# Open admin interface
open http://localhost:3000/admin/salt-rules

# Manual verification steps:
# 1. Navigate to SALT Rules administration page
# 2. Upload test file using drag-drop interface
# 3. Monitor validation progress with real-time updates
# 4. Review validation results in data table
# 5. Preview rule changes in diff view
# 6. Publish rule set with confirmation dialog
# 7. Verify rule set appears in active rules list
```

**Validation Criteria**:
- ✅ File upload with progress indication
- ✅ Validation results displayed in table format
- ✅ CSV export functionality works
- ✅ Rule comparison shows visual diff
- ✅ Publishing confirmation flow
- ✅ Rule set list updates after publishing

## Performance Test

**Objective**: Verify system handles 20MB files within 30 seconds

```bash
# Generate large test file (20MB)
python scripts/generate_large_salt_file.py --size=20MB --output=large_test.xlsx

# Upload and time the process
time curl -X POST http://localhost:8000/api/salt-rules/upload \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F "file=@large_test.xlsx" \
  -F "year=2025" \
  -F "quarter=Q3"

# Monitor validation completion time
start_time=$(date +%s)
while true; do
  response=$(curl -s "http://localhost:8000/api/salt-rules/$RULE_SET_ID/validation")
  status=$(echo $response | jq -r '.status')
  if [ "$status" = "completed" ]; then
    end_time=$(date +%s)
    echo "Validation completed in $((end_time - start_time)) seconds"
    break
  fi
  sleep 2
done
```

**Validation Criteria**:
- ✅ 20MB file upload completes successfully
- ✅ Total processing time under 30 seconds
- ✅ No memory or timeout errors

## Success Criteria

### Functional Requirements Validated
- [x] FR-001: Excel format validation (.xlsx/.xlsm only)
- [x] FR-002: SHA256 duplicate detection
- [x] FR-003: Flexible header normalization
- [x] FR-004: State code and entity type validation
- [x] FR-005: Duplicate state-entity detection
- [x] FR-006: Rate and threshold validation
- [x] FR-007: Detailed validation error reporting
- [x] FR-008: CSV export of validation results
- [x] FR-009: Draft rule set creation
- [x] FR-010: Rule set diff comparison
- [x] FR-011: Publishing blocked on errors
- [x] FR-012: Single active rule set constraint
- [x] FR-013: Resolved rules table generation
- [x] FR-014: Rule set lifecycle tracking
- [x] FR-015: Admin interface functionality
- [x] FR-016: Audit trail maintenance
- [x] FR-017: Year/Quarter versioning
- [x] FR-018: 20MB file size limit
- [x] FR-019: State/entity type mapping
- [x] FR-020: Source file metadata storage

### Performance Requirements
- [x] Upload and validation within 30 seconds for 20MB files
- [x] Support for 3-5 concurrent admin users
- [x] Responsive UI with progress indication

### Error Handling
- [x] Invalid file format rejection
- [x] Validation error collection and reporting
- [x] Duplicate file detection
- [x] Publishing constraints enforcement

### Integration Points
- [x] Backend API endpoints function correctly
- [x] Frontend admin interface integrates seamlessly
- [x] Database operations maintain consistency
- [x] File storage handles uploads securely

---

**Quickstart Status**: ✅ Complete - All test scenarios defined with validation criteria