# Implementation Plan: Simple File Upload & Data Validation

**Branch**: `001-epic-1-simple` | **Date**: 2025-09-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-epic-1-simple/spec.md`

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
Implement drag-and-drop Excel file upload system with real-time validation for PE fund distribution data. System must parse investor and distribution information, validate against specific business rules, provide progress feedback, handle errors gracefully, and save validated data to SQLite database. Includes template download functionality and data preview with issues export.

## Technical Context
**Language/Version**: Python 3.11 (backend), TypeScript/React 18 (frontend)
**Primary Dependencies**: FastAPI (backend), React + Vite + Tailwind CSS (frontend), pandas + openpyxl (Excel processing)
**Storage**: SQLite (file-based database), File system (uploads/results), Docker volumes
**Testing**: pytest (backend), Jest + React Testing Library (frontend), Playwright (E2E)
**Target Platform**: Docker containers (Linux), web browsers (modern)
**Project Type**: web - determines source structure (backend + frontend)
**Performance Goals**: 10MB Excel files in 30 minutes, 50,000 rows max, 3-5 concurrent users
**Constraints**: File size limit 10MB, real-time progress updates, synchronous processing, secure PII handling
**Scale/Scope**: Prototype level - 10 portfolio companies, 20 LPs, 2-3 test partner validation

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 2 (backend API, frontend SPA)
- Using framework directly? ✅ FastAPI + React without custom wrappers
- Single data model? ✅ Pydantic models for API, direct SQLAlchemy ORM
- Avoiding patterns? ✅ Direct service layer, no Repository/UoW for prototype simplicity

**Architecture**:
- EVERY feature as library? ⚠️ DEFERRED - Prototype approach: direct service modules
- Libraries listed: N/A for prototype phase, will refactor in v1.3
- CLI per library: N/A for web application
- Library docs: N/A for prototype phase

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? ✅ Tests written first, must fail before implementation
- Git commits show tests before implementation? ✅ Will enforce in task execution
- Order: Unit→Contract→Integration→E2E tests before implementation? ✅ Planned in Phase 1
- Real dependencies used? ✅ Actual SQLite database, real file system, Playwright for E2E
- Integration tests for: new libraries, contract changes, shared schemas? ✅ Upload flow, validation pipeline
- FORBIDDEN: Implementation before test, skipping RED phase ✅ Will be enforced

**Observability**:
- Structured logging included? ✅ JSON format logging as per TDD
- Frontend logs → backend? ✅ Error tracking and progress reporting
- Error context sufficient? ✅ Structured validation errors with row/column/code/severity

**Versioning**:
- Version number assigned? ✅ 1.2.0 (prototype version)
- BUILD increments on every change? ✅ Will track in development
- Breaking changes handled? ✅ Prototype scope - major changes expected in v1.3

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

**Structure Decision**: Option 2 (Web application) - FastAPI backend + React frontend as indicated by Technical Context

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
- Database models tasks: User, UserSession, Investor, Distribution, ValidationError, EYSALTRule [P]
- API contract tests: Upload, Progress, Results, Template endpoints [P]
- Excel processing pipeline: File validation, parsing, business rules, error collection
- Frontend UI tasks: Upload component with Shadcn, Progress tracking, Results display, Error handling
- Integration tests: Complete upload-to-storage workflow validation
- E2E tests: Playwright scenarios matching quickstart validation steps

**Ordering Strategy**:
- TDD order: Unit tests → Contract tests → Integration tests → E2E tests → Implementation
- Dependency order: Database models → Services → API endpoints → Frontend components
- Mark [P] for parallel execution: Independent model files, separate API endpoints, UI components
- Critical path: Excel processing pipeline (sequential validation stages)

**Estimated Output**: 35-40 numbered, ordered tasks in tasks.md covering:
- 6 database model tasks [P]
- 8 contract test tasks [P]
- 12 implementation tasks (validation pipeline, API endpoints)
- 8 frontend tasks (components, integration)
- 6 testing tasks (E2E scenarios, performance validation)

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
- [x] Phase 0: Research complete (/plan command) - research.md generated with technology decisions
- [x] Phase 1: Design complete (/plan command) - data-model.md, contracts/, quickstart.md created
- [x] Phase 2: Task planning complete (/plan command - describe approach only) - 35-40 task strategy defined
- [x] Phase 3: Tasks generated (/tasks command)
- [x] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (with documented prototype deviations)
- [x] Post-Design Constitution Check: PASS (architecture suitable for prototype phase)
- [x] All NEEDS CLARIFICATION resolved (no ambiguities found in technical context)
- [x] Complexity deviations documented (library-first approach deferred to v1.3)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*