# FundFlow Prototype Constitution (v1.0)

**Ratified:** 2025-09-17 | **Last Amended:** 2025-09-17  

---

## Core Principles

### Simplicity First
- Apply **YAGNI**: build only what’s needed.  
- Extend existing projects, avoid over-engineering.  
- Validate user workflows before optimizing performance.  

### Test-First (Non-Negotiable)
- **Order:** Unit → Contract → Integration → E2E → Implementation.  
- Write tests first (Red-Green-Refactor).  
- All merges require passing tests and proof of the TDD cycle.  
- Spikes allowed only if discarded or covered by tests before merge.  

### Integration Testing Focus
- Validate API contracts, DB ops, component interactions, file processing.  
- Use real dependencies (SQLite, filesystem); in-memory SQLite acceptable fo

### Observability
- JSON-structured logging required.  
- Frontend logs flow to backend.  
- Include error context sufficient for debugging.  

---

## Development Standards

| Area          | Standard |
|---------------|----------|
| **Backend**   | Python 3.11, FastAPI, SQLAlchemy, SQLite |
| **Frontend**  | React 18, TypeScript, Tailwind, Shadcn UI |
| **Testing**   | pytest, Jest, Playwright |
| **Quality**   | black, isort, mypy, ruff; ESLint, Prettier |
| **Perf (Proto)** | ~3–5 concurrent users, ~10MB Excel files |

---

## Quality Gates
- All tests pass before merge.  
- Constitutional compliance check in review.  
- Simplicity > complexity; deviations require a short written rationale.  

---

## Governance
- Constitution overrides all other practices.  
- Amendments require brief rationale + async approval.  