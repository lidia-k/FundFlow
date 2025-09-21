# Data Model: Epic 2B Withholding and Composite Tax Calculation

**Date**: 2025-09-21
**Phase**: Phase 1 - Data Model Design

## Overview

This document defines the data model extensions required for Epic 2B tax calculation functionality. The design extends existing models rather than creating new entities, following the YAGNI principle and maintaining data locality.

## Model Extensions

### 1. Distribution Model Extensions

**Existing Model** (from Epic 1):
```python
class Distribution(Base):
    __tablename__ = "distributions"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_sessions.session_id"))
    investor_id: Mapped[int] = mapped_column(ForeignKey("investors.id"))
    jurisdiction: Mapped[str] = mapped_column(String(10))
    amount: Mapped[Decimal] = mapped_column(DECIMAL(precision=15, scale=2))
    composite_exemption: Mapped[bool] = mapped_column(default=False)
    withholding_exemption: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

**Extended Model** (Epic 2B additions):
```python
class Distribution(Base):
    __tablename__ = "distributions"

    # Existing fields (unchanged)
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_sessions.session_id"))
    investor_id: Mapped[int] = mapped_column(ForeignKey("investors.id"))
    jurisdiction: Mapped[str] = mapped_column(String(10))
    amount: Mapped[Decimal] = mapped_column(DECIMAL(precision=15, scale=2))
    composite_exemption: Mapped[bool] = mapped_column(default=False)
    withholding_exemption: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # NEW: Tax calculation results
    withholding_tax_tx: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(precision=15, scale=4), nullable=True)
    withholding_tax_nm: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(precision=15, scale=4), nullable=True)
    withholding_tax_co: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(precision=15, scale=4), nullable=True)
    composite_tax_tx: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(precision=15, scale=4), nullable=True)
    composite_tax_nm: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(precision=15, scale=4), nullable=True)
    composite_tax_co: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(precision=15, scale=4), nullable=True)

    # NEW: Tax calculation metadata
    tax_calculation_applied: Mapped[bool] = mapped_column(default=False)
    salt_rule_set_id: Mapped[Optional[int]] = mapped_column(ForeignKey("salt_rule_set.id"), nullable=True)
    exemption_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    calculation_timestamp: Mapped[Optional[datetime]] = mapped_column(nullable=True)
```

**Field Descriptions**:
- `withholding_tax_*`: Calculated withholding tax amounts by state (TX/NM/CO)
- `composite_tax_*`: Calculated composite tax amounts by state (TX/NM/CO)
- `tax_calculation_applied`: Flag indicating whether tax calculations were performed
- `salt_rule_set_id`: Reference to the SALT rule set used for calculations
- `exemption_reason`: Human-readable reason when taxes were exempted
- `calculation_timestamp`: When tax calculations were performed

### 2. Tax Calculation Audit Model (New)

**Purpose**: Store detailed audit trail for compliance and debugging

```python
class TaxCalculationAudit(Base):
    __tablename__ = "tax_calculation_audit"

    id: Mapped[int] = mapped_column(primary_key=True)
    distribution_id: Mapped[int] = mapped_column(ForeignKey("distributions.id"))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_sessions.session_id"))

    # Step 1: Exemption checks
    step1_exemption_applied: Mapped[bool] = mapped_column(default=False)
    step1_exemption_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    step1_jurisdiction_matches_tax_state: Mapped[bool] = mapped_column(default=False)

    # Step 2: Composite tax calculation
    step2_mandatory_filing_required: Mapped[bool] = mapped_column(default=False)
    step2_tax_rate_found: Mapped[bool] = mapped_column(default=False)
    step2_income_threshold_met: Mapped[bool] = mapped_column(default=False)
    step2_applied_tax_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(precision=8, scale=6), nullable=True)
    step2_calculated_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(precision=15, scale=4), nullable=True)

    # Step 3: Withholding tax calculation
    step3_withholding_rate_found: Mapped[bool] = mapped_column(default=False)
    step3_income_threshold_met: Mapped[bool] = mapped_column(default=False)
    step3_tax_threshold_met: Mapped[bool] = mapped_column(default=False)
    step3_applied_tax_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(precision=8, scale=6), nullable=True)
    step3_calculated_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(precision=15, scale=4), nullable=True)
    step3_final_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(precision=15, scale=4), nullable=True)

    # Rule references
    applied_salt_rule_set_id: Mapped[int] = mapped_column(ForeignKey("salt_rule_set.id"))
    applied_composite_rule_id: Mapped[Optional[int]] = mapped_column(ForeignKey("composite_rule.id"), nullable=True)
    applied_withholding_rule_id: Mapped[Optional[int]] = mapped_column(ForeignKey("withholding_rule.id"), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    distribution: Mapped["Distribution"] = relationship("Distribution", back_populates="audit_records")
    salt_rule_set: Mapped["SaltRuleSet"] = relationship("SaltRuleSet")
    composite_rule: Mapped[Optional["CompositeRule"]] = relationship("CompositeRule")
    withholding_rule: Mapped[Optional["WithholdingRule"]] = relationship("WithholdingRule")
```

### 3. Pydantic Response Models

**Enhanced Distribution Response**:
```python
class DistributionResponse(BaseModel):
    id: int
    investor_name: str
    jurisdiction: str
    amount: Decimal

    # Legacy exemption flags (preserved for backward compatibility)
    composite_exemption: bool
    withholding_exemption: bool

    # NEW: Tax calculation results
    withholding_tax_tx: Optional[Decimal] = None
    withholding_tax_nm: Optional[Decimal] = None
    withholding_tax_co: Optional[Decimal] = None
    composite_tax_tx: Optional[Decimal] = None
    composite_tax_nm: Optional[Decimal] = None
    composite_tax_co: Optional[Decimal] = None

    # NEW: Calculation metadata
    tax_calculation_applied: bool = False
    exemption_reason: Optional[str] = None
    calculation_timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True
```

**Tax Calculation Summary**:
```python
class TaxCalculationSummary(BaseModel):
    session_id: str
    salt_rule_set_id: Optional[int]
    total_distributions: int
    distributions_with_taxes: int
    distributions_exempted: int

    # Tax totals by state
    total_withholding_tax_tx: Decimal
    total_withholding_tax_nm: Decimal
    total_withholding_tax_co: Decimal
    total_composite_tax_tx: Decimal
    total_composite_tax_nm: Decimal
    total_composite_tax_co: Decimal

    calculation_timestamp: datetime
```

**Audit Report Response**:
```python
class TaxCalculationAuditResponse(BaseModel):
    distribution_id: int
    investor_name: str
    jurisdiction: str
    distribution_amount: Decimal

    step1_exemption_applied: bool
    step1_exemption_reason: Optional[str]

    step2_composite_tax_calculated: bool
    step2_tax_rate: Optional[Decimal]
    step2_tax_amount: Optional[Decimal]

    step3_withholding_tax_calculated: bool
    step3_tax_rate: Optional[Decimal]
    step3_tax_amount: Optional[Decimal]

    applied_rule_set_name: str
    calculation_timestamp: datetime
```

## Data Relationships

### Updated Relationship Mappings

```python
# Distribution relationships (updated)
class Distribution(Base):
    # Existing relationships
    session: Mapped["UserSession"] = relationship("UserSession", back_populates="distributions")
    investor: Mapped["Investor"] = relationship("Investor", back_populates="distributions")

    # NEW relationships
    salt_rule_set: Mapped[Optional["SaltRuleSet"]] = relationship("SaltRuleSet")
    audit_records: Mapped[List["TaxCalculationAudit"]] = relationship(
        "TaxCalculationAudit",
        back_populates="distribution",
        cascade="all, delete-orphan"
    )

# UserSession relationships (updated)
class UserSession(Base):
    # Existing relationships preserved
    distributions: Mapped[List["Distribution"]] = relationship("Distribution", back_populates="session")

    # NEW computed properties
    @property
    def has_tax_calculations(self) -> bool:
        return any(d.tax_calculation_applied for d in self.distributions)

    @property
    def tax_calculation_summary(self) -> Optional[TaxCalculationSummary]:
        if not self.has_tax_calculations:
            return None

        # Calculate summary from distributions
        # Implementation in service layer
```

## Database Migration

**Migration Script** (Alembic):
```python
def upgrade():
    # Add new columns to distributions table
    op.add_column('distributions', sa.Column('withholding_tax_tx', sa.DECIMAL(precision=15, scale=4), nullable=True))
    op.add_column('distributions', sa.Column('withholding_tax_nm', sa.DECIMAL(precision=15, scale=4), nullable=True))
    op.add_column('distributions', sa.Column('withholding_tax_co', sa.DECIMAL(precision=15, scale=4), nullable=True))
    op.add_column('distributions', sa.Column('composite_tax_tx', sa.DECIMAL(precision=15, scale=4), nullable=True))
    op.add_column('distributions', sa.Column('composite_tax_nm', sa.DECIMAL(precision=15, scale=4), nullable=True))
    op.add_column('distributions', sa.Column('composite_tax_co', sa.DECIMAL(precision=15, scale=4), nullable=True))
    op.add_column('distributions', sa.Column('tax_calculation_applied', sa.Boolean(), default=False))
    op.add_column('distributions', sa.Column('salt_rule_set_id', sa.Integer(), nullable=True))
    op.add_column('distributions', sa.Column('exemption_reason', sa.String(255), nullable=True))
    op.add_column('distributions', sa.Column('calculation_timestamp', sa.DateTime(), nullable=True))

    # Add foreign key constraint
    op.create_foreign_key(None, 'distributions', 'salt_rule_set', ['salt_rule_set_id'], ['id'])

    # Create audit table
    op.create_table('tax_calculation_audit',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('distribution_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(36), nullable=False),
        # ... additional columns from model definition
    )
```

## Validation Rules

### Business Logic Validation

1. **Tax Amount Precision**: Tax amounts must be rounded to 4 decimal places
2. **Calculation Consistency**: If tax_calculation_applied=True, at least one tax amount must be non-null
3. **Audit Trail Integrity**: Every calculated tax must have corresponding audit record
4. **Rule Set Reference**: salt_rule_set_id must reference active rule set when tax_calculation_applied=True
5. **Exemption Logic**: exemption_reason must be provided when both tax exemptions are true

### Data Constraints

```sql
-- Check constraints for data integrity
ALTER TABLE distributions ADD CONSTRAINT chk_tax_calculation_consistency
CHECK (
    (tax_calculation_applied = false) OR
    (withholding_tax_tx IS NOT NULL OR withholding_tax_nm IS NOT NULL OR
     withholding_tax_co IS NOT NULL OR composite_tax_tx IS NOT NULL OR
     composite_tax_nm IS NOT NULL OR composite_tax_co IS NOT NULL)
);

-- Ensure audit records exist for calculated taxes
-- (Enforced in application layer due to SQLite limitations)
```

## Performance Considerations

### Indexing Strategy

```sql
-- Indexes for tax calculation queries
CREATE INDEX idx_distributions_tax_calculation ON distributions(tax_calculation_applied, salt_rule_set_id);
CREATE INDEX idx_distributions_session_tax ON distributions(session_id, tax_calculation_applied);
CREATE INDEX idx_audit_distribution ON tax_calculation_audit(distribution_id);
CREATE INDEX idx_audit_session ON tax_calculation_audit(session_id);
```

### Query Optimization

- **Bulk Tax Loading**: Use SQLAlchemy eager loading for session tax summaries
- **Audit Trail Access**: Lazy load audit records to avoid N+1 queries
- **State-based Filtering**: Index on tax_calculation_applied for fast filtering

---
*Data model design completed: 2025-09-21*
*Next: API Contract Generation*