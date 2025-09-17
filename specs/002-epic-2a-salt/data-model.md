# Data Model: SALT Rules Ingestion & Publishing

**Phase 1 Output** | **Date**: 2025-09-17

## Entity Relationships

```
SourceFile (1) ←→ (1) SaltRuleSet ←→ (*) WithholdingRule
                                    ←→ (*) CompositeRule
                                    ←→ (*) ValidationIssue

SaltRuleSet (1) ←→ (*) StateEntityTaxRuleResolved
```

## Core Entities

### SourceFile
**Purpose**: Track uploaded Excel workbooks with deduplication and audit trail

```python
class SourceFile:
    id: UUID4                    # Primary key
    filename: str               # Original filename (e.g., "EY_SALT_Rules_2025Q1.xlsx")
    filepath: str               # Secure storage path
    sha256_hash: str            # File content hash for deduplication
    file_size: int              # Size in bytes
    content_type: str           # MIME type validation
    upload_timestamp: datetime  # When file was uploaded
    uploaded_by: str            # Admin user identifier

    # Relationships
    rule_set: Optional[SaltRuleSet] = None
```

**Validation Rules**:
- filename: Required, max 255 chars
- filepath: Required, unique, secure path format
- sha256_hash: Required, 64 hex chars, unique per (year, quarter)
- file_size: Required, positive, max 20MB (20,971,520 bytes)
- content_type: Must be "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

### SaltRuleSet
**Purpose**: Version control for SALT rule collections with lifecycle management

```python
class SaltRuleSet:
    id: UUID4                   # Primary key
    year: int                   # Tax year (e.g., 2025)
    quarter: Quarter            # Q1, Q2, Q3, Q4
    version: str                # Semantic version (e.g., "1.0.0")
    status: RuleSetStatus       # draft, active, archived
    effective_date: date        # When rules become active
    expiration_date: Optional[date] = None  # When rules expire
    created_at: datetime        # Creation timestamp
    published_at: Optional[datetime] = None # Publication timestamp
    created_by: str             # Admin user identifier

    # Metadata
    description: Optional[str] = None      # Admin notes
    rule_count_withholding: int = 0        # Count of withholding rules
    rule_count_composite: int = 0          # Count of composite rules

    # Relationships
    source_file_id: UUID4       # Foreign key to SourceFile
    source_file: SourceFile
    withholding_rules: List[WithholdingRule] = []
    composite_rules: List[CompositeRule] = []
    validation_issues: List[ValidationIssue] = []
    resolved_rules: List[StateEntityTaxRuleResolved] = []
```

**Validation Rules**:
- year: Required, 2020-2030 range
- quarter: Required, enum validation
- version: Required, semantic version format
- status: Required, enum validation
- effective_date: Required, must be future date for drafts
- Unique constraint: (year, quarter, status='active')

**State Transitions**:
- draft → active: Requires zero validation errors
- active → archived: Automatic when new rule set activated
- archived: Terminal state, read-only

### WithholdingRule
**Purpose**: Tax withholding rates and thresholds by state and entity type

```python
class WithholdingRule:
    id: UUID4                   # Primary key
    rule_set_id: UUID4          # Foreign key to SaltRuleSet
    state_code: USJurisdiction  # US state/DC jurisdiction enum
    entity_type: str               # InvestorEntityType coding value (e.g., "Corporation", "Partnership")

    # Tax calculations
    tax_rate: Decimal           # Percentage rate (e.g., 0.0525 for 5.25%)
    income_threshold: Decimal   # Minimum income for withholding (dollars)
    tax_threshold: Decimal      # Minimum tax amount (dollars)

    # Metadata
    created_at: datetime

    # Relationships
    rule_set: SaltRuleSet
```

**Validation Rules**:
- state_code: Required, USJurisdiction enum value
- entity_type: Required, must be valid InvestorEntityType coding value
- tax_rate: Required, decimal(5,4), 0.0000-1.0000 range
- income_threshold: Required, decimal(12,2), non-negative
- tax_threshold: Required, decimal(12,2), non-negative
- Unique constraint: (rule_set_id, state_code, entity_type)

### CompositeRule
**Purpose**: Composite tax rates and filing requirements by state and entity type

```python
class CompositeRule:
    id: UUID4                   # Primary key
    rule_set_id: UUID4          # Foreign key to SaltRuleSet
    state_code: USJurisdiction  # US state/DC jurisdiction enum
    entity_type: str               # InvestorEntityType coding value (e.g., "Corporation", "Partnership")

    # Tax calculations
    tax_rate: Decimal           # Percentage rate
    income_threshold: Decimal   # Minimum income for composite filing
    mandatory_filing: bool      # Whether filing is required regardless of income

    # Additional thresholds
    min_tax_amount: Optional[Decimal] = None  # Minimum tax due
    max_tax_amount: Optional[Decimal] = None  # Maximum tax due

    # Metadata
    created_at: datetime

    # Relationships
    rule_set: SaltRuleSet
```

**Validation Rules**:
- state_code: Required, USJurisdiction enum value
- entity_type: Required, must be valid InvestorEntityType coding value
- tax_rate: Required, decimal(5,4), 0.0000-1.0000 range
- income_threshold: Required, decimal(12,2), non-negative
- mandatory_filing: Required, boolean
- min_tax_amount: Optional, decimal(12,2), non-negative
- max_tax_amount: Optional, decimal(12,2), non-negative, >= min_tax_amount
- Unique constraint: (rule_set_id, state_code, entity_type)

### StateEntityTaxRuleResolved
**Purpose**: Denormalized view combining withholding and composite rules for fast calculations

```python
class StateEntityTaxRuleResolved:
    id: UUID4                   # Primary key
    rule_set_id: UUID4          # Foreign key to active SaltRuleSet
    state_code: USJurisdiction  # US state/DC jurisdiction enum
    entity_type: str               # InvestorEntityType coding value (e.g., "Corporation", "Partnership")

    # Withholding data
    withholding_rate: Decimal
    withholding_income_threshold: Decimal
    withholding_tax_threshold: Decimal

    # Composite data
    composite_rate: Decimal
    composite_income_threshold: Decimal
    composite_mandatory_filing: bool
    composite_min_tax: Optional[Decimal] = None
    composite_max_tax: Optional[Decimal] = None

    # Effective dates
    effective_date: date
    expiration_date: Optional[date] = None

    # Audit trail
    created_at: datetime
    source_withholding_rule_id: UUID4
    source_composite_rule_id: UUID4

    # Relationships
    rule_set: SaltRuleSet
```

**Validation Rules**:
- All rate and threshold fields: Same as source tables
- effective_date: Must match rule_set.effective_date
- source_*_rule_id: Required, valid foreign keys
- Unique constraint: (rule_set_id, state_code, entity_type)

## Reference Entities

### ValidationIssue
**Purpose**: Structured validation error and warning collection

```python
class ValidationIssue:
    id: UUID4                   # Primary key
    rule_set_id: UUID4          # Foreign key to SaltRuleSet

    # Error location
    sheet_name: str             # Excel sheet name
    row_number: int             # Excel row number (1-based)
    column_name: Optional[str] = None # Excel column name

    # Error details
    error_code: str             # Structured error code (e.g., "INVALID_STATE")
    severity: IssueSeverity     # error, warning
    message: str                # Human-readable error message
    field_value: Optional[str] = None # Invalid value that caused error

    # Metadata
    created_at: datetime

    # Relationships
    rule_set: SaltRuleSet
```

**Validation Rules**:
- sheet_name: Required, max 255 chars
- row_number: Required, positive integer
- error_code: Required, structured format
- severity: Required, enum validation
- message: Required, max 1000 chars

## Enums

### RuleSetStatus
```python
class RuleSetStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
```

### Quarter
```python
class Quarter(str, Enum):
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"
```

### IssueSeverity
```python
class IssueSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
```

### InvestorEntityType Coding Values
**Note**: Uses coding values from existing InvestorEntityType enum

**Valid coding values**:
- "Corporation" (includes Corporation, LLC_Taxed as Corporation)
- "Partnership" (includes Limited Partnership, Partnership, LLC_Taxed as Partnership, LLP, Estate)
- "Individual" (includes Individual, Joint Tenancy / Tenancy in Common, Grantor Trust)
- "Trust" (for Trust entities)
- "S Corporation" (for S Corporation entities)
- "Exempt Org" (includes Exempt Organization, Government Benefit Plan, Benefit Plan Investor entities)
- "IRA" (for IRA/Keogh entities)

**Mapping from InvestorEntityType enum coding field**:
- Reference: `backend/src/models/enums.py` InvestorEntityType.coding values

## Database Constraints

### Primary Keys
- All entities use UUID4 primary keys for global uniqueness

### Foreign Keys
- `salt_rule_sets.source_file_id` → `source_files.id`
- `withholding_rules.rule_set_id` → `salt_rule_sets.id`
- `composite_rules.rule_set_id` → `salt_rule_sets.id`
- `validation_issues.rule_set_id` → `salt_rule_sets.id`
- `state_entity_tax_rules_resolved.rule_set_id` → `salt_rule_sets.id`

### Unique Constraints
- `source_files.sha256_hash` (per year/quarter combination)
- `salt_rule_sets(year, quarter, status)` where status='active'
- `withholding_rules(rule_set_id, state_code, entity_type)`
- `composite_rules(rule_set_id, state_code, entity_type)`
- `state_entity_tax_rules_resolved(rule_set_id, state_code, entity_type)`

### Check Constraints
- All rate fields: >= 0.0000 AND <= 1.0000
- All threshold fields: >= 0.00
- file_size: > 0 AND <= 20971520
- year: >= 2020 AND <= 2030
- Composite rules: max_tax_amount >= min_tax_amount (when both present)

## Indexes

### Performance Indexes
- `withholding_rules(state_code, entity_type)` - Calculation queries
- `composite_rules(state_code, entity_type)` - Calculation queries
- `state_entity_tax_rules_resolved(state_code, entity_type, effective_date)` - Primary lookup
- `salt_rule_sets(year, quarter, status)` - Admin queries
- `source_files(sha256_hash)` - Deduplication
- `validation_issues(rule_set_id, severity)` - Error reporting

### Audit Indexes
- `salt_rule_sets(created_at)` - Timeline queries
- `validation_issues(created_at)` - Error analysis
- `source_files(upload_timestamp)` - Upload history

---

**Data Model Status**: ✅ Complete - All entities defined with validation rules and relationships