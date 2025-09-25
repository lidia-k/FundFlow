# Feature Specification: Epic 2B  Withholding and Composite Tax Calculation

**Feature Branch**: `003-epic-2b-withholding`
**Created**: 2025-09-21
**Status**: Draft
**Input**: User description: "Epic 2B  Withholding and Composite Tax Calculation

  Important Instruction: Implement exactly the steps below. Do not add extra features, optimizations, or alternative designs. Follow the order and scope as written.

When a user uploads the input data, if an active SALT rule set exists, apply the following logic step by step. The order of steps must be followed strictly. The data required for the calculations (entity type mappings, tax rates, thresholds, mandatory filing flags) is pulled from the database after being saved from the uploaded SALT matrix file.

Step 1. Handle Exemptions

For each distribution of an investor:

If composite exemption OR withholding exemption is true, skip tax calculation.

If the jurisdiction of a distribution is the same as the investor's tax state, skip tax calculation.

Step 2. Calculate Composite Tax (mandatory states only)

For each distribution:

Check if mandatory filing = true for the jurisdiction.

If yes, check if a tax rate exists for (jurisdiction, entity type code).

Match the investor's entity type to the entity type code before calculation.

If an income threshold exists, only calculate tax if the distribution amount > threshold.

Apply the tax rate to calculate composite tax.

Step 3. Calculate Withholding Tax

For each distribution not already covered by composite tax in Step 2:

Check if a tax rate exists for (jurisdiction, entity type code).

If a per-partner income threshold exists, only calculate if the distribution amount > threshold.

Apply the tax rate to calculate withholding tax.

If a per-partner W/H tax threshold exists, only keep the calculated tax if it is > threshold; otherwise discard.

Step 4. Present Results

When a user clicks "View Results":

Show a modal (instead of empty page).

Use the existing input file preview format, but replace "Composite Exemption" and "Withholding Exemption" columns with:

Withholding Tax + {State}

Composite Tax + {State}

Add a Download Report button that generates a detailed report (step-by-step tax calculation breakdown for auditing).

Implementation Notes:

Integrate this logic into the existing data pipeline after distributions are parsed and before rendering the results.

The modal should reuse the preview table component but with extended schema.

The report file should be generated server-side and include traceable details (investor, jurisdiction, applied rules, thresholds, rates, exemption checks)."

## Execution Flow (main)
```
1. Parse user description from Input
   ’ If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   ’ Identified: tax calculation engine, exemption handling, results presentation
3. For each unclear aspect:
   ’ Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   ’ User flow: upload data ’ tax calculation ’ view results ’ download report
5. Generate Functional Requirements
   ’ Each requirement must be testable
   ’ Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   ’ If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   ’ If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ¡ Quick Guidelines
-  Focus on WHAT users need and WHY
- L Avoid HOW to implement (no tech stack, APIs, code structure)
- =e Written for business stakeholders, not developers

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a Tax Director, when I upload investor distribution data and an active SALT rule set exists, I want the system to automatically calculate withholding and composite taxes according to state-specific rules, so that I can generate accurate tax calculations and audit reports for compliance purposes.

### Acceptance Scenarios
1. **Given** a user has uploaded distribution data and an active SALT rule set exists, **When** the system processes the data, **Then** exemptions are checked first and tax calculations are skipped for exempt distributions
2. **Given** a distribution qualifies for composite tax calculation, **When** the jurisdiction has mandatory filing enabled, **Then** composite tax is calculated using the appropriate rate and thresholds
3. **Given** a distribution does not qualify for composite tax, **When** withholding tax rules exist for the jurisdiction and entity type, **Then** withholding tax is calculated with applicable thresholds
4. **Given** tax calculations are complete, **When** the user clicks "View Results", **Then** a modal displays calculated taxes by state instead of exemption flags
5. **Given** the results modal is open, **When** the user clicks "Download Report", **Then** a detailed audit report with calculation breakdowns is generated

### Edge Cases
- What happens when both composite and withholding exemptions are true for the same distribution?
- How does the system handle distributions where jurisdiction equals investor's tax state?
- What occurs when tax rates exist but thresholds are not met?
- How are distributions handled when no active SALT rule set exists?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST check for active SALT rule sets before applying tax calculations
- **FR-002**: System MUST apply exemption logic as the first step, skipping tax calculations when composite exemption OR withholding exemption is true
- **FR-003**: System MUST skip tax calculations when distribution jurisdiction matches investor's tax state
- **FR-004**: System MUST calculate composite tax only for jurisdictions with mandatory filing enabled
- **FR-005**: System MUST match investor entity types to database entity type codes before calculation
- **FR-006**: System MUST apply income thresholds when calculating composite tax, only calculating when distribution amount exceeds threshold
- **FR-007**: System MUST calculate withholding tax for distributions not covered by composite tax calculations
- **FR-008**: System MUST apply per-partner income thresholds for withholding tax calculations
- **FR-009**: System MUST apply per-partner withholding tax thresholds, discarding calculated taxes below the threshold
- **FR-010**: System MUST display results in a modal instead of navigating to an empty page
- **FR-011**: System MUST replace "Composite Exemption" and "Withholding Exemption" columns with calculated tax amounts by state
- **FR-012**: System MUST provide a "Download Report" button that generates detailed audit reports
- **FR-013**: Audit reports MUST include step-by-step calculation breakdowns with investor details, jurisdictions, applied rules, thresholds, rates, and exemption checks

### Key Entities *(include if feature involves data)*
- **SALT Rule Set**: Configuration that determines when tax calculations should be applied, includes active/inactive status
- **Tax Rate**: State-specific rates mapped to entity types and jurisdictions, includes composite and withholding rates
- **Income Threshold**: Minimum distribution amounts required before tax calculation applies, varies by jurisdiction and tax type
- **Withholding Tax Threshold**: Minimum calculated tax amounts that must be met for withholding taxes to be applied
- **Mandatory Filing Flag**: Boolean indicator for jurisdictions that require composite tax filings
- **Entity Type Mapping**: Relationship between investor entity types and standardized entity type codes used in tax calculations
- **Tax Calculation Result**: Computed composite and withholding tax amounts by jurisdiction for each distribution
- **Audit Report**: Detailed breakdown document showing calculation steps, applied rules, and exemption checks for compliance tracking

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---