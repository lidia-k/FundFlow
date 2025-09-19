# Research: SALT Rules Ingestion & Publishing

**Phase 0 Output** | **Date**: 2025-09-17

## Excel Processing Research

### Decision: pandas + openpyxl for Excel handling
**Rationale**:
- pandas provides robust data validation and transformation capabilities
- openpyxl offers fine-grained Excel file format support (.xlsx/.xlsm)
- Both libraries are mature, well-documented, and align with TDD v1.2 specifications
- Strong community support and extensive testing coverage

**Alternatives considered**:
- xlrd/xlwt: Limited to .xls format, doesn't support .xlsx/.xlsm
- pyexcel: Additional dependency layer, less direct control
- python-xlsx: Less mature, smaller community

**Implementation approach**:
- Use pandas.read_excel() with openpyxl engine for reading
- Implement flexible header normalization (case-insensitive, whitespace handling)
- Use openpyxl directly for file format validation and metadata extraction

## Validation Strategy Research

### Decision: Multi-layer validation pipeline
**Rationale**:
- Separation of concerns: file format → data structure → business rules
- Structured error collection enables CSV export and detailed user feedback
- Aligns with FR-007 requirement for row/sheet/field-level error reporting

**Validation layers**:
1. **File validation**: Format, size, required sheets presence
2. **Schema validation**: Column headers, data types, required fields
3. **Business validation**: State codes, entity types, duplicate detection
4. **Cross-reference validation**: Foreign key integrity, rate ranges

**Error handling approach**:
- Pydantic models for structured validation
- Custom ValidationError classes with severity levels (error/warning)
- Batch collection of all issues before reporting

## Database Schema Research

### Decision: Separate authoritative tables + resolved view
**Rationale**:
- Maintains data integrity with separate withholding_rules and composite_rules tables
- Resolved rules table provides denormalized view for fast calculation queries
- Supports audit trail and change tracking requirements

**Schema design**:
- `source_files`: SHA256 deduplication, audit trail
- `salt_rule_sets`: Version control by Year/Quarter
- `withholding_rules` & `composite_rules`: Separate normalized tables
- `state_entity_tax_rules_resolved`: Denormalized calculation view

**Performance considerations**:
- Indexes on state_code, entity_type, effective_date for fast lookups
- Materialized view approach for resolved rules table
- Foreign key constraints ensure referential integrity

## File Handling & Security Research

### Decision: SHA256 hashing with secure file storage
**Rationale**:
- SHA256 provides reliable duplicate detection
- File system storage is simpler than blob storage for prototype
- Secure filename generation prevents path traversal attacks

**Security measures**:
- File extension validation (.xlsx/.xlsm only)
- Size limits (20MB) to prevent DoS attacks
- Secure temporary file handling during processing
- Filename sanitization for storage

## State Management Research

### Decision: Draft → Active → Archived lifecycle
**Rationale**:
- Supports preview workflow before publishing
- Enforces single active rule set per Year/Quarter
- Maintains historical data for audit requirements

**State transitions**:
- Draft: Validation passed, ready for review
- Active: Published and available for calculations
- Archived: Replaced by newer rule set, read-only

**Database constraints**:
- Unique constraint on (year, quarter, status='active')
- Check constraints on status transitions
- Cascade rules for dependent data cleanup

## API Design Research

### Decision: RESTful API with file upload endpoint
**Rationale**:
- FastAPI provides excellent file upload handling
- OpenAPI documentation supports admin interface development
- Streaming upload for large files (up to 20MB)

**Endpoint design**:
- POST /api/salt-rules/upload - Multipart file upload with metadata
- GET /api/salt-rules/{id}/validation - Validation results and CSV export
- GET /api/salt-rules/{id}/preview - Diff comparison view
- POST /api/salt-rules/{id}/publish - Activate rule set

## Frontend Architecture Research

### Decision: React with Shadcn UI components
**Rationale**:
- Shadcn provides professional admin interface components
- File upload with drag-drop functionality
- Data tables for validation results and rule previews
- Consistent with existing FundFlow frontend architecture

**Key components needed**:
- FileUpload: Drag-drop with progress indication
- ValidationResults: Tabular display with CSV export
- RuleComparison: Diff view showing changes
- PublishWorkflow: Status tracking and confirmation

## Testing Strategy Research

### Decision: Contract-first testing with real dependencies
**Rationale**:
- Contract tests define API behavior before implementation
- Integration tests use real SQLite and file system
- E2E tests with Playwright cover complete admin workflows

**Test structure**:
- Contract tests: API endpoint schemas and validation
- Integration tests: Excel parsing, validation pipeline, database operations
- E2E tests: Upload → validate → preview → publish workflow

**Test data approach**:
- Sample Excel files with known validation errors
- Fixture data for different rule set scenarios
- Temporary database and file cleanup between tests

## Performance & Scalability Research

### Decision: Synchronous processing with progress tracking
**Rationale**:
- Admin-only feature doesn't require high concurrency
- Prototype simplicity over async complexity
- 20MB file processing within 30 seconds is achievable

**Performance optimizations**:
- Pandas vectorized operations for data validation
- Database bulk insert operations
- Lazy loading for large Excel sheets
- Efficient diff algorithms for rule comparison

## Monitoring & Observability Research

### Decision: Structured logging with admin action tracking
**Rationale**:
- JSON format enables log analysis and alerting
- Admin actions require audit trail for compliance
- Error context supports debugging validation issues

**Logging strategy**:
- File upload events with metadata
- Validation errors with row/sheet context
- Rule set lifecycle transitions
- Performance metrics for large file processing

---

**Research Status**: ✅ Complete - All technical decisions made, no NEEDS CLARIFICATION remaining