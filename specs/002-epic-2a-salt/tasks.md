# Tasks: SALT Rules Ingestion & Publishing

**Input**: Design documents from `/specs/002-epic-2a-salt/`
**Prerequisites**: research.md (✅), data-model.md (✅), contracts/api-spec.yaml (✅), quickstart.md (✅)

## Execution Flow (main)
```
1. Load design documents ✅
   → Tech stack: FastAPI + SQLAlchemy + pandas/openpyxl + React/Shadcn
   → Entities: SourceFile, SaltRuleSet, WithholdingRule, CompositeRule, ValidationIssue, StateEntityTaxRuleResolved
   → API endpoints: 6 endpoints across upload, validation, preview, publish, list, detail, delete
   → Test scenarios: upload → validate → preview → publish workflow

2. Generate tasks by category:
   → Setup: Project structure, dependencies, database
   → Tests: 6 contract tests, 4 integration tests (TDD approach)
   → Core: 6 models, services, Excel processing, validation pipeline
   → Integration: Database operations, file handling, API endpoints
   → Polish: Unit tests, error handling, performance validation

3. Task dependencies and parallel execution marked with [P]
4. All tasks numbered T001-T033 with specific file paths
```

## Phase 3.1: Setup
- [ ] T001 Create backend project structure with FastAPI, SQLAlchemy, pandas dependencies in backend/
- [ ] T002 Initialize database schema with Alembic migrations in backend/alembic/
- [ ] T003 [P] Configure linting (ruff) and formatting tools for backend/
- [ ] T004 [P] Set up file storage directory structure for uploaded Excel files

## Phase 3.2: Unit Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3 ✅
**CRITICAL: Unit tests MUST be written and MUST FAIL before ANY implementation**
- [x] T005 [P] Unit test SourceFile model validation in backend/tests/unit/test_source_file.py
- [x] T006 [P] Unit test SaltRuleSet model validation in backend/tests/unit/test_salt_rule_set.py
- [x] T007 [P] Unit test WithholdingRule model validation in backend/tests/unit/test_withholding_rule.py
- [x] T008 [P] Unit test CompositeRule model validation in backend/tests/unit/test_composite_rule.py
- [x] T009 [P] Unit test ValidationIssue model validation in backend/tests/unit/test_validation_issue.py
- [x] T010 [P] Unit test StateEntityTaxRuleResolved model in backend/tests/unit/test_resolved_rule.py
- [x] T011 [P] Unit test Excel processing service logic in backend/tests/unit/test_excel_processor.py
- [x] T012 [P] Unit test validation pipeline service in backend/tests/unit/test_validation_service.py
- [x] T013 [P] Unit test file service SHA256 hashing in backend/tests/unit/test_file_service.py
- [x] T014 [P] Unit test rule comparison service logic in backend/tests/unit/test_comparison_service.py

## Phase 3.3: Contract Tests ⚠️ MUST COMPLETE BEFORE 3.4 ✅
**CRITICAL: Contract tests MUST be written and MUST FAIL before implementation**
- [x] T015 [P] Contract test POST /api/salt-rules/upload in backend/tests/contract/test_upload_endpoint.py
- [x] T016 [P] Contract test GET /api/salt-rules/{ruleSetId}/validation in backend/tests/contract/test_validation_endpoint.py
- [x] T017 [P] Contract test GET /api/salt-rules/{ruleSetId}/preview in backend/tests/contract/test_preview_endpoint.py
- [x] T018 [P] Contract test POST /api/salt-rules/{ruleSetId}/publish in backend/tests/contract/test_publish_endpoint.py
- [x] T019 [P] Contract test GET /api/salt-rules in backend/tests/contract/test_list_endpoint.py
- [x] T020 [P] Contract test GET /api/salt-rules/{ruleSetId} in backend/tests/contract/test_detail_endpoint.py

## Phase 3.4: Integration Tests ⚠️ MUST COMPLETE BEFORE 3.5 ✅
**CRITICAL: Integration tests MUST be written and MUST FAIL before implementation**
- [x] T021 [P] Integration test complete upload → validate → preview → publish workflow in backend/tests/integration/test_complete_workflow.py
- [x] T022 [P] Integration test error handling with invalid Excel files in backend/tests/integration/test_error_scenarios.py
- [x] T023 [P] Integration test duplicate file detection in backend/tests/integration/test_duplicate_detection.py

## Phase 3.5: E2E Tests ⚠️ MUST COMPLETE BEFORE 3.6 ✅
**CRITICAL: E2E tests MUST be written and MUST FAIL before implementation**
- [x] T024 [P] E2E test performance with 20MB files in backend/tests/e2e/test_performance.py

## Phase 3.6: Core Implementation (ONLY after ALL tests are failing)
- [x] T025 [P] SourceFile model in backend/src/models/source_file.py
- [x] T026 [P] SaltRuleSet model in backend/src/models/salt_rule_set.py
- [x] T027 [P] WithholdingRule model in backend/src/models/withholding_rule.py
- [x] T028 [P] CompositeRule model in backend/src/models/composite_rule.py
- [x] T029 [P] ValidationIssue model in backend/src/models/validation_issue.py
- [x] T030 [P] StateEntityTaxRuleResolved model in backend/src/models/resolved_rule.py
- [x] T031 [P] Excel processing service with pandas/openpyxl in backend/src/services/excel_processor.py
- [x] T032 [P] Validation pipeline service in backend/src/services/validation_service.py
- [x] T033 [P] File storage service with SHA256 hashing in backend/src/services/file_service.py
- [x] T034 [P] Rule comparison service for diff preview in backend/src/services/comparison_service.py
- [x] T035 POST /api/salt-rules/upload endpoint implementation
- [x] T036 GET /api/salt-rules/{ruleSetId}/validation endpoint implementation
- [x] T037 GET /api/salt-rules/{ruleSetId}/preview endpoint implementation
- [x] T038 POST /api/salt-rules/{ruleSetId}/publish endpoint implementation
- [x] T039 GET /api/salt-rules endpoint implementation
- [x] T040 GET /api/salt-rules/{ruleSetId} endpoint implementation

## Phase 3.7: Database Integration
- [x] T041 Database operations for rule set lifecycle management
- [x] T042 Resolved rules table generation on publish
- [x] T043 CSV export functionality for validation results

## Phase 3.8: Polish
- [ ] T044 Error handling and structured logging implementation
- [ ] T045 Performance optimization for large file processing
- [ ] T046 Run quickstart.md test scenarios for validation

## Dependencies
- Setup (T001-T004) before everything
- Unit tests (T005-T014) before contract tests (T015-T020)
- Contract tests (T015-T020) before integration tests (T021-T023)
- Integration tests (T021-T023) before E2E tests (T024)
- All tests (T005-T024) before implementation (T025-T040)
- Models (T025-T030) before services (T031-T034)
- Services before endpoints (T035-T040)
- Implementation before database integration (T041-T043)
- All functionality before polish (T044-T046)

## Parallel Example
```bash
# Launch unit tests together (T005-T010):
Task: "Unit test SourceFile model validation in backend/tests/unit/test_source_file.py"
Task: "Unit test SaltRuleSet model validation in backend/tests/unit/test_salt_rule_set.py"
Task: "Unit test WithholdingRule model validation in backend/tests/unit/test_withholding_rule.py"
Task: "Unit test CompositeRule model validation in backend/tests/unit/test_composite_rule.py"
Task: "Unit test ValidationIssue model validation in backend/tests/unit/test_validation_issue.py"
Task: "Unit test StateEntityTaxRuleResolved model in backend/tests/unit/test_resolved_rule.py"

# Launch contract tests together (T015-T020):
Task: "Contract test POST /api/salt-rules/upload in backend/tests/contract/test_upload_endpoint.py"
Task: "Contract test GET /api/salt-rules/{ruleSetId}/validation in backend/tests/contract/test_validation_endpoint.py"
Task: "Contract test GET /api/salt-rules/{ruleSetId}/preview in backend/tests/contract/test_preview_endpoint.py"
Task: "Contract test POST /api/salt-rules/{ruleSetId}/publish in backend/tests/contract/test_publish_endpoint.py"
Task: "Contract test GET /api/salt-rules in backend/tests/contract/test_list_endpoint.py"
Task: "Contract test GET /api/salt-rules/{ruleSetId} in backend/tests/contract/test_detail_endpoint.py"

# Launch model creation together (T025-T030):
Task: "SourceFile model in backend/src/models/source_file.py"
Task: "SaltRuleSet model in backend/src/models/salt_rule_set.py"
Task: "WithholdingRule model in backend/src/models/withholding_rule.py"
Task: "CompositeRule model in backend/src/models/composite_rule.py"
Task: "ValidationIssue model in backend/src/models/validation_issue.py"
Task: "StateEntityTaxRuleResolved model in backend/src/models/resolved_rule.py"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing (TDD approach)
- Commit after each task completion
- Tech stack: FastAPI + SQLAlchemy + pandas + openpyxl + React + Shadcn UI
- Focus on admin-only Excel upload and validation workflow
- Support 20MB files with sub-30-second processing time

## Task Generation Rules Applied
1. **From API Contract** (6 endpoints):
   - Each endpoint → contract test task [P] (T005-T010)
   - Each endpoint → implementation task (T025-T030)

2. **From Data Model** (6 entities):
   - Each entity → model creation task [P] (T015-T020)
   - Service layer for business logic (T021-T024)

3. **From User Stories** (quickstart.md):
   - Complete workflow → integration test [P] (T011)
   - Error scenarios → integration test [P] (T012-T014)
   - Performance requirements → integration test [P] (T014)

4. **Ordering Applied**:
   - Setup → Tests → Models → Services → Endpoints → Integration → Polish
   - TDD: All tests written before implementation
   - Dependencies prevent inappropriate parallelization

## Validation Checklist ✅
- [x] All 6 entities have unit tests (T005-T010) and model tasks (T025-T030)
- [x] All 4 services have unit tests (T011-T014) and implementation tasks (T031-T034)
- [x] All 6 API endpoints have contract tests (T015-T020) and implementation tasks (T035-T040)
- [x] Proper TDD order: Unit → Contract → Integration → E2E → Implementation
- [x] Unit tests (T005-T014) before contract tests (T015-T020)
- [x] Contract tests before integration tests (T021-T023)
- [x] Integration tests before E2E tests (T024)
- [x] All tests (T005-T024) before implementation (T025-T040)
- [x] Parallel tasks are truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] Complete workflow from upload to publish covered