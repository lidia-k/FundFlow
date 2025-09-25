# FundFlow - AI-Powered PE Back-Office Automation Platform (v1.2.1)

## Project Overview
FundFlow is an AI-powered automation platform designed to solve manual SALT (State and Local Tax) calculation challenges for Private Equity fund back-office operations. This prototype version (v1.2) focuses on validating the core workflow of Excel file upload, SALT calculation, and results generation without complex API integrations.

**Key Goal**: Validate user experience and data processing workflow with 2-3 test partner clients by Q1 2026.

## Key Documents
- PRD: `prototype/v1.2/FundFlow PRD v1.2.md` - Product requirements focused on simplified Excel upload workflow with pre-stored EY SALT data
- TDD: `prototype/v1.2/FundFlow TDD v1.2.md` - Technical design using traditional 3-tier web architecture with Python Flask + React
- Architecture Decisions: `docs/architecture/` - Architectural decision records and design documentation

## Project Structure
```
FundFlow/
├── backend/                 # FastAPI backend application
│   ├── app/                # FastAPI app configuration
│   │   ├── core/           # Core configuration and utilities
│   │   └── main.py         # FastAPI application entry point
│   ├── src/                # Source code (main implementation)
│   │   ├── api/            # API route handlers (upload, results, health, etc.)
│   │   ├── database/       # Database connection and setup
│   │   ├── models/         # Pydantic models and data schemas
│   │   └── services/       # Business logic and SALT calculations
│   ├── data/               # Data storage and uploads
│   │   └── uploads/        # Uploaded Excel files
│   ├── tests/              # Backend tests (pytest)
│   ├── alembic/            # Database migrations
│   ├── requirements.txt    # Python dependencies
│   └── pyproject.toml      # Python project configuration
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # Reusable React components
│   │   │   └── ui/         # Shadcn UI components
│   │   ├── pages/          # Page components (Upload, Dashboard, Results)
│   │   ├── api/            # API client utilities
│   │   ├── hooks/          # Custom React hooks
│   │   ├── types/          # TypeScript type definitions
│   │   └── utils/          # Frontend utility functions
│   ├── tests/              # Frontend tests (Jest + Playwright)
│   │   ├── e2e/            # End-to-end tests
│   │   └── fixtures/       # Test data and fixtures
│   ├── public/             # Static assets
│   └── package.json        # Node.js dependencies
├── shared/                 # Shared code between frontend/backend
│   ├── types/              # Shared TypeScript types
│   └── utils/              # Shared utility functions
├── docker/                 # Docker configuration files
├── specs/                  # Project specifications and documentation
├── docs/                   # Project documentation
├── data/                   # Sample data and templates
├── scripts/                # Development and deployment scripts
├── archive/                # Archived files
├── .specify/               # Specify AI configuration
├── .serena/                # Serena MCP configuration
├── .claude/                # Claude Code configuration
├── docker-compose.yml      # Development environment
├── docker-compose.override.yml  # Local development overrides
├── Makefile               # Development commands
└── package.json           # Root package.json for shared dependencies
```

## Architecture Overview
**Simplified 3-Tier Web Application (Monolithic)**
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS (Single Page Application)
- **Backend**: Python 3.11 + FastAPI + SQLite (synchronous processing)
- **File Processing**: pandas + openpyxl for Excel handling
- **Storage**: Local file system with SQLite database
- **Deployment**: Docker + Docker Compose for development

**Key Design Principles**:
1. Simplicity over complexity. Apply **YAGNI**: build only what’s needed.  
2. Rapid prototyping for user feedback
3. User experience validation focus
4. Future scalability considerations
5. Clean service boundaries (preparing for v1.3 library extraction)

**Architecture Decisions**: See [Architecture Decision Records](docs/architecture/README.md) for detailed rationale behind design choices.

## Tech Stack & Dependencies
### Backend
- **Framework**: FastAPI 0.104+ (async/await support)
- **Database**: SQLite with SQLAlchemy ORM
- **File Processing**: pandas 2.0+, openpyxl 3.1+ (Excel parsing and validation)
- **Validation**: Pydantic v2, structured error collection
- **Testing**: pytest, pytest-asyncio, real dependencies (SQLite, filesystem)
- **Code Quality**: black, isort, mypy, ruff

### Frontend
- **Framework**: React 18 + TypeScript 5.0+
- **Build Tool**: Vite 4.0+
- **Styling**: Tailwind CSS 3.3+
- **HTTP Client**: axios
- **Testing**: Jest, React Testing Library
- **Code Quality**: ESLint, Prettier

## API Reference
### Core Upload & Results Endpoints
- `POST /api/upload` - Upload Excel file for processing
- `GET /api/results/{session_id}` - Get processing results and status
- `GET /api/results/{session_id}/preview` - Preview processing results with mode support
- `GET /api/results/{session_id}/download` - Download results as Excel
- `GET /api/results/{session_id}/download-errors` - Download validation errors
- `GET /api/results/{session_id}/report` - Download detailed tax calculation audit report
- `GET /api/template` - Download Excel template
- `GET /api/sessions` - List all user sessions
- `GET /api/health` - Health check
- `GET /api/health/simple` - Simple health check

### SALT Rule Management Endpoints
- `POST /api/salt-rules/upload` - Upload SALT rule workbooks for processing
- `GET /api/salt-rules` - List rule sets with filtering and pagination
- `GET /api/salt-rules/{id}` - Get detailed rule set information
- `GET /api/salt-rules/{id}/validation` - Get validation results (JSON/CSV)
- `GET /api/salt-rules/{id}/preview` - Preview rule changes vs current active
- `GET /api/salt-rules/template` - Download SALT rules template

### Data Models
#### Core Models
- **UserSession**: Upload session tracking with status and progress
- **Investor**: Persistent investor entities with name, entity type, and tax state
- **Distribution**: Quarterly distribution amounts by jurisdiction with tax calculations
- **ValidationError**: File validation errors with severity levels
- **UploadStatus**: Enum for tracking upload/processing stages

#### SALT Rule Models
- **SaltRuleSet**: Version-controlled SALT rule collections with lifecycle management
- **WithholdingRule**: Individual withholding tax rules by state and entity type
- **CompositeRule**: Composite tax rates and filing requirements
- **SourceFile**: Uploaded file tracking with SHA256 hashing
- **ValidationIssue**: Rule validation errors and warnings
- **StateEntityTaxRuleResolved**: Denormalized view for fast tax lookups

## Database Schema
### Core Tables
- `user_sessions` - Upload sessions (session_id, user_id, status, progress, file info)
- `users` - User accounts (id, email, name, created_at)
- `investors` - Persistent investor entities (id, name, entity_type, tax_state)
- `distributions` - Distribution data with tax calculations (composite_tax_amount, withholding_tax_amount)
- `validation_errors` - Processing errors (id, session_id, row_number, severity, message)

### SALT Rule Tables
- `salt_rule_set` - Rule set versions with lifecycle management (draft/active/archived)
- `withholding_rule` - Withholding tax rules by state and entity type
- `composite_rule` - Composite tax rates and mandatory filing requirements
- `source_file` - Uploaded file metadata with SHA256 hashing for duplicates
- `validation_issue` - Rule validation errors and warnings
- `state_entity_tax_rule_resolved` - Denormalized tax rule lookup table

## Coding Standards & Conventions
### Python (Backend)
- **Style**: Black formatting, line length 88
- **Imports**: isort with profile black
- **Type Hints**: Required for all functions and classes
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Error Handling**: Custom exceptions in `app.core.exceptions`
- **Logging**: Use Python logging, structured JSON for production

### TypeScript (Frontend)
- **Style**: Prettier formatting, 2-space indentation
- **Naming**: camelCase for variables/functions, PascalCase for components
- **Components**: Functional components with hooks
- **State**: React hooks (useState, useEffect) for local state
- **API Calls**: Custom hooks for data fetching
- **Error Handling**: Error boundaries and toast notifications

### File Organization
- **Components**: One component per file, named exports
- **APIs**: Group by feature (uploads, calculations, results)
- **Types**: Shared types in `types/` directory
- **Utils**: Pure functions, well-tested utilities

## Development Workflow
### Commands (Make targets)
```bash
make dev          # Start Docker development environment
make test         # Run all tests (backend + frontend)
make lint         # Run all linters and formatters
make type-check   # TypeScript type checking
make build        # Build production bundle
make clean        # Clean Docker containers/images

# Individual services
make test-backend    # pytest only
make test-frontend   # Jest only
make lint-fix        # Auto-fix linting issues
```

### Testing Strategy
- **Backend**: pytest with >90% coverage, focus on services and API endpoints
- **Frontend**: Jest + RTL for components, integration tests for workflows
- **E2E**: Manual testing for upload-to-results workflow
- **Test Data**: Sample Excel files in `data/test_files/`

## Current Status & Progress
- ✅ Project structure setup
- ✅ Tech stack configuration (FastAPI + React)
- ✅ Docker development environment
- ✅ Basic API endpoints defined
- ✅ File upload infrastructure
- ✅ Updated TDD v1.2 with correct tech stack specifications
- ✅ Feature specification created for file upload and validation
- ✅ Implementation plan Phase 0 (Research) and Phase 1 (Design) completed
- ✅ API contracts defined (OpenAPI spec with upload, validation, progress endpoints)
- ✅ Data model designed (User, Session, Investor, Distribution, ValidationError entities)
- ✅ Epic 1 specification files created with comprehensive development workflow
- ✅ Architecture Decision Records established with ADR-0001 (monolithic approach)
- ✅ Updated data model for persistent investors and exemption fields support (v1.2 format)
- ✅ Enhanced specifications to support 9-column Excel format with CO/NM exemption tracking
- ✅ **COMPLETE MVP IMPLEMENTATION** - All Phase 3.1-3.7 tasks (T001-T040) implemented
- ✅ **Epic 2A COMPLETE: SALT Rule System** - Full tax rule management with 7 new models, 6 API endpoints, comprehensive validation
- ✅ **Epic 2B COMPLETE: Tax Calculation Engine** - Automated withholding and composite tax calculations with audit reporting
- ✅ Backend: 26 Python files with database models, services, and API endpoints (11 services, 11+ models)
- ✅ Frontend: 18+ React components with Shadcn UI, modal workflow, advanced data grids
- ✅ E2E testing: Playwright test suite covering complete upload and tax calculation workflow
- ✅ **Results Modal Workflow** - Streamlined user experience with modal-based results instead of separate pages
- ✅ **Audit Reporting** - CSV download functionality for detailed tax calculation compliance reports
- ✅ **Database Auto-Migration** - Automatic schema updates for tax calculation columns on legacy databases
- ✅ **v1.3 Format Support** - Dynamic Excel column detection supporting multiple state jurisdictions
- ✅ **Comprehensive Test Coverage** - 35+ test files covering contracts, integration, and unit testing
- 🎯 **Production Ready**: Advanced tax processing system ready for deployment and user testing

## Version 1.2.1 Scope & Capabilities
### Implemented Features
- Excel file upload (drag & drop) with comprehensive validation
- Complete SALT rule management system with lifecycle control
- Automated tax calculation engine (withholding + composite)
- Advanced results dashboard with modal workflow
- Excel export and audit report generation
- Template download functionality (v1.3 format)
- Support for ~10 portfolio companies, ~20 LPs
- File size limit: 10MB
- Comprehensive audit trail for compliance

### Out of Scope for v1.2 (Future v1.3+)
- API integrations (NetSuite, Salesforce)
- Real-time data synchronization
- Advanced dashboards and visualizations
- Large-scale data processing (50+ portfolios, 100+ LPs)
- SOC 2 security compliance
- Microservices architecture
- Advanced workflow automation

## Business Context
### Target Users
- **Primary**: Tax Directors like "Sarah Chen" who need intuitive, fast workflow
- **Secondary**: Fund administrators and back-office staff

### Success Metrics
- **Performance**: 30min upload-to-results completion time
- **Accuracy**: 95% Excel format recognition accuracy
- **Concurrency**: Support 3-5 concurrent users
- **Processing**: 30min processing for typical files (~10 portfolios, ~20 LPs)

### Critical Constraints
- **Processing**: Synchronous processing (no async/queuing for prototype)
- **Security**: Basic file validation, no sensitive data storage yet
- **Future Migration**: Code should be structured to facilitate v1.3 microservices transition

## Common Development Tasks
### Adding New API Endpoint
1. Create route in `backend/src/api/`
2. Add Pydantic models in `backend/src/models/`
3. Implement service logic in `backend/src/services/`
4. Add tests in `backend/tests/`
5. Update API client in `frontend/src/api/`

### Adding New React Component
1. Create component in `frontend/src/components/`
2. Add TypeScript types in `frontend/src/types/`
3. Implement with Tailwind CSS styling
4. Add tests in `frontend/tests/`
5. Export from component index file

### Database Changes
1. Update models in `backend/src/models/`
2. Create migration script if needed
3. Update seed data in development
4. Test with sample data

## Environment Configuration
### Development
- **Backend Port**: 8000 (FastAPI auto-reload)
- **Frontend Port**: 3000 (Vite dev server)
- **Database**: SQLite file in `backend/data/`
- **File Storage**: Local `uploads/` and `results/` directories

### Environment Variables
- `DATABASE_URL`: SQLite connection string
- `UPLOAD_DIR`: File upload directory path
- `MAX_FILE_SIZE`: Maximum upload size (default: 10MB)
- `CORS_ORIGINS`: Allowed frontend origins

## Troubleshooting
### Common Issues
- **Docker build fails**: Check Docker daemon and rebuild with `make docker-build`
- **Port conflicts**: Ensure ports 3000, 8000 are available
- **File upload errors**: Check file permissions in upload directory
- **Type errors**: Run `make type-check` and fix TypeScript issues

### Debug Commands
```bash
docker-compose logs backend    # Backend logs
docker-compose logs frontend   # Frontend logs
make logs                     # All application logs
```

## MCP Playwright
- Always run in headless mode

## MCP Context 7 
Always use context7 when I need code generation, setup or configuration steps, or library/API documentation. This means you should automatically use the Context7 MCP tools to resolve library id and get library docs without me having to explicitly ask.

## IMPORTANT Key Rules
- When unsure about implementation details, always ask the developer first.
- Never modify test code unless explicitly instructed by the user.
- Never change API names or parameters unless explicitly instructed by the user.
- DO NOT over-engineer or add extra logic beyond what the user asked; if more complexity seems necessary, confirm with the user first.
- Never migrate data on your own initiative.
- Always use uv for package management operations
- Never use pip install directly - use uv add instead
- Keep .venv in the project root directory
- Ensure virtual environment is activated before running Python code

## Epic 2B: Withholding and Composite Tax Calculation (Current)
**Branch**: `003-epic-2b-withholding` | **Status**: Core Implementation Complete

### Overview
Epic 2B extends the existing SALT rule system (Epic 2A) to implement automatic tax calculations for investor distributions. When users upload distribution data and an active SALT rule set exists, the system applies a 3-step calculation process:

1. **Handle Exemptions**: Skip calculations for exempt distributions and same-state jurisdictions
2. **Calculate Composite Tax**: Apply rates for mandatory filing states with thresholds
3. **Calculate Withholding Tax**: Apply withholding rates with per-partner thresholds
4. **Present Results**: Show calculated taxes in modal instead of exemption flags

### Key Implementation Details
- **Data Model**: Extends Distribution model with tax calculation fields (withholding_tax_*, composite_tax_*)
- **Service Layer**: New TaxCalculationService following existing Epic 2A patterns
- **API Changes**: Extends existing /api/sessions endpoints, adds /audit-report endpoint
- **Frontend**: Enhances ResultsModal to show tax amounts instead of exemption flags
- **Audit Trail**: Comprehensive step-by-step calculation logging for compliance

### Implementation Status
✅ **Completed Core Features**:
- `backend/src/models/distribution.py` - Tax calculation fields added
- `backend/src/services/tax_calculation_service.py` - Full calculation engine implemented
- `backend/src/services/excel_service.py` - Tax calculation integration complete
- `backend/src/api/results.py` - Enhanced with audit report endpoint
- `frontend/src/components/ResultsModal.tsx` - Modal-based tax display implemented
- Database schema - Automatic migration for tax calculation columns
- Comprehensive unit tests for all tax calculation logic

### Integration Strategy
Epic 2B leverages existing Epic 2A infrastructure:
- Uses existing SALT rule tables (salt_rule_set, withholding_rule, composite_rule)
- Integrates with current Excel upload pipeline
- Maintains backward compatibility for sessions without SALT rules
- Follows established service patterns and error handling

## Test-First (Non-Negotiable)
- **Order:** Unit → Contract → Integration → E2E → Implementation.
- Write tests first (Red-Green-Refactor).
- All merges require passing tests and proof of the TDD cycle.  