# FundFlow Architecture Documentation

This directory contains architectural documentation for the FundFlow project, organized following industry-standard patterns.

## Architecture Decision Records (ADRs)

ADRs document significant architectural decisions made during development, providing context and rationale for future reference.

### Active Decisions

| ADR | Title | Status | Date | Summary |
|-----|-------|--------|------|---------|
| [0001](decisions/0001-monolithic-vs-library-first.md) | Monolithic vs Library-First Architecture | Accepted | 2025-09-15 | Choose monolithic approach for v1.2 prototype to optimize for user validation speed |

### Upcoming Decisions

- ADR-0002: FastAPI over Flask
- ADR-0003: SQLite for prototype storage
- ADR-0004: Microservices transition strategy for v1.3

## Architecture Overview

### Current State (v1.2 Prototype)
- **Pattern**: Monolithic 3-tier web application
- **Backend**: Python 3.11 + FastAPI + SQLite
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Processing**: Synchronous file processing with pandas + openpyxl
- **Deployment**: Docker + Docker Compose

### Future State (v1.3+ Production)
- **Pattern**: Microservices with extracted domain libraries
- **Architecture**: Library-first with service composition
- **Scalability**: Independent service scaling and deployment

## Guidelines

### Making Architecture Decisions

1. **Document Significant Decisions**: Use ADR format for choices that affect:
   - Technology selection
   - Structural organization
   - Integration patterns
   - Quality attribute trade-offs

2. **ADR Process**:
   - Copy template from `decisions/template.md`
   - Number sequentially (0001, 0002, etc.)
   - Include alternatives considered
   - Document consequences (positive and negative)
   - Update this index

3. **Review Cycle**:
   - All ADRs should be reviewed before implementation
   - Update status from "Proposed" → "Accepted" → "Superseded" as needed
   - Reference related ADRs for context

### Architecture Principles (v1.2)

1. **Simplicity Over Complexity**: Optimize for prototype validation speed
2. **Clean Boundaries**: Organize code for future library extraction
3. **Test-Driven Development**: RED-GREEN-Refactor cycle enforced
4. **Progressive Architecture**: Add complexity as value becomes clear

### Migration Strategy

The monolithic v1.2 is designed to enable smooth transition to library-first v1.3:

```
v1.2 Services → v1.3 Libraries
├── excel_processing/ → libs/excel-processor/
├── salt_calculation/ → libs/salt-calculator/
└── file_management/ → libs/file-validator/
```

## Diagrams

Architecture diagrams are stored in the `diagrams/` directory:

- System context diagrams
- Component interaction diagrams
- Data flow diagrams
- Deployment diagrams

## Resources

### Internal Documentation
- [Project Overview](../../claude.md)
- [Product Requirements](../../prototype/v1.2/FundFlow%20PRD%20v1.2.md)
- [Technical Design](../../prototype/v1.2/FundFlow%20TDD%20v1.2.md)

### External References
- [Architecture Decision Records](https://adr.github.io/) - ADR format and tools
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Microservices Patterns](https://microservices.io/patterns/index.html)

---

*For questions about architectural decisions or to propose new ADRs, please refer to the development team.*