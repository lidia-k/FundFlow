# ADR-0001: Choose Monolithic Architecture over Library-First for v1.2 Prototype

## Status
Accepted

## Date
2025-09-15

## Context

FundFlow v1.2 is an AI-powered PE back-office automation prototype designed to validate user experience and data processing workflow with 2-3 test partner clients by Q1 2026. The primary goal is to solve manual SALT (State and Local Tax) calculation challenges through Excel file upload, processing, and results generation.

During architectural planning, we considered two approaches:

1. **Library-First Principle** (from spec-kit): Every feature must begin as a standalone library with minimal dependencies, forcing modular design from the start
2. **Monolithic Application**: Traditional 3-tier web application with FastAPI backend and React frontend

The Library-First principle offers benefits like modularity, reusability, and cleaner separation of concerns, but comes with additional complexity and development overhead.

## Decision

We will implement FundFlow v1.2 as a **monolithic application** with pragmatic organization, deferring complex architectural patterns until we better understand the domain and requirements.

The monolith will follow simple, conventional patterns:
- Standard FastAPI application structure with clear separation of concerns
- Business logic in service modules, but not necessarily framework-agnostic
- Focus on working software over architectural purity
- Organize code for readability and maintainability rather than future extraction

## Rationale

### 1. **Prototype-Specific Goals**
- Primary objective is user experience validation, not technical architecture
- Need fast time-to-feedback with 2-3 test partners
- Requirements are still evolving and boundaries are unknown

### 2. **Development Velocity**
- Monolithic approach: ~35-40 tasks → Working prototype in 2-3 weeks
- Library-First approach: ~50-60 tasks → Same functionality in 4-5 weeks
- User feedback loop can start 2+ weeks earlier with monolithic approach

### 3. **Complexity vs. Value Trade-off**
Library-First adds significant overhead at prototype stage:
- Library versioning and dependency management
- Inter-library communication contracts
- Package publishing and distribution
- More complex testing setup
- Development environment complexity

The value is minimal since:
- No other consumers of these libraries yet
- No proven need for independent deployability
- Business logic still evolving rapidly

### 4. **Unknown Requirements Problem**
We don't yet know which boundaries matter most in the PE domain:
- Will SALT calculation need to be reused elsewhere? (Unknown)
- Should Excel processing be generic or PE-specific? (Unknown)
- What's the optimal granularity for libraries? (Unknown)
- Which business rules will prove most complex and need isolation? (Unknown)

Premature abstraction based on assumptions could create wrong boundaries that are harder to change than monolithic code. It's better to discover the natural boundaries through implementation and user feedback.

### 5. **Team Cognitive Load Management**
The prototype phase involves learning multiple complex domains simultaneously:
- Learning PE domain complexities (SALT rules, fund structures, distribution flows)
- Understanding user workflow pain points (Tax Director needs, back-office processes)
- Implementing file processing logic (Excel formats, validation rules, error handling)
- Building web application (FastAPI + React integration, real-time progress)

Adding architectural complexity (library design, packaging, inter-library contracts) reduces focus on these core problems. The team's mental capacity is better invested in understanding the business domain rather than managing library abstractions.

### 6. **Migration Path Exists**
Well-organized monolithic services can become libraries with minimal code changes:
```python
# v1.2 Monolith
backend/app/services/salt_calculation/engine.py

# v1.3 Library - same code!
libs/salt-calculator/src/salt_calculator/engine.py
```

The architectural investment isn't lost - it's deferred until we have better information.

## Consequences

### Positive
- **Faster user feedback**: Can validate user experience 2+ weeks earlier
- **Reduced cognitive load**: Focus on PE domain and user workflow rather than library architecture
- **Lower development overhead**: Single deployment, debugging, and development workflow
- **Risk mitigation**: Learn which boundaries matter most before committing to library structure
- **Team simplicity**: Easier coordination with small team

### Negative
- **Future refactoring required**: Will need to extract libraries for v1.3 microservices transition
- **Potential technical debt**: If service boundaries aren't maintained properly
- **Limited reusability**: Business logic cannot be easily reused in other contexts during prototype phase

### Neutral
- **Refactoring will inform better architecture**: Learning from prototype implementation will guide v1.3 design
- **Testing remains pragmatic**: Focus on integration and user workflow tests over pure unit testing

## Alternatives Considered

### 1. Library-First from Start
**Pros**: Perfect modularity, immediate reusability, clean boundaries
**Cons**: 40% more development tasks, delayed user feedback, premature abstraction risk
**Rejected because**: Optimization target is user validation, not technical architecture

### 2. Microservices from Start
**Pros**: Ultimate scalability and independence
**Cons**: Massive complexity overhead, operational challenges, network latency
**Rejected because**: Inappropriate for prototype scale and team size

### 3. Hybrid Approach (Some Libraries)
**Pros**: Selective modularity for obvious boundaries
**Cons**: Inconsistent architecture, partial complexity without full benefits
**Rejected because**: Creates architectural inconsistency and cognitive overhead

## Implementation Guidelines

For the prototype, prioritize simplicity and conventional patterns:

1. **Service Organization**:
   ```
   services/
   ├── upload_service.py        # File upload and storage
   ├── excel_service.py         # Excel parsing and validation
   ├── salt_service.py          # Tax calculations
   └── results_service.py       # Results generation and export
   ```

2. **Pragmatic Structure**:
   - Use FastAPI dependencies and SQLAlchemy where convenient
   - Focus on working code over architectural purity
   - Optimize for readability and debugging ease
   - Let natural boundaries emerge through implementation

3. **Learning Checkpoints**:
   After Epic 1, evaluate what we've learned:
   - Which parts of the system are most complex?
   - What are the natural data boundaries?
   - Where do users experience the most friction?
   - Which components would benefit from isolation in v1.3?

## References

- [FundFlow PRD v1.2](../../../prototype/v1.2/FundFlow%20PRD%20v1.2.md)
- [FundFlow TDD v1.2](../../../prototype/v1.2/FundFlow%20TDD%20v1.2.md)
- [Clean Architecture Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Library-First Principle](https://github.com/specify/specify-kit) - spec-kit library

## Related Decisions

- ADR-0002: FastAPI over Flask (planned)
- ADR-0003: SQLite for prototype storage (planned)
- ADR-0004: Microservices transition strategy for v1.3 (future)