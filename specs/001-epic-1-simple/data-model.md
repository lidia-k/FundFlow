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
- One-to-many with Investor
- One-to-many with Distribution
- One-to-many with ValidationError

---

### Investor Entity
**Purpose**: Represents investor information from uploaded Excel files
**Storage**: `investors` table

```python
class Investor:
    id: int (Primary Key)
    session_id: str (Foreign Key -> user_sessions.session_id)
    fund_code: str (Extracted from filename)
    period_quarter: str (Q1-Q4, extracted from filename)
    period_year: int (Extracted from filename)
    investor_name: str (Required, from Excel)
    investor_entity_type: InvestorEntityType (Enum, from Excel)
    investor_tax_state: str (2-letter state code, from Excel)
    row_number: int (Original Excel row for error tracking)
    created_at: datetime (Auto-generated)
    updated_at: datetime (Auto-updated on changes)
```

**Validation Rules**:
- investor_name: Non-empty string, max 255 characters
- investor_entity_type: Must be one of enumerated values
- investor_tax_state: Must be valid US state code (2 letters, uppercase) or "DC"
- fund_code: Alphanumeric, max 50 characters
- period_quarter: Must match Q1, Q2, Q3, or Q4
- period_year: Must be 4-digit year >= 2020
- Unique constraint on (session_id, fund_code, investor_name) - case-insensitive

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
- Many-to-one with UserSession
- One-to-many with Distribution

---

### Distribution Entity
**Purpose**: Represents quarterly distribution amounts by jurisdiction
**Storage**: `distributions` table

```python
class Distribution:
    id: int (Primary Key)
    investor_id: int (Foreign Key -> investors.id)
    jurisdiction: JurisdictionType (Enum: TX_NM or CO)
    amount: decimal.Decimal (Required, >= 0)
    created_at: datetime (Auto-generated)
```

**Validation Rules**:
- amount: Must be >= 0, precision to 2 decimal places
- jurisdiction: Must be TX_NM or CO
- At least one distribution per investor must have amount > 0

**JurisdictionType Enum**:
- TX_NM (Texas and New Mexico)
- CO (Colorado)

**Business Rules**:
- Each investor can have 0-2 distribution records (one per jurisdiction)
- Total distribution amount across all jurisdictions must be > 0 per investor
- Amounts are stored with 2 decimal precision for currency

**Relationships**:
- Many-to-one with Investor

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

### EY SALT Rules Entity (Pre-populated)
**Purpose**: Contains pre-loaded EY tax calculation rules
**Storage**: `ey_salt_rules` table

```python
class EYSALTRule:
    id: int (Primary Key)
    state: str (2-letter state code)
    tax_rate: decimal.Decimal (Tax rate percentage)
    apportionment_formula: str (Tax calculation formula)
    effective_date: date (When rule became effective)
    created_at: datetime (Auto-generated)
    is_active: bool (Default True)
```

**Validation Rules**:
- state: Must be valid US state code (2 letters, uppercase) or "DC"
- tax_rate: Must be >= 0, max 100 (percentage)
- apportionment_formula: Must be non-empty string
- effective_date: Must be valid date
- Only one active rule per state

**Relationships**:
- Used for SALT calculations (read-only for upload feature)

---

## Database Relationships

```
User (1) ─── (N) UserSession ─── (N) Investor ─── (N) Distribution
                     │
                     └─── (N) ValidationError
```

## File Processing Data Flow

1. **Upload**: File uploaded to UserSession, status = "queued"
2. **Filename Parse**: Extract fund_code, period_quarter, period_year
3. **Excel Parse**: Read first worksheet, normalize headers
4. **Row Validation**: Create Investor records with validation
5. **Distribution Creation**: Create Distribution records per jurisdiction
6. **Error Collection**: Create ValidationError records for issues
7. **Completion**: Update UserSession status and counts

## Data Integrity Constraints

### Primary Keys
- All entities have auto-incrementing integer primary keys
- UserSession uses UUID for session_id for security/uniqueness

### Foreign Keys
- All foreign key relationships enforced at database level
- Cascade delete: UserSession deletion removes related Investors, Distributions, ValidationErrors

### Unique Constraints
- User.email (unique across system)
- (Investor.session_id, Investor.fund_code, Investor.investor_name) case-insensitive
- (Distribution.investor_id, Distribution.jurisdiction)

### Check Constraints
- Distribution.amount >= 0
- UserSession.progress_percentage BETWEEN 0 AND 100
- UserSession.file_size <= 10485760 (10MB)

## Indexes for Performance

### Read-Heavy Queries
```sql
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_status ON user_sessions(status);
CREATE INDEX idx_investors_session_id ON investors(session_id);
CREATE INDEX idx_distributions_investor_id ON distributions(investor_id);
CREATE INDEX idx_validation_errors_session_id ON validation_errors(session_id);
CREATE INDEX idx_validation_errors_severity ON validation_errors(severity);
```

### Business Logic Queries
```sql
CREATE INDEX idx_investors_fund_period ON investors(fund_code, period_quarter, period_year);
CREATE INDEX idx_ey_salt_rules_state_active ON ey_salt_rules(state, is_active);
```

## Data Size Estimates (Prototype Scale)

### Per Upload Session
- 1 UserSession record
- ~10-20 Investor records (max 50,000)
- ~20-40 Distribution records (2 per investor max)
- ~0-100 ValidationError records (errors/warnings)

### Storage Requirements
- UserSession: ~200 bytes per record
- Investor: ~300 bytes per record
- Distribution: ~50 bytes per record
- ValidationError: ~200 bytes per record
- **Total per session**: ~10KB (typical) to 15MB (max with 50k investors)

### Database Growth (3-5 concurrent users, daily usage)
- Daily: ~50-100 sessions = ~500KB-1.5MB
- Monthly: ~15-30MB
- Yearly: ~180-360MB (well within SQLite limits)