# Quickstart Guide: Epic 2B Tax Calculation Implementation

**Date**: 2025-09-21
**Phase**: Phase 1 - Implementation Quickstart

## Overview

This quickstart guide provides step-by-step instructions for implementing Epic 2B withholding and composite tax calculation functionality. Follow these steps to extend the existing FundFlow system with tax calculation capabilities.

## Prerequisites

- Epic 2A SALT rule system must be implemented and functional
- Active SALT rule set must exist in the database
- Existing upload and distribution processing pipeline must be working
- Test data with investor distributions and SALT rules available

## Implementation Sequence

### Step 1: Database Schema Extensions

**Duration**: 30 minutes

1. **Create Alembic Migration**:
   ```bash
   cd backend
   alembic revision --autogenerate -m "epic_2b_tax_calculation_fields"
   ```

2. **Review Generated Migration**:
   - Verify all new Distribution model fields are included
   - Confirm TaxCalculationAudit table creation
   - Check foreign key constraints

3. **Apply Migration**:
   ```bash
   alembic upgrade head
   ```

**Validation**:
```sql
-- Verify new columns exist
PRAGMA table_info(distributions);
-- Should include: withholding_tax_tx, composite_tax_tx, tax_calculation_applied, etc.

-- Verify audit table exists
SELECT name FROM sqlite_master WHERE type='table' AND name='tax_calculation_audit';
```

### Step 2: Data Model Updates

**Duration**: 45 minutes

1. **Update Distribution Model** (`backend/src/models/distribution.py`):
   ```python
   # Add new fields from data-model.md specification
   withholding_tax_tx: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(precision=15, scale=4), nullable=True)
   # ... (add all tax calculation fields)
   ```

2. **Create TaxCalculationAudit Model** (`backend/src/models/tax_calculation_audit.py`):
   ```python
   # Implement complete audit model from specification
   ```

3. **Update Pydantic Response Models** (`backend/src/models/responses.py`):
   ```python
   # Extend DistributionResponse with tax fields
   # Add TaxCalculationSummary and audit response models
   ```

**Validation**:
```python
# Test model instantiation
distribution = Distribution(
    session_id="test",
    investor_id=1,
    jurisdiction="TX",
    amount=Decimal("1000.00"),
    tax_calculation_applied=True,
    withholding_tax_tx=Decimal("25.0000")
)
assert distribution.withholding_tax_tx == Decimal("25.0000")
```

### Step 3: Tax Calculation Service

**Duration**: 2 hours

1. **Create TaxCalculationService** (`backend/src/services/tax_calculation_service.py`):
   ```python
   class TaxCalculationService:
       def __init__(self, db: Session):
           self.db = db

       async def apply_tax_calculations(self, distributions: List[Distribution]) -> List[Distribution]:
           """Apply 3-step tax calculation logic"""
           # Step 1: Handle exemptions
           # Step 2: Calculate composite tax (mandatory states)
           # Step 3: Calculate withholding tax
           pass
   ```

2. **Implement Step-by-Step Logic**:
   - `_check_exemptions()`: Handle composite/withholding exemptions and jurisdiction matching
   - `_calculate_composite_tax()`: Mandatory filing states with thresholds
   - `_calculate_withholding_tax()`: Withholding rates with thresholds
   - `_create_audit_records()`: Generate detailed audit trail

3. **Add Validation and Error Handling**:
   ```python
   class TaxCalculationError(Exception):
       def __init__(self, message: str, distribution_id: int = None):
           super().__init__(message)
           self.distribution_id = distribution_id
   ```

**Validation**:
```python
# Unit test for exemption logic
distributions = [create_test_distribution(composite_exemption=True)]
service = TaxCalculationService(db)
result = await service.apply_tax_calculations(distributions)
assert result[0].tax_calculation_applied == False
assert "composite exemption" in result[0].exemption_reason
```

### Step 4: Integration with Excel Service

**Duration**: 1 hour

1. **Extend ExcelService** (`backend/src/services/excel_service.py`):
   ```python
   async def process_session(self, session_id: str) -> None:
       # Existing distribution parsing logic
       distributions = self._parse_distributions(excel_data)

       # NEW: Check for active SALT rules and apply calculations
       if await self._has_active_salt_rules():
           tax_service = TaxCalculationService(self.db)
           distributions = await tax_service.apply_tax_calculations(distributions)

       # Store updated distributions
       await self._store_distributions(session_id, distributions)
   ```

2. **Add SALT Rule Detection**:
   ```python
   async def _has_active_salt_rules(self) -> bool:
       active_rule_set = self.db.query(SaltRuleSet).filter(
           SaltRuleSet.status == SaltRuleSetStatus.ACTIVE
       ).first()
       return active_rule_set is not None
   ```

**Validation**:
```python
# Integration test
session_id = await excel_service.process_session(test_session_id)
session = db.query(UserSession).filter_by(session_id=session_id).first()
assert session.distributions[0].tax_calculation_applied == True
```

### Step 5: API Endpoint Extensions

**Duration**: 1 hour

1. **Extend Session Endpoint** (`backend/src/api/sessions.py`):
   ```python
   @router.get("/{session_id}", response_model=SessionWithTaxCalculationsResponse)
   async def get_session_with_taxes(session_id: str, db: Session = Depends(get_db)):
       # Load session with tax calculation data
       # Include tax calculation summary if applicable
       pass
   ```

2. **Add Audit Report Endpoint**:
   ```python
   @router.get("/{session_id}/audit-report")
   async def get_audit_report(
       session_id: str,
       format: str = Query("json", regex="^(json|excel)$"),
       db: Session = Depends(get_db)
   ):
       # Generate audit report in requested format
       pass
   ```

**Validation**:
```bash
# Test API endpoints
curl http://localhost:8000/api/sessions/{session_id}
# Should return extended response with tax fields

curl http://localhost:8000/api/sessions/{session_id}/audit-report
# Should return detailed audit report
```

### Step 6: Frontend Component Extensions

**Duration**: 2 hours

1. **Extend ResultsModal** (`frontend/src/components/ResultsModal.tsx`):
   ```typescript
   interface ResultsModalProps {
     session: SessionWithTaxCalculations;
     // ... existing props
   }

   const ResultsModal: React.FC<ResultsModalProps> = ({ session, ...props }) => {
     const hasTaxCalculations = session.has_tax_calculations;

     return (
       <Modal>
         {hasTaxCalculations ? (
           <TaxResultsTable distributions={session.distributions} />
         ) : (
           <ExemptionResultsTable distributions={session.distributions} />
         )}
       </Modal>
     );
   };
   ```

2. **Create TaxResultsTable Component**:
   ```typescript
   const TaxResultsTable: React.FC<TaxResultsTableProps> = ({ distributions }) => {
     const columns = useMemo(() => {
       return [
         { key: 'investor_name', label: 'Investor' },
         { key: 'jurisdiction', label: 'Jurisdiction' },
         { key: 'amount', label: 'Amount', type: 'currency' },
         { key: 'withholding_tax_tx', label: 'Withholding Tax TX', type: 'currency' },
         { key: 'composite_tax_tx', label: 'Composite Tax TX', type: 'currency' },
         // Dynamic columns based on available states
       ];
     }, [distributions]);
   };
   ```

3. **Add Audit Report Download**:
   ```typescript
   const handleDownloadAuditReport = async () => {
     const response = await api.downloadAuditReport(session.session_id, 'excel');
     downloadFile(response.blob, response.filename);
   };
   ```

**Validation**:
```bash
# Start frontend development server
cd frontend
npm run dev

# Navigate to results modal and verify:
# - Tax amounts display instead of exemption flags when applicable
# - Download audit report button appears
# - Modal shows appropriate content based on tax calculation status
```

### Step 7: End-to-End Testing

**Duration**: 1.5 hours

1. **Create Integration Test** (`backend/tests/integration/test_tax_calculation_workflow.py`):
   ```python
   async def test_complete_tax_calculation_workflow():
       # Upload file with distribution data
       # Verify SALT rules are applied
       # Check tax calculations in response
       # Validate audit trail
       pass
   ```

2. **Add Frontend E2E Test** (`frontend/tests/e2e/tax-calculation.spec.ts`):
   ```typescript
   test('tax calculation end-to-end workflow', async ({ page }) => {
     // Upload file
     // Wait for processing
     // Open results modal
     // Verify tax amounts display
     // Download audit report
   });
   ```

3. **Performance Validation**:
   ```python
   # Test with larger dataset (100 distributions)
   # Verify processing completes within 30 minutes
   # Check memory usage stays within limits
   ```

**Validation**:
```bash
# Run all tests
cd backend && pytest tests/integration/test_tax_calculation_workflow.py
cd frontend && npm run test:e2e
```

## Testing Scenarios

### Scenario 1: Full Tax Calculation

**Setup**:
- Active SALT rule set with TX, NM, CO rules
- Upload file with 10 distributions across multiple jurisdictions
- Mix of entity types (LLC, Corp, Partnership)

**Expected Results**:
- Tax calculations applied to non-exempt distributions
- Composite tax calculated for mandatory filing states
- Withholding tax calculated for remaining distributions
- Audit trail created for all calculations

### Scenario 2: Exemption Handling

**Setup**:
- Distributions with composite_exemption=true
- Distributions where jurisdiction matches investor tax state

**Expected Results**:
- Exempted distributions show no tax calculations
- exemption_reason field populated appropriately
- Non-exempt distributions processed normally

### Scenario 3: Missing Rules

**Setup**:
- Distributions for jurisdictions without SALT rules
- Entity types not covered by rule set

**Expected Results**:
- Graceful handling of missing rules
- Clear error reporting
- Partial calculation for available rules

## Troubleshooting

### Common Issues

1. **Migration Fails**:
   ```bash
   # Check for existing data conflicts
   SELECT COUNT(*) FROM distributions WHERE tax_calculation_applied IS NULL;

   # Apply default values if needed
   UPDATE distributions SET tax_calculation_applied = false WHERE tax_calculation_applied IS NULL;
   ```

2. **Tax Calculations Not Applied**:
   ```python
   # Verify active SALT rule set exists
   active_rules = db.query(SaltRuleSet).filter_by(status='active').first()
   if not active_rules:
       print("No active SALT rule set found")
   ```

3. **Frontend Modal Not Showing Tax Columns**:
   ```typescript
   // Check session data structure
   console.log('Session has_tax_calculations:', session.has_tax_calculations);
   console.log('Distributions with taxes:', session.distributions.filter(d => d.tax_calculation_applied));
   ```

### Debug Commands

```bash
# Backend logs
docker-compose logs backend | grep "tax_calculation"

# Database inspection
sqlite3 backend/data/fundflow.db
.tables
PRAGMA table_info(distributions);

# Frontend development
npm run dev -- --host --debug
```

## Success Criteria

✅ **Database**: New fields and audit table created successfully
✅ **Tax Calculation**: 3-step algorithm processes distributions correctly
✅ **Integration**: Excel upload pipeline includes tax calculations
✅ **API**: Extended endpoints return tax data and audit reports
✅ **Frontend**: Modal displays tax amounts instead of exemption flags
✅ **Audit**: Detailed reports generated for compliance
✅ **Testing**: All integration and E2E tests pass
✅ **Performance**: Processing completes within existing time constraints

## Next Steps

After successful implementation:

1. **User Acceptance Testing**: Deploy to staging for partner validation
2. **Performance Optimization**: Profile and optimize for larger datasets
3. **Documentation Updates**: Update user guides and API documentation
4. **Monitoring**: Add tax calculation metrics to observability stack

---
*Quickstart guide created: 2025-09-21*
*Implementation ready to begin*