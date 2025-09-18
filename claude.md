# FundFlow - AI-Powered PE Back-Office Automation Platform (Prototype v1.2)

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
### Core Endpoints
- `POST /api/upload` - Upload Excel file for processing
- `GET /api/results/{session_id}` - Get processing results and status
- `GET /api/results/{session_id}/preview` - Preview processing results
- `GET /api/results/{session_id}/download` - Download results as Excel
- `GET /api/results/{session_id}/download-errors` - Download validation errors
- `GET /api/template` - Download Excel template
- `GET /api/health` - Health check
- `GET /api/health/simple` - Simple health check

### Data Models
- **UserSession**: Upload session tracking with status and progress
- **Investor**: Persistent investor entities with name, entity type, and tax state
- **Distribution**: Quarterly distribution amounts by jurisdiction
- **ValidationError**: File validation errors with severity levels
- **UploadStatus**: Enum for tracking upload/processing stages

## Database Schema
### Key Tables
- `user_sessions` - Upload sessions (session_id, user_id, status, progress, file info)
- `users` - User accounts (id, email, name, created_at)
- `investors` - Persistent investor entities (id, name, entity_type, tax_state)
- `distributions` - Distribution data (id, investor_id, session_id, jurisdiction, amount, exemptions)
- `validation_errors` - Processing errors (id, session_id, row_number, severity, message)

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
- ✅ Backend: 21 Python files with database models, services, and API endpoints
- ✅ Frontend: 15+ React components with Shadcn UI, drag-drop upload, data grids
- ✅ E2E testing: Playwright test suite covering complete upload workflow
- ✅ **Docker Configuration Fixed** - Resolved pydantic-settings parsing errors, dependency conflicts, and health checks
- ✅ **v1.3 Format Support** - Updated ExcelService with flexible column detection for dynamic state-based parsing
- ✅ **Project Onboarding Complete** - Comprehensive memory files created with project overview, tech stack, conventions, and development workflows
- ✅ **Sessions API Endpoint** - Added GET /sessions endpoint to fix Dashboard 404 error when loading user sessions
- ✅ **Dynamic Column Preview** - Enhanced file preview modal to dynamically display columns based on uploaded file content instead of hardcoded TX/NM/CO
- 🎯 **Ready for user validation**: Working end-to-end prototype with all containers healthy

## Prototype Scope & Limitations
### In Scope for v1.2
- Excel file upload (drag & drop)
- SALT calculation with pre-stored EY data
- Basic results dashboard
- Excel export of calculation results
- Template download functionality
- Support for ~10 portfolio companies, ~20 LPs
- File size limit: 10MB

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
- Never migrate data on your own initiative.
- Always use uv for package management operations
- Never use pip install directly - use uv add instead
- Keep .venv in the project root directory
- Ensure virtual environment is activated before running Python code

## Test-First (Non-Negotiable)
- **Order:** Unit → Contract → Integration → E2E → Implementation.  
- Write tests first (Red-Green-Refactor).  
- All merges require passing tests and proof of the TDD cycle.  