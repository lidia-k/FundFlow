# Phase 0: Research - Epic 2A SALT Rules Ingestion

## Excel Processing Research

### Decision: pandas + openpyxl for Excel parsing
**Rationale**:
- pandas provides robust data manipulation and validation capabilities
- openpyxl handles both .xlsx and .xlsm formats with sheet-level access
- Existing project dependency - no new packages required
- Strong error handling for malformed Excel files

**Alternatives considered**:
- xlrd/xlwt: Limited to .xls format, deprecated for .xlsx
- pure openpyxl: More manual data processing, no built-in validation
- pyexcel: Additional dependency, less mature ecosystem

### Header Normalization Strategy
**Decision**: Custom normalization function with synonym mapping
**Rationale**:
- Case-insensitive matching handles user variations
- Whitespace normalization prevents parsing errors
- Synonym mapping (e.g., "Entity" → "Entity Type") improves usability
- Newline-to-space conversion handles multi-line headers

**Implementation approach**:
```python
def normalize_header(header: str) -> str:
    # Strip, lowercase, collapse whitespace, convert newlines
    normalized = re.sub(r'\s+', ' ', str(header).strip().lower())
    return HEADER_SYNONYMS.get(normalized, normalized)
```

## Database Schema Research

### Decision: Separate authoritative tables + resolved view
**Rationale**:
- Maintains data integrity with separate withholding_rules and composite_rules
- Resolved rules table provides O(1) lookup for calculation engine
- Clear audit trail with source_*_id provenance fields
- PostgreSQL partial unique constraints enforce business rules

**Alternatives considered**:
- Single rules table with rule_type column: Harder to enforce entity-specific constraints
- JSON fields for rule data: Poor query performance, no referential integrity
- Separate databases per rule type: Unnecessary complexity for prototype

### Generated Columns for Date Calculation
**Decision**: PostgreSQL GENERATED ALWAYS AS for effective_from dates
**Rationale**:
- Ensures consistent quarter-to-date mapping
- Database enforces correctness at storage level
- Eliminates application-level date calculation bugs
- Supports temporal queries efficiently

**Implementation**:
```sql
effective_from DATE GENERATED ALWAYS AS (
  CASE quarter
    WHEN 'Q1' THEN make_date(year,1,1)
    WHEN 'Q2' THEN make_date(year,4,1)
    WHEN 'Q3' THEN make_date(year,7,1)
    ELSE make_date(year,10,1)
  END
) STORED
```

## Validation Strategy Research

### Decision: Multi-layer validation with structured error collection
**Rationale**:
- File-level validation catches format issues early
- Row-level validation provides granular feedback
- Cross-table validation enforces business rules
- Severity levels (error/warning) enable partial workflows

**Validation layers**:
1. **File validation**: Format, size, SHA256 deduplication
2. **Structure validation**: Required sheets, header mapping
3. **Data validation**: Type conversion, range checks, referential integrity
4. **Business validation**: Coverage gaps, duplicate rules

### Error Context Strategy
**Decision**: Structured ValidationIssue model with downloadable CSV export
**Rationale**:
- Users need precise error locations (row, sheet, field)
- CSV export enables offline review and correction
- Severity filtering allows progressive error resolution
- Structured format supports automated tooling

**Error model**:
```python
@dataclass
class ValidationIssue:
    row: int
    sheet: str
    state_code: Optional[str]
    entity_type_code: Optional[str]
    code: str  # MISSING_SHEET, DUPLICATE_RULE, etc.
    message: str
    severity: Literal["error", "warning"]
```

## State Management Research

### Decision: State machine with atomic transitions
**Rationale**:
- Clear workflow: draft → staged → active → archived
- Atomic database transactions prevent inconsistent states
- Partial unique constraints enforce one-active-per-period
- Rollback capability for failed publications

**State transitions**:
- Upload: source_files + draft salt_rule_sets
- Validate: Issues collection, block on errors
- Stage: Rules written to authoritative tables
- Publish: Status flip + resolved rules generation
- Archive: Graceful deprecation with effective_to dates

## File Storage Research

### Decision: Local filesystem with configurable path + SHA256 deduplication
**Rationale**:
- Prototype simplicity - no S3 integration needed
- SHA256 prevents duplicate uploads for same year/quarter
- Configurable paths support future cloud migration
- Database stores metadata, filesystem stores content

**Security considerations**:
- File type validation prevents malicious uploads
- Size limits prevent DoS attacks
- Quarantine directory for failed validations
- Audit logging for all file operations

## Number Parsing Research

### Decision: Custom parsing with strict validation
**Rationale**:
- Handle common Excel formatting (commas, spaces)
- Reject negative values (parentheses notation)
- Convert blank cells to SQL NULL
- Preserve precision for financial calculations

**Implementation strategy**:
```python
def parse_number(value) -> Optional[Decimal]:
    if pd.isna(value) or value == "":
        return None

    # Remove formatting
    cleaned = re.sub(r'[,\s]', '', str(value).strip())

    # Reject negatives (parentheses)
    if '(' in cleaned and ')' in cleaned:
        raise ValueError("Negative values not allowed")

    return Decimal(cleaned)
```

## Testing Strategy Research

### Decision: Real dependencies with test data isolation
**Rationale**:
- SQLite for fast test database setup/teardown
- Real Excel files in test fixtures
- No mocking of pandas/openpyxl - test actual parsing
- Separate test schema prevents data contamination

**Test data management**:
- fixtures/excel/ directory with sample workbooks
- Known-good files for positive tests
- Malformed files for error path validation
- State/entity reference data in test database

## Performance Considerations

### Decision: Synchronous processing with progress tracking
**Rationale**:
- Prototype scope: 3-5 users, reasonable file sizes
- Simplicity over async complexity
- Progress UI prevents user confusion
- Future scaling to async queues as needed

**Optimization strategies**:
- Batch inserts for rule data
- Database indexes on lookup columns
- Resolved rules table for O(1) query performance
- File size limits prevent memory issues