# Feature Specification: SALT Rules Ingestion & Publishing

**Feature Branch**: `002-epic-2a-salt`
**Created**: 2025-09-17
**Status**: Draft
**Input**: User description: "Epic 2A  SALT Rules Ingestion & Publishing: When a user uploads the EY SALT rule workbook (.xlsx/.xlsm), ingest, validate, stage, and publish a versioned Rule Set into the database, and generate a readonly Resolved Rules table for fast/traceable calculations (to be used by Epic 2B)."

## Execution Flow (main)
```
1. Parse user description from Input
   ’ Feature allows tax admins to upload SALT rule workbooks and publish versioned rule sets
2. Extract key concepts from description
   ’ Actors: Tax Admins, Reviewers, Engineers
   ’ Actions: Upload, validate, stage, publish, diff comparison
   ’ Data: Excel workbooks, withholding/composite rules, resolved rules table
   ’ Constraints: Admin-only access, 20MB file limit, versioning by Year/Quarter
3. For each unclear aspect:
   ’ All aspects clearly defined in detailed feature description
4. Fill User Scenarios & Testing section
   ’ Upload workflow, validation, staging, and publishing scenarios identified
5. Generate Functional Requirements
   ’ File handling, parsing, validation, versioning, and UI requirements
6. Identify Key Entities
   ’ Source files, rule sets, withholding rules, composite rules, resolved rules
7. Run Review Checklist
   ’ All sections complete, focused on user value, no implementation details
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
As a Tax Admin, I need to upload EY SALT rule workbooks containing withholding and composite tax rules, validate the data for accuracy, preview changes against currently active rules, and publish versioned rule sets that the calculation engine can use to determine tax obligations for investor distributions.

### Acceptance Scenarios
1. **Given** I have an EY SALT rule workbook (.xlsx/.xlsm), **When** I upload it with Year 2025 and Quarter Q1, **Then** the system validates the file format, parses both withholding and composite rule sheets, and creates a draft rule set
2. **Given** my uploaded workbook has validation errors (duplicate state-entity combinations, invalid rates), **When** I review the validation results, **Then** I can see detailed error messages with row/sheet references and download a CSV report of all issues
3. **Given** my uploaded workbook passes validation, **When** I preview the staged rules, **Then** I can see a comparison showing which rules are new, changed, or removed compared to the currently active rule set
4. **Given** I have a valid draft rule set, **When** I publish it, **Then** the system marks it as active, archives any previous active rule set for the same period, and generates a resolved rules table combining both withholding and composite data
5. **Given** I need to review rule set history, **When** I access the admin interface, **Then** I can see all rule sets with their status (draft/active/archived) and effective periods

### Edge Cases
- What happens when I upload the same file (identical SHA256) for the same Year/Quarter? System should detect idempotency and show info message without creating duplicate
- How does system handle malformed Excel files or missing required sheets? System should reject with clear error messages
- What happens when I try to publish a rule set when another active rule set exists for the same period? System should either reject or auto-archive the existing one based on configuration
- How does system handle partial data (missing states or entity types)? System should show coverage gaps as warnings or errors based on policy settings

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST accept only .xlsx and .xlsm file formats, rejecting all other file types with clear error messages
- **FR-002**: System MUST compute SHA256 hash of uploaded files and detect identical files for the same Year/Quarter to prevent duplicate processing
- **FR-003**: System MUST parse Excel workbooks with flexible header normalization (case-insensitive, whitespace handling, synonym mapping)
- **FR-004**: System MUST validate that all state codes exist in reference table and all entity types match canonical codes from Epic 1
- **FR-005**: System MUST detect and reject duplicate state-entity combinations within the same sheet
- **FR-006**: System MUST validate that all rates and thresholds are non-negative numeric values, rejecting negative values indicated by parentheses
- **FR-007**: System MUST provide detailed validation results showing row, sheet, field, error code, message, and severity for each issue
- **FR-008**: System MUST allow downloading validation results as CSV file for external review and documentation
- **FR-009**: System MUST create draft rule sets that can be previewed before publishing
- **FR-010**: System MUST show comparison (diff) between draft rule set and currently active rule set, highlighting added, changed, and removed rules at field level
- **FR-011**: System MUST prevent publishing rule sets that contain any validation errors (only warnings allowed)
- **FR-012**: System MUST enforce exactly one active rule set per Year/Quarter combination through database constraints
- **FR-013**: System MUST generate resolved rules table that combines withholding and composite rule data for efficient calculation queries
- **FR-014**: System MUST track rule set lifecycle with status transitions (draft ’ active ’ archived)
- **FR-015**: System MUST provide admin interface for uploading files, reviewing validation results, previewing staged rules, and publishing rule sets
- **FR-016**: System MUST maintain audit trail of all import and publish operations with timestamp and user information
- **FR-017**: System MUST support rule set versioning by Year and Quarter with automatic effective date calculation
- **FR-018**: System MUST handle file size limit of 20MB for uploaded workbooks
- **FR-019**: System MUST map state full names to 2-letter codes and entity type labels to canonical codes during parsing
- **FR-020**: System MUST store source file metadata including filename, filepath, SHA256, and upload timestamp

### Key Entities *(include if feature involves data)*
- **Source Files**: Uploaded Excel workbooks with metadata (filename, filepath, SHA256 hash, upload timestamp) for deduplication and audit trail
- **Rule Sets**: Versioned collections of SALT rules identified by Year/Quarter with lifecycle status (draft/active/archived) and effective date ranges
- **Withholding Rules**: Tax withholding rates and thresholds by state and entity type, including income thresholds and tax thresholds for exemption calculations
- **Composite Rules**: Composite tax rates and thresholds by state and entity type, including mandatory filing flags and income thresholds
- **Resolved Rules**: Read-only denormalized table combining withholding and composite rule data for efficient calculation queries, with provenance tracking
- **Validation Issues**: Structured error and warning records with row/sheet references, error codes, and severity levels for user feedback
- **States**: Reference table of 51 US states and DC with 2-letter codes and full names for validation and mapping
- **Entity Types**: Canonical entity type codes and labels matching Epic 1 investor classification system

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