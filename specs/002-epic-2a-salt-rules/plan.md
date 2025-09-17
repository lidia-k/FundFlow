# Implementation Plan: Epic 2A - SALT Rules Ingestion & Publishing


**Branch**: `002-epic-2a-salt-rules` | **Date**: 2025-09-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/Users/lidia/FundFlow/specs/002-epic-2a-salt-rules/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, or `GEMINI.md` for Gemini CLI).
6. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Epic 2A implements a comprehensive SALT rules management system enabling Tax Admins to upload EY SALT rule workbooks (.xlsx/.xlsm), validate and parse them into structured data, stage draft rule sets, and publish them as versioned, active rule sets. The system generates a read-only Resolved Rules table optimized for fast calculations by combining withholding and composite rules data. Technical approach uses existing FastAPI backend with SQLAlchemy for database modeling, pandas/openpyxl for Excel processing, and React frontend with file upload UI.

## Technical Context
**Language/Version**: Python 3.11+ (backend), TypeScript 5.2+ (frontend)
**Primary Dependencies**: FastAPI 0.104+, SQLAlchemy 2.0+, pandas 2.1+, openpyxl 3.1+, React 18+, Vite 4.5+
**Storage**: SQLite (development), PostgreSQL (production), local file system for Excel uploads
**Testing**: pytest + pytest-asyncio (backend), Jest + React Testing Library (frontend)
**Target Platform**: Linux/Docker containers, web browsers (modern)
**Project Type**: web - existing frontend + backend structure
**Performance Goals**: <30min upload-to-publish for typical workbooks (~2k rules), <2sec rule lookup queries
**Constraints**: Excel files ≤20MB, America/Los_Angeles timezone, admin-only access, draft→active versioning
**Scale/Scope**: 3-5 concurrent admin users, ~2000 rules per workbook, 51 states × 10 entity types coverage

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 3 (backend API, frontend UI, integration tests) ✓
- Using framework directly? Yes - FastAPI/React without wrapper abstractions ✓
- Single data model? Yes - SQLAlchemy models serve as both domain and persistence ✓
- Avoiding patterns? No Repository/UoW - direct service layer to ORM ✓

**Architecture**:
- EVERY feature as library? Yes - salt_rules service library, excel_parser library, rule_validator library
- Libraries listed: salt_rules_service (business logic), excel_parser (file processing), rule_validator (validation logic)
- CLI per library: Each library provides CLI interface for standalone testing ✓
- Library docs: llms.txt format planned for each library ✓

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? Yes - contract tests written first ✓
- Git commits show tests before implementation? Yes - test commits precede implementation ✓
- Order: Contract→Integration→E2E→Unit strictly followed? Yes ✓
- Real dependencies used? Yes - actual SQLite/PostgreSQL, real Excel files ✓
- Integration tests for: New salt_rules_service library, file upload contracts, database schema changes ✓
- FORBIDDEN: Implementation before test, skipping RED phase ✓

**Observability**:
- Structured logging included? Yes - structlog for all operations ✓
- Frontend logs → backend? Yes - API error tracking, audit trail ✓
- Error context sufficient? Yes - validation issues with row/column context ✓

**Versioning**:
- Version number assigned? v2.1.0 (MAJOR: new domain, MINOR: rule management, BUILD: iterations) ✓
- BUILD increments on every change? Yes ✓
- Breaking changes handled? Migration plan for new database tables, backward compatibility ✓

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: Option 2 (Web application) - using existing backend/ and frontend/ structure

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `/scripts/bash/update-agent-context.sh claude` for your AI assistant
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Library-first approach: salt_rules_service, excel_parser, rule_validator libraries
- Each API endpoint → contract test task [P]
- Each entity (SourceFile, SaltRuleSet, etc.) → model creation task [P]
- Each user story → integration test scenario
- Implementation tasks following TDD: RED-GREEN-Refactor cycle

**Ordering Strategy**:
- Constitutional TDD order: Contract→Integration→E2E→Unit tests before implementation
- Dependency order:
  1. Database models (SourceFile, SaltRuleSet, Rules)
  2. Core libraries (excel_parser, rule_validator)
  3. Service layer (salt_rules_service)
  4. API endpoints (admin APIs, engine APIs)
  5. Frontend components (upload UI, validation display)
- Mark [P] for parallel execution within phases
- Real dependencies: SQLite database, actual Excel files

**Library Structure**:
- `backend/app/libs/excel_parser/` - Excel parsing and normalization
- `backend/app/libs/rule_validator/` - Multi-layer validation engine
- `backend/app/libs/salt_rules_service/` - Business logic and workflow
- Each library includes CLI interface for standalone testing

**Test Data Requirements**:
- fixtures/excel/valid_salt_rules_2025_q1.xlsx - Complete valid workbook
- fixtures/excel/invalid_* variants for error path testing
- Reference data: 51 states, 10 entity types from Epic 1
- Known-good validation scenarios for each error code

**Performance Validation Tasks**:
- Large file handling (2000+ rules, <30min processing)
- Concurrent access testing (3-5 admin users)
- Query performance validation (<2sec resolved rules lookup)

**Integration Points**:
- Epic 1 entity_types table integration
- Existing file upload infrastructure reuse
- Admin authentication system integration
- Audit logging consistency with existing patterns

**Estimated Output**: 35-40 numbered, ordered tasks in tasks.md

**Key Constitutional Compliance**:
- Every feature implemented as testable library
- RED-GREEN-Refactor cycle strictly enforced
- Real dependencies used (no mocking of SQLAlchemy/pandas)
- Structured logging throughout
- CLI interfaces for all libraries

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✅ 2025-09-17
- [x] Phase 1: Design complete (/plan command) ✅ 2025-09-17
- [x] Phase 2: Task planning complete (/plan command - describe approach only) ✅ 2025-09-17
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS ✅ No violations found
- [x] Post-Design Constitution Check: PASS ✅ Library architecture confirmed
- [x] All NEEDS CLARIFICATION resolved ✅ Technical context complete
- [x] Complexity deviations documented ✅ No deviations required

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*