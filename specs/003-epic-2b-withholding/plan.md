# Implementation Plan: Epic 2B Withholding and Composite Tax Calculation

**Branch**: `003-epic-2b-withholding` | **Date**: 2025-09-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/Users/lidia/FundFlow/specs/003-epic-2b-withholding/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ COMPLETE - Feature spec loaded and analyzed
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ COMPLETE - Technical context filled from existing codebase analysis
3. Evaluate Constitution Check section below
   → ✅ COMPLETE - Constitution compliance verified
4. Execute Phase 0 → research.md
   → ✅ COMPLETE - Research completed
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → ✅ COMPLETE - Design artifacts generated
6. Re-evaluate Constitution Check section
   → ✅ COMPLETE - Post-design constitution check passed
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
   → ✅ COMPLETE - Task generation approach planned
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
**Primary Requirement**: Implement multi-step tax calculation engine that processes investor distributions through exemption checks, composite tax calculations (mandatory states), and withholding tax calculations, with enhanced results presentation modal and detailed audit report generation.

**Technical Approach**: Extend existing SALT rule system (Epic 2A) to integrate calculation engine with current file upload pipeline, modifying results presentation to show calculated taxes instead of exemption flags, using existing React modal components and backend Excel export capabilities.

## Technical Context
**Language/Version**: Python 3.11 (existing FastAPI backend), TypeScript 5.0+ (existing React frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy, pandas, openpyxl, React 18, Tailwind CSS (all existing)
**Storage**: SQLite with existing SALT rule tables from Epic 2A (salt_rule_set, withholding_rule, composite_rule)
**Testing**: pytest (backend), Jest + React Testing Library (frontend), Playwright (E2E) - all existing
**Target Platform**: Linux server (Docker containerized), modern web browsers
**Project Type**: web - existing 3-tier architecture (frontend + backend)
**Performance Goals**: ~3-5 concurrent users, <30min processing for 10MB Excel files (existing constraints)
**Constraints**: Synchronous processing (existing limitation), integration with current upload pipeline
**Scale/Scope**: ~10 portfolio companies, ~20 LPs per file (existing prototype constraints)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 2 (backend + frontend, existing structure)
- Using framework directly? ✅ Yes (FastAPI, React, no wrapper classes)
- Single data model? ✅ Yes (extending existing distribution model, no DTOs)
- Avoiding patterns? ✅ Yes (using existing service pattern from Epic 2A)

**Architecture**:
- EVERY feature as library? ✅ Yes (TaxCalculationService extends existing services/ library)
- Libraries listed: ExcelService (existing), TaxCalculationService (new), ValidationService (existing)
- CLI per library: N/A (web application, existing API endpoints)
- Library docs: ✅ Yes (llms.txt format planned in existing structure)

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? ✅ Yes (following existing TDD practices)
- Git commits show tests before implementation? ✅ Yes (constitutional requirement)
- Order: Contract→Integration→E2E→Unit strictly followed? ✅ Yes
- Real dependencies used? ✅ Yes (SQLite, filesystem - existing approach)
- Integration tests for: new libraries, contract changes, shared schemas? ✅ Yes
- FORBIDDEN: Implementation before test, skipping RED phase ✅ Acknowledged

**Observability**:
- Structured logging included? ✅ Yes (extending existing logging)
- Frontend logs → backend? ✅ Yes (existing pattern)
- Error context sufficient? ✅ Yes (following existing error handling)

**Versioning**:
- Version number assigned? ✅ Yes (Epic 2B extends existing v1.2 prototype)
- BUILD increments on every change? ✅ Yes (following existing git workflow)
- Breaking changes handled? ✅ Yes (backward compatible extensions)

## Project Structure

### Documentation (this feature)
```
specs/003-epic-2b-withholding/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 2: Web application (existing structure)
backend/
├── src/
│   ├── models/          # Extend existing Distribution model
│   ├── services/        # New TaxCalculationService + extend ExcelService
│   └── api/             # Extend existing sessions endpoints
└── tests/               # New tax calculation tests

frontend/
├── src/
│   ├── components/      # Extend existing ResultsModal, add TaxResultsTable
│   ├── pages/           # Extend existing Results page
│   └── services/        # Extend existing API client
└── tests/               # New frontend calculation tests
```

**Structure Decision**: Option 2 (web application) - using existing frontend + backend structure

## Phase 0: Outline & Research

**Research Goals**:
1. **Tax Calculation Algorithms**: Research best practices for multi-step tax calculations with exemptions and thresholds
2. **Integration Patterns**: Analyze how to integrate calculation engine with existing upload pipeline
3. **Modal Enhancement**: Investigate extending existing ResultsModal for tax display
4. **Report Generation**: Research audit report generation patterns for tax compliance

**Key Research Areas**:
- Tax calculation sequencing and validation patterns
- Integration with existing ExcelService and SessionService
- Frontend modal component extension strategies
- Backend Excel export with detailed audit trails

**Output**: research.md with architectural decisions and integration approaches

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

**Design Artifacts**:
1. **Data Model Extensions**: Extend Distribution model with tax calculation fields
2. **API Contract Extensions**: Modify existing sessions endpoints for tax display
3. **Tax Calculation Service**: Core business logic following Epic 2A patterns
4. **Frontend Component Extensions**: Enhanced ResultsModal and TaxResultsTable

**Contract Generation**:
- Extend GET /api/sessions/{id} response schema with tax calculation fields
- Add GET /api/sessions/{id}/audit-report endpoint for detailed reports
- Modify frontend ResultsModal component interface

**Test Generation**:
- Contract tests for extended API responses
- Integration tests for complete tax calculation workflow
- Unit tests for TaxCalculationService business logic

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, updated CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Extend existing endpoints rather than create new ones (YAGNI principle)
- Focus on integration with existing Epic 2A SALT rule system

**Ordering Strategy**:
- TDD order: Contract tests → Integration tests → Unit tests → Implementation
- Dependency order: Data model extensions → Service layer → API layer → Frontend
- Leverage existing infrastructure: ExcelService, SessionService, ResultsModal components

**Estimated Output**: 20-25 numbered, ordered tasks in tasks.md

**Key Task Categories**:
1. Data model extensions (2-3 tasks)
2. TaxCalculationService implementation (5-6 tasks)
3. API endpoint extensions (3-4 tasks)
4. Frontend component enhancements (4-5 tasks)
5. Integration and validation (4-6 tasks)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No constitutional violations identified - all extensions follow existing patterns*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) - research.md generated
- [x] Phase 1: Design complete (/plan command) - data-model.md, contracts/, quickstart.md, CLAUDE.md updated
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (None)

**Generated Artifacts**:
- [x] `/specs/003-epic-2b-withholding/plan.md` - This implementation plan
- [x] `/specs/003-epic-2b-withholding/research.md` - Architectural research and decisions
- [x] `/specs/003-epic-2b-withholding/data-model.md` - Data model extensions and schemas
- [x] `/specs/003-epic-2b-withholding/quickstart.md` - Step-by-step implementation guide
- [x] `/specs/003-epic-2b-withholding/contracts/api-extensions.yaml` - OpenAPI contract extensions
- [x] `/specs/003-epic-2b-withholding/contracts/frontend-interfaces.ts` - TypeScript interface definitions
- [x] `/Users/lidia/FundFlow/CLAUDE.md` - Updated with Epic 2B context

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*