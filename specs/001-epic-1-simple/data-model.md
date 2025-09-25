# Data Model: Simple File Upload & Data Validation

**Feature**: Epic 1 - Simple File Upload & Data Validation
**Date**: 2025-09-14

## Entity Definitions

### User Entity
**Purpose**: Represents system users (Tax Leads like Sarah)
**Storage**: `users` table

```python
class User:
    id: int (Primary Key)
    email: str (Unique, Required)
    company_name: str (Required)
    created_at: datetime (Auto-generated)
```

**Validation Rules**:
- Email must be valid format
- Company name minimum 2 characters
- Created timestamp auto-generated

**Relationships**: One-to-many with UserSession

---

### UserSession Entity
**Purpose**: Tracks file upload and processing sessions
**Storage**: `user_sessions` table

```python
class UserSession:
    session_id: str (Primary Key, UUID)
    user_id: int (Foreign Key -> users.id)
    upload_filename: str (Required)
    original_filename: str (Required)
    file_hash: str (SHA256, for idempotency)
    file_size: int (bytes)
    status: UploadStatus (Enum)
    progress_percentage: int (0-100)
    error_message: str (Optional)
    total_rows: int (Optional)
    valid_rows: int (Optional)
    created_at: datetime (Auto-generated)
    completed_at: datetime (Optional)
```

**Validation Rules**:
- Session ID must be valid UUID
- File size must be <= 10MB (10,485,760 bytes)
- Progress percentage between 0-100
- Status must be valid enum value
- Original filename must match pattern: `^(.+)_Q[1-4] \d{4} distribution data\.(xlsx|xls)$`

**State Transitions**:
```
queued -> uploading -> parsing -> validating -> saving -> completed
    |         |          |          |          |          |
    +-------> failed_upload        |          |          |
              +-------------------> failed_parsing      |
                         +------------------------> failed_validation
                                              +----------> failed_saving
```

**Relationships**:
- Many-to-one with User
- One-to-many with Distribution (for audit trail)
- One-to-many with ValidationError

---

### Investor Entity
**Purpose**: Represents persistent investor entities across multiple uploads and quarters
**Storage**: `investors` table

```python
class Investor:
    id: int (Primary Key)
    investor_name: str (Required, from Excel)
    investor_entity_type: InvestorEntityType (Enum, from Excel)
    investor_tax_state: str (2-letter state code, from Excel)
    created_at: datetime (Auto-generated)
    updated_at: datetime (Auto-updated on changes)
```

**Validation Rules**:
- investor_name: Non-empty string, max 255 characters
- investor_entity_type: Must be one of enumerated values
- investor_tax_state: Must be valid US state code (2 letters, uppercase) or "DC"
- Unique constraint on (investor_name, investor_entity_type, investor_tax_state) - case-insensitive

**InvestorEntityType Enum**:
- CORPORATION
- EXEMPT_ORGANIZATION
- GOVERNMENT_BENEFIT_PLAN
- INDIVIDUAL
- JOINT_TENANCY_TENANCY_IN_COMMON
- LLC_TAXED_AS_PARTNERSHIP
- LLP
- LIMITED_PARTNERSHIP
- PARTNERSHIP
- TRUST

**Relationships**:
- One-to-many with Distribution

---

### Fund Entity
**Purpose**: Centralizes period metadata for a fund upload and anchors associated data
**Storage**: `funds` table

```python
class Fund:
    fund_code: str (Primary Key, extracted from filename)
    period_quarter: str (Q1-Q4 metadata)
    period_year: int (4-digit year)
    created_at: datetime (Auto-generated)
```

**Validation Rules**:
- `fund_code`: Alphanumeric, max 50 characters
- `period_quarter`: Must match Q1, Q2, Q3, or Q4
- `period_year`: Must be ≥ 2020

**Relationships**:
- One-to-many with `FundSourceData`
- One-to-many with `InvestorFundCommitment`
- One-to-many with `Distribution`

---

### InvestorFundCommitment Entity
**Purpose**: Captures an investor’s commitment percentage to a fund (association object)
**Storage**: `investor_fund_commitments` table

```python
class InvestorFundCommitment:
    investor_id: int (Primary Key, FK -> investors.id)
    fund_code: str (Primary Key, FK -> funds.fund_code)
    commitment_percentage: decimal.Decimal (0.0000 – 100.0000)
    effective_date: datetime (commitment start)
    created_at: datetime (Auto-generated)
```

**Validation Rules**:
- `commitment_percentage`: Must be between 0 and 100 inclusive, stored to four decimal places
- (`investor_id`, `fund_code`) pair must be unique

**Relationships**:
- Many-to-one with `Investor`
- Many-to-one with `Fund`

---

### Distribution Entity
**Purpose**: Represents calculated distribution amounts by jurisdiction for a fund period
**Storage**: `distributions` table

```python
class Distribution:
    id: int (Primary Key)
    investor_id: int (Foreign Key -> investors.id)
    session_id: str (Foreign Key -> user_sessions.session_id, for audit trail)
    fund_code: str (Foreign Key -> funds.fund_code)
    jurisdiction: JurisdictionType (Enum: TX_NM or CO)
    amount: decimal.Decimal (Required, >= 0)
    composite_exemption: bool (Default False, from Excel exemption columns)
    withholding_exemption: bool (Default False, from Excel exemption columns)
    composite_tax_amount: decimal.Decimal | None
    withholding_tax_amount: decimal.Decimal | None
    created_at: datetime (Auto-generated)
```

**Validation Rules**:
- amount: Must be ≥ 0, precision to 2 decimal places
- jurisdiction: Must be TX_NM or CO
- fund_code: Must reference an existing fund
- composite_exemption / withholding_exemption: Boolean flags parsed from Excel
- At least one distribution per investor must have amount > 0

**JurisdictionType Enum**:
- TX_NM (Texas and New Mexico)
- CO (Colorado)

**Business Rules**:
- Each investor can have up to one distribution per jurisdiction per fund period
- Total distribution amount across all jurisdictions must be > 0 per investor per fund
- Amounts stored with currency precision
- Exemption flags remain jurisdiction-specific (CO vs. TX_NM)
- Unique constraint on (investor_id, fund_code, jurisdiction)

**Relationships**:
- Many-to-one with `Investor`
- Many-to-one with `UserSession` (audit trail)
- Many-to-one with `Fund` (period metadata)

---

### ValidationError Entity
**Purpose**: Captures validation errors during file processing
**Storage**: `validation_errors` table

```python
class ValidationError:
    id: int (Primary Key)
    session_id: str (Foreign Key -> user_sessions.session_id)
    row_number: int (Excel row number)
    column_name: str (Excel column name)
    error_code: str (Machine-readable error type)
    error_message: str (Human-readable description)
    severity: ErrorSeverity (Enum)
    field_value: str (Optional, problematic value)
    created_at: datetime (Auto-generated)
```

**Validation Rules**:
- row_number: Must be > 0
- column_name: Must be non-empty string
- error_code: Must match defined error codes pattern
- error_message: Must be non-empty, max 500 characters
- severity: Must be valid enum value

**ErrorSeverity Enum**:
- ERROR (Blocks processing)
- WARNING (Allows processing but flags issue)

**Error Codes**:
- MISSING_HEADER: Required column header missing
- INVALID_FILENAME: Filename doesn't match required pattern
- EMPTY_FIELD: Required field is empty
- INVALID_ENTITY_TYPE: Entity type not in allowed enumeration
- INVALID_STATE_CODE: State code not valid US state or DC
- NEGATIVE_AMOUNT: Distribution amount is negative
- ZERO_DISTRIBUTIONS: No positive distribution amounts for investor
- DUPLICATE_INVESTOR: Investor name duplicated within file
- INVALID_NUMBER_FORMAT: Numeric field contains invalid format
- ROW_LIMIT_EXCEEDED: File exceeds 50,000 row limit
- FILE_SIZE_EXCEEDED: File exceeds 10MB limit

**Relationships**:
- Many-to-one with UserSession

---

## Database Relationships

```
User (1) ─── (N) UserSession ─── (N) ValidationError
                     │
                     └─── (N) Distribution ─── (N) Investor (1)
                                     │
                                     └─── (N) InvestorFundCommitment (N) ─── (1) Fund ─── (N) FundSourceData
```

**Key Changes**:
- Investors are now persistent entities, not tied to specific upload sessions
- Distributions link to both Investor (business relationship) and UserSession (audit trail)
- Investor upsert logic: Find existing investor by (name, entity_type, tax_state) or create new

## File Processing Data Flow

1. **Upload**: File uploaded to UserSession, status = "queued"
2. **Filename Parse**: Extract fund_code, period_quarter, period_year
3. **Excel Parse**: Read first worksheet, normalize headers
4. **Investor Upsert**: Find existing investor by (name, entity_type, tax_state) or create new
5. **Distribution Creation**: Create Distribution records linking to persistent Investor + UserSession with exemption flags
6. **Error Collection**: Create ValidationError records for issues
7. **Completion**: Update UserSession status and counts

**Investor Persistence Logic**:
- For each Excel row, check if investor exists: `SELECT * FROM investors WHERE investor_name = ? AND investor_entity_type = ? AND investor_tax_state = ?`
- If found: Use existing investor_id for distribution records
- If not found: Create new investor record, use new investor_id
- This ensures investors persist across multiple quarters/uploads

**Distribution Creation with Exemptions**:
- For TX_NM jurisdiction: Use `distribution_tx_nm` amount, `nm_composite_exemption`, `nm_withholding_exemption`
- For CO jurisdiction: Use `distribution_co` amount, `co_composite_exemption`, `co_withholding_exemption`
- Convert exemption text: "Exemption" (case-insensitive) → True, all else → False
- Create distribution record only if amount > 0 for that jurisdiction

## Data Integrity Constraints

### Primary Keys
- All entities have auto-incrementing integer primary keys
- UserSession uses UUID for session_id for security/uniqueness

### Foreign Keys
- All foreign key relationships enforced at database level
- Cascade delete: UserSession deletion removes related Distributions and ValidationErrors (but NOT Investors)
- Investors are persistent: Deleting UserSession does not delete Investor records

### Unique Constraints
- User.email (unique across system)
- (Investor.investor_name, Investor.investor_entity_type, Investor.investor_tax_state) case-insensitive
- (Distribution.investor_id, Distribution.fund_code, Distribution.period_quarter, Distribution.period_year, Distribution.jurisdiction)

### Check Constraints
- Distribution.amount >= 0
- Distribution.composite_exemption IN (TRUE, FALSE)
- Distribution.withholding_exemption IN (TRUE, FALSE)
- UserSession.progress_percentage BETWEEN 0 AND 100
- UserSession.file_size <= 10485760 (10MB)

## Indexes for Performance

### Read-Heavy Queries
```sql
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_status ON user_sessions(status);
CREATE INDEX idx_investors_identity ON investors(investor_name, investor_entity_type, investor_tax_state);
CREATE INDEX idx_distributions_investor_id ON distributions(investor_id);
CREATE INDEX idx_distributions_session_id ON distributions(session_id);
CREATE INDEX idx_validation_errors_session_id ON validation_errors(session_id);
CREATE INDEX idx_validation_errors_severity ON validation_errors(severity);
```

### Business Logic Queries
```sql
CREATE INDEX idx_distributions_fund_period ON distributions(fund_code, period_quarter, period_year);
CREATE INDEX idx_distributions_investor_period ON distributions(investor_id, fund_code, period_quarter, period_year);
```

## Data Size Estimates (Prototype Scale)

### Per Upload Session
- 1 UserSession record
- ~0-20 NEW Investor records (only if investors don't already exist)
- ~20-40 Distribution records (2 per investor max, always created)
- ~0-100 ValidationError records (errors/warnings)

### Storage Requirements
- UserSession: ~200 bytes per record
- Investor: ~250 bytes per record (reduced fields)
- Distribution: ~110 bytes per record (increased fields with exemption booleans)
- ValidationError: ~200 bytes per record
- **Total per session**: ~8KB (typical) to 5.5MB (max with 50k distributions)

### Database Growth (3-5 concurrent users, daily usage)
**Investor Growth**: Slower growth after initial period as investors become persistent
- Initial period: ~10-20 new investors per session
- Steady state: ~2-5 new investors per session (95% are existing)

**Distribution Growth**: Linear growth with uploads
- Daily: ~50-100 sessions = ~1,000-2,000 new distributions
- Monthly: ~30,000-60,000 new distributions
- Yearly: ~360,000-720,000 distribution records

**Total Database Size**:
- Daily: ~500KB-1MB
- Monthly: ~15-30MB
- Yearly: ~180-360MB (well within SQLite limits)

**Business Queries Enabled**:
- "Show all distributions for Pension Fund X across all quarters"
- "Which investors participated in Q3 2024 vs Q4 2024?"
- "What's the total distribution history for Fund ABC?"
