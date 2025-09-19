# Tasks: Simple File Upload & Data Validation

**Input**: Design documents from `/specs/001-epic-1-simple/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Tech stack: FastAPI backend, React frontend, SQLite, pandas/openpyxl
   → Structure: Web application (backend/ + frontend/)
2. Load design documents:
   → data-model.md: 6 entities (User, UserSession, Investor, Distribution, ValidationError, EYSALTRule)
   → contracts/api-spec.yaml: 5 endpoints (upload, results, download, template, health)
   → research.md: Technology decisions and best practices
3. Generate tasks by TDD category order
4. Apply parallelization for independent files
5. Number tasks sequentially (T001-T040)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app structure**: `backend/src/`, `frontend/src/`
- Tests: `backend/tests/`, `frontend/tests/`

## Phase 3.1: Setup

- [x] T001 Create backend project structure and FastAPI dependencies in backend/
- [x] T002 Create frontend project structure with React 18 + TypeScript + Vite in frontend/
- [x] T003 [P] Configure backend linting (black, isort, mypy, ruff) in backend/pyproject.toml
- [x] T004 [P] Configure frontend linting (ESLint, Prettier) in frontend/.eslintrc.js
- [x] T005 [P] Setup Docker environment with docker-compose.yml
- [x] T006 Initialize SQLite database schema and migrations in backend/src/database/

## Phase 3.2: Tests First (OPTIONAL FOR PROTOTYPE - Priority 2)
**NOTE: For rapid prototyping, skip comprehensive testing initially. Add after MVP is working.**

### Unit Tests (Business Logic Validation) - **SKIP FOR MVP**
- [ ] T007 [P] Unit test Excel parsing validation in backend/tests/unit/test_excel_parser.py
- [ ] T008 [P] Unit test investor entity validation in backend/tests/unit/test_investor_validation.py
- [ ] T009 [P] Unit test distribution calculation in backend/tests/unit/test_distribution_calculation.py
- [ ] T010 [P] Unit test exemption field conversion in backend/tests/unit/test_exemption_conversion.py

### Contract Tests (API Endpoint Validation) - **SKIP FOR MVP**
- [ ] T011 [P] Contract test POST /api/upload in backend/tests/contract/test_upload_post.py
- [ ] T012 [P] Contract test GET /api/results/{session_id} in backend/tests/contract/test_results_get.py
- [ ] T013 [P] Contract test GET /api/results/{session_id}/download in backend/tests/contract/test_download_get.py
- [ ] T014 [P] Contract test GET /api/template in backend/tests/contract/test_template_get.py
- [ ] T015 [P] Contract test GET /api/health in backend/tests/contract/test_health_get.py

### Integration Tests (Complete Workflows) - **SKIP FOR MVP**
- [ ] T016 [P] Integration test Excel upload to database flow in backend/tests/integration/test_upload_workflow.py
- [ ] T017 [P] Integration test investor persistence across sessions in backend/tests/integration/test_investor_persistence.py
- [ ] T018 [P] Integration test exemption field processing in backend/tests/integration/test_exemption_processing.py
- [ ] T019 [P] Integration test validation error collection in backend/tests/integration/test_validation_errors.py

## Phase 3.3: Database Models (Priority 1 - Core MVP)

- [x] T020 [P] User model in backend/src/models/user.py
- [x] T021 [P] UserSession model with state transitions in backend/src/models/user_session.py
- [x] T022 [P] Investor model with persistence logic in backend/src/models/investor.py
- [x] T023 [P] Distribution model with exemption fields in backend/src/models/distribution.py
- [x] T024 [P] ValidationError model in backend/src/models/validation_error.py

## Phase 3.4: Core Services (Priority 1 - Core MVP)

- [x] T026 Excel file validation and parsing service in backend/src/services/excel_service.py
- [x] T027 Investor upsert service (find or create) in backend/src/services/investor_service.py
- [x] T028 Distribution processing service with exemptions in backend/src/services/distribution_service.py
- [x] T029 Validation error collection service in backend/src/services/validation_service.py
- [x] T030 Session management service in backend/src/services/session_service.py

## Phase 3.5: API Endpoints (Priority 1 - Core MVP)

- [x] T031 POST /api/upload endpoint with file processing in backend/src/api/upload.py
- [x] T032 GET /api/results/{session_id} endpoint in backend/src/api/results.py
- [x] T033 GET /api/results/{session_id}/download endpoint in backend/src/api/download.py
- [x] T034 GET /api/template endpoint in backend/src/api/template.py
- [x] T035 GET /api/health endpoint in backend/src/api/health.py

## Phase 3.6: Frontend Components (Priority 1 - Core MVP)

- [x] T036 [P] File upload component with drag-and-drop in frontend/src/components/FileUpload.tsx
- [x] T037 [P] Progress tracking component in frontend/src/components/ProgressTracker.tsx
- [x] T038 [P] Results display component with data grid in frontend/src/components/ResultsDisplay.tsx
- [x] T039 [P] Error handling component in frontend/src/components/ErrorDisplay.tsx

## Phase 3.7: E2E Validation (Priority 1 - Core MVP)

- [x] T040 [P] E2E test complete upload workflow with Playwright in frontend/tests/e2e/test_upload_workflow.spec.ts

## Dependencies

### Critical Path for MVP (Sequential)
- Setup (T001-T006) before all implementation
- Models (T020-T024) before services (T026-T030)
- Services (T026-T030) before endpoints (T031-T035)
- Backend endpoints before frontend components (T036-T039)
- Complete flow before E2E validation (T040)

### Testing Path (Priority 2 - Add After MVP)
- Tests (T007-T019) can be added later for robustness

### Parallel Opportunities for MVP
- Models T020-T024 can run together (different files)
- Frontend components T036-T039 can run together (different files)

### Testing Parallelization (Priority 2)
- Unit tests T007-T010 can run together (different files)
- Contract tests T011-T015 can run together (different files)
- Integration tests T016-T019 can run together (different files)

## Parallel Execution Examples

### MVP Phase - Database Models (Run Together):
```bash
# Launch T020-T024 together for rapid parallel development:
Task: "User model in backend/src/models/user.py"
Task: "UserSession model with state transitions in backend/src/models/user_session.py"
Task: "Investor model with persistence logic in backend/src/models/investor.py"
Task: "Distribution model with exemption fields in backend/src/models/distribution.py"
Task: "ValidationError model in backend/src/models/validation_error.py"
```

### MVP Phase - Frontend Components (Run Together):
```bash
# Launch T036-T039 together for rapid parallel development:
Task: "File upload component with drag-and-drop in frontend/src/components/FileUpload.tsx"
Task: "Progress tracking component in frontend/src/components/ProgressTracker.tsx"
Task: "Results display component with data grid in frontend/src/components/ResultsDisplay.tsx"
Task: "Error handling component in frontend/src/components/ErrorDisplay.tsx"
```

### Testing Phase (Priority 2 - Optional):
```bash
# Launch T007-T010 together when adding unit testing:
Task: "Unit test Excel parsing validation in backend/tests/unit/test_excel_parser.py"
Task: "Unit test investor entity validation in backend/tests/unit/test_investor_validation.py"
Task: "Unit test distribution calculation in backend/tests/unit/test_distribution_calculation.py"
Task: "Unit test exemption field conversion in backend/tests/unit/test_exemption_conversion.py"

# Launch T011-T015 together when adding contract testing:
Task: "Contract test POST /api/upload in backend/tests/contract/test_upload_post.py"
Task: "Contract test GET /api/results/{session_id} in backend/tests/contract/test_results_get.py"
Task: "Contract test GET /api/results/{session_id}/download in backend/tests/contract/test_download_get.py"
Task: "Contract test GET /api/template in backend/tests/contract/test_template_get.py"
Task: "Contract test GET /api/health in backend/tests/contract/test_health_get.py"
```

## Key Implementation Notes

### Prototype Development Approach
- **MVP Focus**: Skip comprehensive testing initially (T007-T019) to get working prototype fast
- **Manual Testing**: Use browser and Postman to verify functionality during development
- **Add Testing Later**: Once MVP is working, add comprehensive test suite for robustness

### Data Model Specifics
- Investor entities are persistent across upload sessions
- Distribution records include composite_exemption and withholding_exemption boolean fields
- Exemption mapping: "Exemption" → True, all else → False
- Support for 9-column Excel format (4 new exemption columns)

### API Contract Requirements
- File upload limited to 10MB with .xlsx/.xls validation
- Real-time progress updates during processing
- Structured validation error responses with row/column/code/severity
- Session-based result retrieval with UUID session IDs

### Frontend Requirements
- Drag-and-drop file upload with Shadcn components
- Real-time progress bar showing processing states
- Data preview grid for first 100 valid rows
- Error export functionality (CSV format)
- Template download button

## Validation Checklist
*GATE: Checked before task execution*

- [ ] All contracts have corresponding tests (T011-T015)
- [x] All entities have model tasks (T020-T024)
- [x] MVP tasks prioritized (T020-T040) before comprehensive testing (T007-T019)
- [x] Parallel tasks truly independent (different files marked [P])
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Complete workflow coverage from upload to results display
- [x] Prototype order optimized: Setup → Models → Services → Endpoints → Frontend → E2E

## Prototype-Focused Timeline (Rapid MVP)

**Priority 1: Core MVP (4-6 hours)**
- **Phase 3.1 Setup**: 30 minutes (T001-T006)
- **Phase 3.3 Models**: 45 minutes (T020-T024) [P]
- **Phase 3.4 Services**: 90 minutes (T026-T030)
- **Phase 3.5 Endpoints**: 60 minutes (T031-T035)
- **Phase 3.6 Frontend**: 90 minutes (T036-T039) [P]
- **Phase 3.7 Integration**: 15 minutes (T040)

**Priority 2: Testing & Polish (Optional - Add Later)**
- **Phase 3.2 Comprehensive Tests**: 2-3 hours (T007-T019) - Skip for initial prototype

**Total MVP Duration**: ~5.5 hours for working end-to-end prototype

## Summary
Generated **39 implementation tasks** with **prototype-focused prioritization**:

**Priority 1 (MVP - 5.5 hours)**: 19 core tasks (T001-T006, T020-T024, T026-T040)
- ✅ Working end-to-end file upload and processing
- ✅ Basic validation and error handling
- ✅ Simple UI for upload, progress, and results

**Priority 2 (Testing - 2-3 hours)**: 13 test tasks (T007-T019)
- ✅ Comprehensive test coverage
- ✅ Contract validation
- ✅ Robust error scenarios

**Approach**: Get working prototype first, add comprehensive testing second. Perfect for rapid MVP validation with potential for robust production later.