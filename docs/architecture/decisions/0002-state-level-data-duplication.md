# ADR-0002: State-Level Data Duplication in SALT Rules

## Status
Accepted

## Date
2025-09-19

## Context

We are implementing a SALT (State and Local Tax) rules processing system for FundFlow v1.2 prototype. The system processes Excel files containing tax rules with the following structure:

### Data Structure
- **Each row represents one state** with tax rates and thresholds for multiple entity types
- **Each column represents either**:
  - State identification (State, State Abbrev)
  - Entity-specific tax rates (e.g., "NONRESIDENT / CORPORATE WITHHOLDING_Individual")
  - State-level thresholds that apply to ALL entity types for that state

### State-Level vs Entity-Specific Data

**State-Level Data (applies to all entity types within a state):**
- Withholding: `Per Partner Income Threshold`, `Per Partner W/H Tax Threshold`
- Composite: `Composite Rates_Income Threshold`, `Composite Rates_Mandatory Composite`

**Entity-Specific Data (varies by entity type):**
- Tax rates for each entity type (Individual, Partnership, Corporation, etc.)

### Current Models
```python
class WithholdingRule(Base):
    state_code = Column(SQLEnum(USJurisdiction))
    entity_type = Column(String(50))  # Individual, Partnership, etc.
    tax_rate = Column(DECIMAL(5, 4))  # Entity-specific
    income_threshold = Column(DECIMAL(12, 2))  # State-level
    tax_threshold = Column(DECIMAL(12, 2))  # State-level

class CompositeRule(Base):
    state_code = Column(SQLEnum(USJurisdiction))
    entity_type = Column(String(50))  # Individual, Partnership, etc.
    tax_rate = Column(DECIMAL(5, 4))  # Entity-specific
    income_threshold = Column(DECIMAL(12, 2))  # State-level
    mandatory_filing = Column(Boolean)  # State-level
```

## Decision

We will **duplicate state-level threshold data across all entity types** for each state (Option 1), rather than creating a separate state-level model (Option 2).

### Implementation Approach
For each state row in the Excel file:
1. Extract state name, state abbreviation, and state-level thresholds
2. For each entity type column that has a tax rate:
   - Create a separate WithholdingRule/CompositeRule object
   - Include the duplicated state-level thresholds in each rule object
   - Use entity type coding values from InvestorEntityType enum

Example for Alabama state:
```python
# Multiple objects created from one Excel row
WithholdingRule(state="Alabama", state_code="AL", entity_type="Individual",
                income_threshold=1000, tax_threshold=500, tax_rate=0.05)
WithholdingRule(state="Alabama", state_code="AL", entity_type="Partnership",
                income_threshold=1000, tax_threshold=500, tax_rate=0.03)
# Same thresholds duplicated across all entity types for Alabama
```

## Rationale

### Why Option 1 (Duplication) for v1.2 Prototype

**Simplicity and Development Speed:**
- Single table queries for all use cases
- No complex joins or additional models needed
- Faster development = quicker user validation
- Aligns with v1.2 YAGNI principle

**Scale Considerations:**
- Data volume: ~50 states × ~8 entity types = ~400 rules per sheet
- Threshold duplication overhead is negligible at this scale
- Query performance will be excellent with single-table access

**Prototype Goals:**
- Focus on validating user workflow and Excel processing
- Avoid over-engineering for theoretical data normalization benefits
- Reduce potential failure points during user validation

### Alternative Considered (Option 2 - Normalized)

**Separate State-Level Model:**
```python
class StateTaxInfo(Base):
    state_code = Column(SQLEnum(USJurisdiction))
    withholding_income_threshold = Column(DECIMAL)
    withholding_tax_threshold = Column(DECIMAL)
    composite_income_threshold = Column(DECIMAL)
    composite_mandatory_filing = Column(Boolean)

# WithholdingRule/CompositeRule would reference StateTaxInfo
```

**Why Not for v1.2:**
- Requires joins for every query: `SELECT w.*, s.* FROM withholding_rules w JOIN state_tax_info s...`
- Additional complexity in data loading and validation
- More models to manage and test
- Premature optimization for a prototype phase

## Consequences

### Positive
- **Fast Development**: Single model operations, no join complexity
- **Simple Queries**: All data available in one table
- **Easy Testing**: Straightforward data setup and validation
- **Clear Data Model**: Each rule object is self-contained

### Negative
- **Data Duplication**: State-level thresholds stored multiple times
- **Potential Inconsistency**: Risk if manual data editing occurs
- **Future Refactoring**: May need normalization in v1.3 for larger scale

### Future Considerations for v1.3
- Monitor query patterns and performance with real usage
- Consider normalization if data volume grows significantly (>10k rules)
- Evaluate whether state-level data changes frequently enough to warrant normalization
- Plan migration strategy if normalized approach becomes beneficial

## References
- Excel file structure with state rows and entity type columns
- InvestorEntityType enum with coding values (Partnership, Corporation, Individual, etc.)
- FundFlow v1.2 prototype requirements focusing on simplicity and user validation