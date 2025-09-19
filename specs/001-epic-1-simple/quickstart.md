# Quickstart Guide: Simple File Upload & Data Validation

**Feature**: Epic 1 - Simple File Upload & Data Validation
**Date**: 2025-09-14
**Prerequisites**: Docker, Docker Compose installed

This guide validates the complete user workflow from Excel upload to data storage following the Unit → Contract → Integration → E2E testing strategy.

## Development Setup

### 1. Environment Preparation
```bash
# Navigate to project root
cd /Users/lidia/FundFlow

# Ensure Docker is running
docker --version
docker-compose --version

# Create required directories
mkdir -p data uploads results logs

# Set permissions for data directories
chmod 755 data uploads results logs
```

### 2. Database Initialization
```bash
# Start services
docker-compose up -d

# Wait for backend to initialize SQLite database
docker-compose logs -f backend

# Verify database creation
ls -la data/
# Should see: fundflow.db

# Verify backend health
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"1.2.0","service":"FundFlow API"}
```

### 3. Frontend Verification
```bash
# Verify frontend is running
curl http://localhost:3000
# Should return HTML page

# Check API connection from frontend
curl http://localhost:8000/api/template
# Should download portfolio_template.xlsx
```

## User Workflow Validation

### Test Scenario 1: Valid File Upload (Happy Path)

**Objective**: Validate complete workflow with properly formatted Excel file

```bash
# 1. Download template
curl -O http://localhost:8000/api/template
# Saves: portfolio_template.xlsx

# 2. Create test file (simulate user editing template)
# Rename to: TestFund_Q3 2024 distribution data.xlsx
# Add valid test data:
# - Investor Name: "Test Pension Fund"
# - Investor Entity Type: "Government Benefit Plan"
# - Investor Tax State: "TX"
# - Distribution TX and NM: 100000.00
# - Distribution CO: 50000.00

# 3. Upload test file
curl -X POST \
  -F "file=@TestFund_Q3 2024 distribution data.xlsx" \
  http://localhost:8000/api/upload \
  | jq '.'

# Expected response:
# {
#   "session_id": "uuid-here",
#   "filename": "TestFund_Q3 2024 distribution data.xlsx",
#   "status": "completed",
#   "message": "File processed successfully",
#   "created_at": "2025-09-14T...",
#   "file_hash": "sha256-hash"
# }

# Save session_id for next steps
SESSION_ID="uuid-from-response"
```

### Test Scenario 2: Progress Tracking

**Objective**: Validate real-time progress reporting

```bash
# Monitor progress during upload (in separate terminal)
while true; do
  curl -s http://localhost:8000/api/progress/$SESSION_ID | jq '.progress_percentage'
  sleep 1
done

# Expected progression: 5 -> 40 -> 70 -> 90 -> 99 -> 100
```

### Test Scenario 3: Results Retrieval

**Objective**: Validate data storage and preview functionality

```bash
# Get complete results
curl http://localhost:8000/api/results/$SESSION_ID | jq '.'

# Expected response structure:
# {
#   "session_id": "uuid",
#   "filename": "TestFund_Q3 2024 distribution data.xlsx",
#   "status": "completed",
#   "progress_percentage": 100,
#   "total_rows": 1,
#   "valid_rows": 1,
#   "summary": {
#     "investors_upserted": 1,
#     "distributions_inserted": 2,
#     "rows_skipped": 0,
#     "error_count": 0,
#     "warning_count": 0
#   },
#   "preview_data": [
#     {
#       "row_number": 2,
#       "fund_code": "TestFund",
#       "period_quarter": "Q3",
#       "period_year": 2024,
#       "investor_name": "Test Pension Fund",
#       "investor_entity_type": "Government Benefit Plan",
#       "investor_tax_state": "TX",
#       "distribution_tx_nm": 100000.00,
#       "distribution_co": 50000.00
#     }
#   ],
#   "validation_errors": []
# }

# Download results Excel
curl -O http://localhost:8000/api/results/$SESSION_ID/download
# Saves: results file with processed data
```

### Test Scenario 4: Database Validation

**Objective**: Verify data persistence in SQLite

```bash
# Access SQLite database
docker-compose exec backend sqlite3 /app/data/fundflow.db

# Verify user session
.headers on
.mode column
SELECT * FROM user_sessions WHERE session_id = '$SESSION_ID';

# Verify investor data
SELECT * FROM investors WHERE session_id = '$SESSION_ID';

# Verify distribution data
SELECT i.investor_name, d.jurisdiction, d.amount
FROM investors i
JOIN distributions d ON i.id = d.investor_id
WHERE i.session_id = '$SESSION_ID';

# Expected results:
# Test Pension Fund | TX_NM | 100000.00
# Test Pension Fund | CO    | 50000.00

.exit
```

### Test Scenario 5: Validation Error Handling

**Objective**: Test error detection and reporting

```bash
# Create invalid test file: InvalidTest_Q5 2024 distribution data.xlsx
# - Invalid quarter (Q5)
# - Invalid entity type ("Invalid Type")
# - Invalid state ("XY")
# - Negative amount (-1000)

# Upload invalid file
curl -X POST \
  -F "file=@InvalidTest_Q5 2024 distribution data.xlsx" \
  http://localhost:8000/api/upload \
  | jq '.'

# Expected response:
# {
#   "session_id": "uuid",
#   "status": "failed_validation",
#   "errors": [
#     {
#       "row_number": 2,
#       "column_name": "Investor Entity Type",
#       "error_code": "INVALID_ENTITY_TYPE",
#       "error_message": "Entity type must be one of: Corporation, Exempt Organization, ...",
#       "severity": "ERROR"
#     }
#   ]
# }

# Download error CSV
SESSION_ID="uuid-from-invalid-response"
curl -O http://localhost:8000/api/results/$SESSION_ID/errors
```

### Test Scenario 6: File Size and Type Validation

**Objective**: Test client and server-side file validation

```bash
# Test oversized file (>10MB)
dd if=/dev/zero of=large_file.xlsx bs=1M count=11

curl -X POST \
  -F "file=@large_file.xlsx" \
  http://localhost:8000/api/upload

# Expected: HTTP 413 - File too large

# Test invalid file type
curl -X POST \
  -F "file=@README.md" \
  http://localhost:8000/api/upload

# Expected: HTTP 415 - Unsupported file type
```

### Test Scenario 7: Duplicate File Detection

**Objective**: Verify idempotency with SHA256 hashing

```bash
# Upload same file twice
curl -X POST \
  -F "file=@TestFund_Q3 2024 distribution data.xlsx" \
  http://localhost:8000/api/upload \
  | jq '.file_hash'

# Save first hash
HASH1="hash-from-first-upload"

curl -X POST \
  -F "file=@TestFund_Q3 2024 distribution data.xlsx" \
  http://localhost:8000/api/upload \
  | jq '.file_hash'

# Verify same hash, no duplicate data insertion
# Check database to confirm investor count didn't increase
```

## Frontend Integration Testing

### Test Scenario 8: Complete UI Workflow

**Objective**: Validate end-to-end user interface

```bash
# Start Playwright tests (when implemented)
cd frontend
npm run test:e2e

# Manual UI validation:
# 1. Open http://localhost:3000
# 2. Click "Download Template" button -> downloads portfolio_template.xlsx
# 3. Drag TestFund_Q3 2024 distribution data.xlsx to upload area
# 4. Verify progress bar shows: 5% -> 40% -> 70% -> 90% -> 99% -> 100%
# 5. Verify data preview shows 1 row with correct values
# 6. Click "Issues" tab -> verify empty (no errors)
# 7. Click "Export Issues" -> downloads empty CSV
```

## Performance Validation

### Test Scenario 9: Large File Processing

**Objective**: Validate performance with maximum file size

```bash
# Create test file with ~10,000 rows (within 50k limit)
# File size should approach but not exceed 10MB

# Time the processing
time curl -X POST \
  -F "file=@LargeFund_Q1 2024 distribution data.xlsx" \
  http://localhost:8000/api/upload

# Verify completion within 30 minutes (actual should be much faster)
# Monitor memory usage during processing
docker stats
```

## Clean Up

### Reset Environment

```bash
# Stop services
docker-compose down

# Clean up test data
rm -f *.xlsx *.csv

# Reset database (optional)
rm -f data/fundflow.db

# Clear logs
rm -f logs/*.log
```

## Success Criteria

### Testing Strategy Implementation:
Following the Unit → Contract → Integration → E2E approach:
- **Unit Tests**: Validation functions, business logic, data transformations
- **Contract Tests**: API specification compliance, request/response formats
- **Integration Tests**: File processing pipeline, database operations
- **E2E Tests**: Complete user workflows via Playwright

### All integration tests must pass:

1. ✅ **File Upload**: Valid Excel files upload successfully
2. ✅ **Progress Tracking**: Real-time progress updates work correctly
3. ✅ **Data Validation**: Business rules enforced correctly
4. ✅ **Error Handling**: Invalid data produces structured error reports
5. ✅ **Data Storage**: Validated data persists correctly in SQLite
6. ✅ **Template Download**: Excel template generates with proper format
7. ✅ **Results Export**: Processed data exports to Excel format
8. ✅ **Error Export**: Validation errors export to CSV format
9. ✅ **File Validation**: Size and type limits enforced
10. ✅ **Idempotency**: Duplicate files detected and handled correctly

### Performance Requirements:
- File processing completes within reasonable time (<5 minutes for typical files)
- Progress updates respond within 1 second
- Database operations complete successfully
- Memory usage remains stable during processing

### User Experience Requirements:
- Upload interface responds immediately to file selection
- Progress feedback is clear and informative
- Error messages are specific and actionable
- Results are presented in organized, readable format

## Troubleshooting

### Common Issues:

**Database Connection Error**:
```bash
# Check SQLite file permissions
ls -la data/fundflow.db
chmod 664 data/fundflow.db
```

**File Upload Timeout**:
```bash
# Check Docker container resources
docker-compose logs backend
# Increase timeout in FastAPI settings if needed
```

**Progress Not Updating**:
```bash
# Verify session ID is correctly returned and used
# Check backend logs for processing errors
```

**Template Download Fails**:
```bash
# Verify template generation logic
# Check file permissions in results directory
```

This quickstart validates all 30 functional requirements from the feature specification through practical testing scenarios.