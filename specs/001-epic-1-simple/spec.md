# Feature Specification: Simple File Upload & Data Validation

**Feature Branch**: `001-epic-1-simple`
**Created**: 2025-09-14
**Status**: Draft
**Input**: User description: "# Epic 1 - Simple File Upload & Data Validation

## 0. Scope and constraints

- Input types: .xlsx, .xls
- Max file size: 10 MB
- Max rows parsed: 50,000
- Parse first worksheet only. Target name: `Distribution Data`. If name differs, use index 0.
- SALT master data: already in DB, read-only
- Timezone: America/Los_Angeles
- PII present: treat securely

## 1. User story

As Tax Lead Sarah, I drag and drop a portfolio Excel file, see a progress bar during upload and validation, preview parsed rows and issues, then the platform saves investor and distribution data to the database. If the file is invalid, I download the standard template and fix it.

## 2. Acceptance criteria by requirement

### REQ 1.1 - Drag and drop upload

- Accept only .xlsx and .xls
- Block files over 10 MB client and server side
- Auto start upload on drop or selection

### REQ 1.2 - Auto format validation

- Required source headers in the first sheet:
    - `Investor Name`
    - `Investor Entity Type`
    - `Investor Tax State`
    - `Distribution \nTX and NM`
    - `Distribution \nCO`
- Header normalization:
    - Trim, collapse internal whitespace, convert newlines to single spaces for matching
- Canonical fields mapped:
    - investor_name  Investor Name
    - investor_entity_type  Investor Entity Type
    - investor_tax_state  Investor Tax State
    - distribution_tx_nm  Distribution TX and NM
    - distribution_co  Distribution CO
- Type and value checks:
    - investor_name: non-empty string
    - investor_entity_type: one of

        `Corporation, Exempt Organization, Government Benefit Plan, Individual, Joint Tenancy / Tenancy in Common, LLC_Taxed as Partnership, LLP, Limited Partnership, Partnership, Trust`

    - investor_tax_state: 2-letter US state, DC, uppercase
    - distribution_tx_nm: numeric, >= 0
    - distribution_co: numeric, >= 0
    - At least one of distribution_tx_nm or distribution_co must be > 0
- Number parsing rules:
    - Allow thousands separators, leading/trailing spaces
    - Allow parentheses to indicate negatives, but negatives are invalid and raise `NEGATIVE_AMOUNT`
    - Blank numeric cells are treated as 0
- Duplicate rule:
    - No duplicate investor within the same file by key `(fund_code, investor_name)`
    - Normalize by trim and case-insensitive compare on investor_name
- Output errors as a structured list with `row, column, code, message, severity`

### REQ 1.3 - Real-time progress bar

- States and mapping:
    - `queued` 5
    - `uploading` 5 to 40
    - `parsing` 40 to 70
    - `validating` 70 to 90
    - `saving` 90 to 99
    - `completed` 100
    - Any `failed_*` shows error banner and freezes bar

### REQ 1.4 - Template download

- Button downloads `portfolio_template.xlsx`
- Template contains the 5 canonical columns and 5 sample rows
- Excel data validation:
    - Investor Tax State list: 50 states + DC
    - Investor Entity Type list: the enumeration above

### REQ 1.5 - Data preview

- Show first 100 valid rows in a grid after `completed`
- Separate Issues tab with filter by severity and code
- CSV export of issues

### REQ 1.6 - Persist investor and distribution data

- On successful validation, save rows to DB
- Summary counts returned: `investors_upserted, distributions_inserted, rows_skipped`
- Idempotency: SHA256 of file bytes. Re-upload of identical file does not reinsert
- Upsert key for investors: `(fund_code, investor_name)`
- For each row, insert or upsert distributions:
    - jurisdiction `TX_NM` with `distribution_tx_nm`
    - jurisdiction `CO` with `distribution_co`

### REQ 1.7 - Metadata extraction from filename

- Filename pattern: `^(?P<fund_code>.+)_(?P<period_quarter>Q[1-4]) (?P<period_year>\d{4}) distribution data\.xlsx`
- Extract and attach to each row: `fund_code, period_quarter, period_year`
- If pattern does not match, raise `INVALID_FILENAME` and abort before parse"

## Execution Flow (main)
```
1. Parse user description from Input
   ’ If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   ’ Identify: actors, actions, data, constraints
3. For each unclear aspect:
   ’ Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   ’ If no clear user flow: ERROR "Cannot determine user scenarios"
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

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As Sarah, a Tax Lead at a PE fund, I need to process quarterly distribution data by uploading Excel files containing investor information and distribution amounts. The system must validate the data format, show me any errors, and save the validated data to the database for SALT calculations. When files have formatting issues, I need to download a correct template to fix them.

### Acceptance Scenarios
1. **Given** I have a properly formatted Excel file named "ABC_Fund_Q3 2024 distribution data.xlsx" containing investor data, **When** I drag and drop it onto the upload area, **Then** the system shows a progress bar, validates the data, displays a preview of 100 rows, and saves all valid investor and distribution records to the database
2. **Given** I upload a file with validation errors (missing required fields, invalid states, negative amounts), **When** the validation completes, **Then** the system shows me an Issues tab with filterable error details and allows me to export the issues as CSV
3. **Given** I need the correct file format, **When** I click the template download button, **Then** I receive "portfolio_template.xlsx" with the 5 required columns, sample data, and Excel data validation dropdowns
4. **Given** I upload the same file twice, **When** the second upload completes, **Then** the system detects the duplicate using file hash and does not create duplicate records

### Edge Cases
- What happens when the filename doesn't match the required pattern? System shows INVALID_FILENAME error and aborts processing
- What happens when file size exceeds 10MB? System blocks upload both client and server side with clear error message
- What happens when the Excel sheet is named differently than "Distribution Data"? System uses the first worksheet (index 0)
- What happens when numeric fields contain parentheses (negative indicators)? System raises NEGATIVE_AMOUNT error as negatives are invalid
- What happens when required headers are missing or misspelled? System shows validation errors with specific missing/incorrect headers

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST accept only .xlsx and .xls file formats for upload
- **FR-002**: System MUST block files over 10MB at both client and server level
- **FR-003**: System MUST auto-start upload immediately when file is dropped or selected
- **FR-004**: System MUST validate filename matches pattern: fund_code_Q[1-4] YYYY distribution data.xlsx
- **FR-005**: System MUST parse first worksheet only, preferring "Distribution Data" sheet name or using index 0
- **FR-006**: System MUST validate presence of exactly 5 required headers: Investor Name, Investor Entity Type, Investor Tax State, Distribution TX and NM, Distribution CO
- **FR-007**: System MUST normalize headers by trimming whitespace, collapsing internal spaces, and converting newlines to single spaces
- **FR-008**: System MUST validate investor_name as non-empty string
- **FR-009**: System MUST validate investor_entity_type against specific enumeration: Corporation, Exempt Organization, Government Benefit Plan, Individual, Joint Tenancy / Tenancy in Common, LLC_Taxed as Partnership, LLP, Limited Partnership, Partnership, Trust
- **FR-010**: System MUST validate investor_tax_state as 2-letter US state code or DC in uppercase
- **FR-011**: System MUST validate distribution amounts as numeric values >= 0, treating blank cells as 0
- **FR-012**: System MUST require at least one distribution amount (TX_NM or CO) to be > 0 per row
- **FR-013**: System MUST allow thousands separators and leading/trailing spaces in numeric fields
- **FR-014**: System MUST treat parentheses as negative indicators and raise NEGATIVE_AMOUNT error
- **FR-015**: System MUST prevent duplicate investors within same file based on (fund_code, investor_name) key with case-insensitive comparison
- **FR-016**: System MUST show real-time progress bar with specific percentage ranges for each processing stage
- **FR-017**: System MUST display progress states: queued (5%), uploading (5-40%), parsing (40-70%), validating (70-90%), saving (90-99%), completed (100%)
- **FR-018**: System MUST show error banner and freeze progress bar for any failed_* states
- **FR-019**: System MUST provide template download button that delivers "portfolio_template.xlsx"
- **FR-020**: Template MUST contain 5 canonical columns with 5 sample data rows
- **FR-021**: Template MUST include Excel data validation dropdowns for state and entity type fields
- **FR-022**: System MUST display preview of first 100 valid rows in grid format after successful processing
- **FR-023**: System MUST provide separate Issues tab with filtering by severity and error code
- **FR-024**: System MUST allow CSV export of validation issues
- **FR-025**: System MUST save validated data to database with upsert logic for investors based on (fund_code, investor_name)
- **FR-026**: System MUST return summary counts: investors_upserted, distributions_inserted, rows_skipped
- **FR-027**: System MUST implement idempotency using SHA256 file hash to prevent duplicate processing
- **FR-028**: System MUST extract and attach metadata (fund_code, period_quarter, period_year) from filename to each row
- **FR-029**: System MUST create distribution records for both TX_NM and CO jurisdictions when amounts > 0
- **FR-030**: System MUST limit processing to maximum 50,000 rows per file

### Key Entities *(include if feature involves data)*
- **Investor**: Represents an investor entity with name, entity type, and tax state. Key for upsert operations and duplicate detection
- **Distribution**: Represents quarterly distribution amounts for specific jurisdictions (TX_NM, CO) tied to investors and fund periods
- **Upload Job**: Represents a file processing operation with status tracking, progress percentage, and error collection
- **Validation Error**: Represents individual data quality issues with row/column location, error code, message, and severity level
- **Fund Period**: Represents quarterly reporting period extracted from filename, containing fund code, quarter, and year information

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