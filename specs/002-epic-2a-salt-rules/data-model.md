# Data Model - Epic 2A SALT Rules Ingestion

## Entity Overview

The SALT rules system manages the complete lifecycle of tax rules from Excel upload through publication and resolution. The model supports versioning, validation, and optimized query access.

## Core Entities

### SourceFile
**Purpose**: Tracks uploaded Excel files with deduplication
**Relationships**: One-to-many with SaltRuleSet

```python
class SourceFile:
    id: int (PK)
    filename: str (NOT NULL)
    filepath: str (NOT NULL)  # Local filesystem path
    sha256: str(64) (NOT NULL, UNIQUE)
    uploaded_at: datetime (NOT NULL)

    # Relationships
    rule_sets: List[SaltRuleSet]
```

**Validation Rules**:
- filename must match `.xlsx` or `.xlsm` pattern
- filepath must be absolute and accessible
- sha256 prevents duplicate uploads
- uploaded_at uses America/Los_Angeles timezone

### SaltRuleSet
**Purpose**: Versioned collections of SALT rules with lifecycle management
**Relationships**: Many-to-one with SourceFile, one-to-many with WithholdingRule and CompositeRule

```python
class SaltRuleSet:
    id: int (PK)
    source_file_id: int (FK -> SourceFile.id)
    year: int (NOT NULL)  # e.g., 2025
    quarter: str (NOT NULL, CHECK IN ('Q1','Q2','Q3','Q4'))
    effective_from: date (GENERATED, STORED)  # Auto-calculated from year/quarter
    effective_to: date (NULL)  # Set when archived
    status: str (NOT NULL, CHECK IN ('draft','active','archived'))
    created_at: datetime (NOT NULL)
    updated_at: datetime (NOT NULL)

    # Relationships
    source_file: SourceFile
    withholding_rules: List[WithholdingRule]
    composite_rules: List[CompositeRule]

    # Constraints
    UNIQUE(year, quarter) WHERE status = 'active'  # Only one active per period
```

**Validation Rules**:
- year must be reasonable range (2020-2030)
- quarter enum validation
- effective_from auto-calculated: Q1=Jan1, Q2=Apr1, Q3=Jul1, Q4=Oct1
- Only one active rule set per year/quarter period
- Status transitions: draft → active → archived

### WithholdingRule
**Purpose**: State-specific withholding tax rules by entity type
**Relationships**: Many-to-one with SaltRuleSet, references State and EntityType

```python
class WithholdingRule:
    id: int (PK)
    rule_set_id: int (FK -> SaltRuleSet.id)
    state_code: str(2) (FK -> State.code)
    entity_type_code: str (FK -> EntityType.code)
    rate: Decimal(7,6) (NULL, CHECK >= 0)  # e.g., 0.0575 for 5.75%
    income_threshold: Decimal(18,2) (NULL, CHECK >= 0)  # USD amounts
    tax_threshold: Decimal(18,2) (NULL, CHECK >= 0)

    # Relationships
    rule_set: SaltRuleSet
    state: State
    entity_type: EntityType

    # Constraints
    UNIQUE(rule_set_id, state_code, entity_type_code)
```

**Validation Rules**:
- Rates are fractional decimals (0.0575 = 5.75%)
- Thresholds are non-negative USD amounts
- No duplicate (state, entity_type) within a rule set
- All referenced states and entity types must exist

### CompositeRule
**Purpose**: State-specific composite tax rules by entity type
**Relationships**: Many-to-one with SaltRuleSet, references State and EntityType

```python
class CompositeRule:
    id: int (PK)
    rule_set_id: int (FK -> SaltRuleSet.id)
    state_code: str(2) (FK -> State.code)
    entity_type_code: str (FK -> EntityType.code)
    rate: Decimal(7,6) (NULL, CHECK >= 0)
    income_threshold: Decimal(18,2) (NULL, CHECK >= 0)
    mandatory: bool (NULL)  # TRUE/FALSE/NULL from Excel

    # Relationships
    rule_set: SaltRuleSet
    state: State
    entity_type: EntityType

    # Constraints
    UNIQUE(rule_set_id, state_code, entity_type_code)
```

**Validation Rules**:
- Same numeric constraints as WithholdingRule
- mandatory field allows three states: True, False, NULL
- No duplicate (state, entity_type) within a rule set

### StateEntityTaxRuleResolved
**Purpose**: Read-only optimized view combining withholding and composite rules
**Relationships**: References SaltRuleSet, denormalized for performance

```python
class StateEntityTaxRuleResolved:
    # Compound Primary Key
    rule_set_id: int (NOT NULL)
    state_code: str(2) (NOT NULL)
    entity_type_code: str (NOT NULL)

    # Withholding rule data
    withholding_rate: Decimal(7,6) (NULL)
    withholding_income_threshold: Decimal(18,2) (NULL)
    withholding_tax_threshold: Decimal(18,2) (NULL)

    # Composite rule data
    composite_rate: Decimal(7,6) (NULL)
    composite_income_threshold: Decimal(18,2) (NULL)
    composite_mandatory: bool (NULL)

    # Provenance tracking
    source_withholding_id: int (NULL)  # References WithholdingRule.id
    source_composite_id: int (NULL)    # References CompositeRule.id

    # Primary Key
    PK(rule_set_id, state_code, entity_type_code)
    INDEX(rule_set_id, state_code, entity_type_code)
```

**Generation Logic**:
- Built atomically when SaltRuleSet status changes to 'active'
- Contains union of all (state, entity_type) combinations from both rule types
- NULL values indicate no rule exists for that combination
- Provenance IDs enable audit trail back to source rules

## Reference Entities

### State
**Purpose**: US state reference data
**Relationships**: Referenced by WithholdingRule and CompositeRule

```python
class State:
    code: str(2) (PK)  # e.g., 'CA', 'NY', 'DC'
    name: str (NOT NULL)  # e.g., 'California', 'New York'
```

**Data**: 50 states + District of Columbia (51 total)

### EntityType
**Purpose**: Investor entity type reference from Epic 1
**Relationships**: Referenced by WithholdingRule and CompositeRule

```python
class EntityType:
    code: str (PK)  # Canonical codes from Epic 1
    label: str (NOT NULL)
```

**Examples**: 'INDIVIDUAL', 'CORPORATION', 'PARTNERSHIP', 'TRUST', etc.

## Validation Models

### ValidationIssue
**Purpose**: Structured validation error/warning collection
**Lifecycle**: Created during parsing, exported as CSV

```python
@dataclass
class ValidationIssue:
    row: int  # Excel row number (1-based)
    sheet: str  # 'Withholding' or 'Composite'
    state_code: Optional[str]  # If parseable
    entity_type_code: Optional[str]  # If parseable
    code: str  # Error code: MISSING_SHEET, DUPLICATE_RULE, etc.
    message: str  # Human-readable description
    severity: Literal["error", "warning"]
```

**Error Codes**:
- `UNSUPPORTED_FILE_TYPE`: File extension not .xlsx/.xlsm
- `MISSING_SHEET`: Required sheet not found
- `DUPLICATE_RULE`: Same (state, entity_type) in sheet
- `UNKNOWN_REFERENCE`: State/entity_type not in reference data
- `INVALID_NUMBER`: Cannot parse as non-negative number
- `COVERAGE_GAP`: Missing state/entity combinations (warning)

## State Transitions

### SaltRuleSet Lifecycle
1. **Upload**: Create SourceFile → Create SaltRuleSet(status='draft')
2. **Parse**: Read Excel → Validate → Collect ValidationIssues
3. **Stage**: If no errors → Write WithholdingRules + CompositeRules
4. **Publish**: Change status to 'active' → Generate ResolvedRules → Archive previous active
5. **Archive**: Set effective_to date, change status to 'archived'

### Validation Workflow
1. **File Validation**: Format, size, SHA256 deduplication
2. **Structure Validation**: Sheet presence, header mapping
3. **Data Validation**: Type conversion, range checks
4. **Reference Validation**: State/entity existence
5. **Business Validation**: Duplicate detection, coverage analysis

## Performance Considerations

### Indexing Strategy
- Primary keys on all entities for referential integrity
- Compound index on (rule_set_id, state_code, entity_type_code) for resolved rules
- Index on (year, quarter, status) for rule set queries
- Index on sha256 for file deduplication

### Query Patterns
- **Rule Lookup**: SELECT * FROM state_entity_tax_rules_resolved WHERE rule_set_id = ? AND state_code = ? AND entity_type_code = ?
- **Active Rules**: SELECT * FROM salt_rule_sets WHERE status = 'active' AND ? BETWEEN effective_from AND COALESCE(effective_to, '9999-12-31')
- **Validation History**: SELECT * FROM source_files WHERE sha256 = ?

### Data Volume Estimates
- States: 51 rows (static)
- EntityTypes: ~10 rows (from Epic 1)
- Rules per set: ~2,000 (51 states × 10 entities × 2 rule types × 20% coverage)
- Rule sets: ~20 per year (quarterly updates with revisions)
- Storage: <1MB per rule set, <100MB total for production