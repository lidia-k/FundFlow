# Research: Simple File Upload & Data Validation

**Feature**: Epic 1 - Simple File Upload & Data Validation
**Date**: 2025-09-14

## Technology Research

### Backend Framework: FastAPI
**Decision**: FastAPI with Python 3.11
**Rationale**:
- Automatic API documentation (OpenAPI/Swagger)
- Native async/await support for potential future enhancements
- Type hints integration with Pydantic for validation
- Mature ecosystem with pandas/openpyxl for Excel processing
- Alignment with TDD v1.2 specifications

**Alternatives considered**:
- Flask: Simpler but lacks automatic documentation and type validation
- Django: Too heavy for prototype requirements

### Frontend Framework: React 18 + TypeScript
**Decision**: React 18 with TypeScript, Vite build tool, Tailwind CSS
**Rationale**:
- Component-based architecture for reusable UI elements (upload, progress, tables)
- TypeScript provides type safety for API integration
- Vite offers fast development with HMR
- Tailwind CSS enables rapid UI development with Shadcn components
- Strong ecosystem for file upload and data visualization

**Alternatives considered**:
- Vue.js: Smaller learning curve but less ecosystem for enterprise features
- Vanilla JavaScript: Faster initial setup but slower development for complex UI

### Excel Processing: pandas + openpyxl
**Decision**: pandas 2.1.3 + openpyxl 3.1.2
**Rationale**:
- pandas.read_excel() handles Excel parsing robustly
- openpyxl supports .xlsx format with formula evaluation
- Built-in data validation and transformation capabilities
- Memory-efficient for prototype scale (50k rows max)
- Mature library with extensive documentation

**Alternatives considered**:
- xlrd/xlwt: Limited to .xls format, deprecated for .xlsx
- PyExcel: Less mature, smaller community

### Database: SQLite
**Decision**: SQLite with SQLAlchemy ORM
**Rationale**:
- File-based database perfect for prototype deployment
- ACID compliance for data consistency
- No separate database server setup required
- SQLAlchemy provides ORM abstraction for future database migration
- Docker volume mounting for data persistence

**Alternatives considered**:
- PostgreSQL: Requires separate container, overkill for prototype
- In-memory storage: Data loss on restart, not suitable for persistence

### UI Component Library: Shadcn/ui
**Decision**: Shadcn/ui with Radix UI primitives
**Rationale**:
- Copy-paste components (no runtime dependency)
- Built on Radix UI for accessibility
- Tailwind CSS integration
- Comprehensive form components for file upload/validation
- Modern design system suitable for business applications

**Alternatives considered**:
- Material-UI: Heavy runtime dependency, opinionated design
- Chakra UI: Good alternative but less business-focused

### File Upload Strategy
**Decision**: Multipart form upload with client-side validation
**Rationale**:
- HTML5 drag-and-drop for UX
- Client-side file type/size validation for immediate feedback
- Server-side validation for security
- Progress tracking via upload events
- Secure temporary file handling

**Alternatives considered**:
- Base64 encoding: Inefficient for large files (10MB limit)
- Chunked upload: Unnecessary complexity for prototype scale

### Testing Strategy
**Decision**: Unit → Contract → Integration → E2E test ordering
**Rationale**:
- Unit tests provide fast feedback for validation logic and business rules
- Contract tests validate API specifications and frontend-backend compatibility
- Integration tests cover critical file upload → database flow with real dependencies
- Playwright E2E tests validate complete user scenarios
- Test pyramid approach: many fast unit tests, fewer expensive integration/E2E tests

**Alternatives considered**:
- Contract-first testing: Slower feedback loop during development
- Mock-heavy approach: Misses integration issues critical for file processing

## Architecture Patterns

### Validation Pipeline
**Decision**: Multi-stage validation with error collection
**Rationale**:
- Stage 1: File format and size validation
- Stage 2: Header presence and normalization
- Stage 3: Row-level data type and business rule validation
- Stage 4: Cross-row duplicate detection
- Collect all errors before returning (don't fail fast)

### Progress Reporting
**Decision**: Server-sent events or polling for progress updates
**Rationale**:
- Real-time feedback essential for 30-minute processing window
- Progress percentages mapped to processing stages
- Error state handling with frozen progress bars
- Backend progress tracking in memory (prototype simplicity)

### Error Handling
**Decision**: Structured error objects with severity levels
**Rationale**:
- Errors include row, column, code, message, severity
- Filterable and exportable error reports
- Differentiate between warnings and blocking errors
- Support for multiple errors per row

## Security Considerations

### File Processing Security
**Decision**: Server-side validation with sandboxed processing
**Rationale**:
- Never trust client-side validation alone
- Temporary file cleanup after processing
- File type validation beyond extension checking
- Memory limits for Excel processing (pandas chunking if needed)

### PII Handling
**Decision**: Minimal PII retention with secure processing
**Rationale**:
- Process files in memory when possible
- Temporary file storage with secure cleanup
- No long-term storage of raw uploaded files
- Database stores only processed/validated results

## Performance Optimization

### Excel Processing
**Decision**: Synchronous processing with progress feedback
**Rationale**:
- Prototype simplicity over async complexity
- 30-minute timeout sufficient for 10MB/50k row limits
- Memory-efficient pandas operations
- Single-threaded processing acceptable for 3-5 concurrent users

### Database Operations
**Decision**: Bulk upsert operations with SQLAlchemy
**Rationale**:
- Batch insert/update for performance
- Database transactions for consistency
- Prepared statements for security
- Connection pooling for concurrent users

## Integration Points

### Frontend-Backend Communication
**Decision**: REST API with JSON payloads
**Rationale**:
- Standard HTTP patterns for file upload
- JSON for data exchange (progress, results, errors)
- OpenAPI documentation for contract clarity
- CORS configuration for cross-origin requests

### Database Schema Design
**Decision**: Normalized schema with minimal relationships
**Rationale**:
- Separate tables for users, sessions, rules, calculations
- Foreign key relationships for data integrity
- Indexes on query-heavy columns
- Simple schema suitable for SQLite limitations

## Risk Mitigation

### File Processing Risks
- **Risk**: Memory exhaustion on large files
- **Mitigation**: File size limits (10MB) + row limits (50k) + chunked processing if needed

### Data Quality Risks
- **Risk**: Invalid data corrupting calculations
- **Mitigation**: Multi-stage validation + error collection + user review before save

### Performance Risks
- **Risk**: Slow processing frustrating users
- **Mitigation**: Progress feedback + realistic expectations (30min limit) + optimization focus

### Security Risks
- **Risk**: File upload vulnerabilities
- **Mitigation**: Server-side validation + temporary file handling + secure cleanup