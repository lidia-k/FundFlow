# FundFlow - AI-Powered PE Back-Office Automation Platform (Prototype v1.2)

## Project Overview
FundFlow is an AI-powered automation platform designed to solve manual SALT (State and Local Tax) calculation challenges for Private Equity fund back-office operations. This prototype version (v1.2) focuses on validating the core workflow of Excel file upload, SALT calculation, and results generation without complex API integrations.

**Key Goal**: Validate user experience and data processing workflow with 2-3 test partner clients by Q1 2026.

## Key Documents
- PRD: `prototype/v1.2/FundFlow PRD v1.2.md` - Product requirements focused on simplified Excel upload workflow with pre-stored EY SALT data
- TDD: `prototype/v1.2/FundFlow TDD v1.2.md` - Technical design using traditional 3-tier web architecture with Python Flask + React

## Project Structure
```
FundFlow/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   ├── core/           # Core configuration and utilities
│   │   ├── models/         # Pydantic models and database schemas
│   │   ├── services/       # Business logic and SALT calculations
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests (pytest)
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # Reusable React components
│   │   ├── pages/          # Page components (Upload, Dashboard, Results)
│   │   ├── api/            # API client utilities
│   │   └── types/          # TypeScript type definitions
│   ├── tests/              # Frontend tests (Jest)
│   └── package.json        # Node.js dependencies
├── data/                   # Sample data and templates
├── docker-compose.yml      # Development environment
└── Makefile               # Development commands
```

## Architecture Overview
**Simplified 3-Tier Web Application (Monolithic)**
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS (Single Page Application)
- **Backend**: Python 3.11 + FastAPI + SQLite (synchronous processing)
- **File Processing**: pandas + openpyxl for Excel handling
- **Storage**: Local file system with SQLite database
- **Deployment**: Docker + Docker Compose for development

**Key Design Principles**:
1. Simplicity over complexity
2. Rapid prototyping for user feedback
3. User experience validation focus
4. Future scalability considerations

## Tech Stack & Dependencies
### Backend
- **Framework**: FastAPI 0.104+ (async/await support)
- **Database**: SQLite with SQLAlchemy ORM
- **File Processing**: pandas 2.0+, openpyxl 3.1+
- **Validation**: Pydantic v2
- **Testing**: pytest, pytest-asyncio
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
- `GET /api/calculations/{id}` - Get calculation status and results
- `GET /api/calculations/{id}/download` - Download results as Excel
- `GET /api/template` - Download Excel template
- `GET /api/health` - Health check

### Data Models
- **UploadFile**: Excel file metadata and validation
- **Calculation**: SALT calculation job with status tracking
- **Portfolio**: Portfolio company data structure
- **SALTResult**: Calculated tax allocations and results

## Database Schema
### Key Tables
- `calculations` - Calculation jobs (id, status, created_at, file_path, results_path)
- `portfolios` - Portfolio company data (id, name, state, calculation_id)
- `salt_rules` - Pre-stored EY SALT calculation rules (state, rule_type, rate)
- `results` - Calculated results (id, portfolio_id, state, allocation, tax_amount)

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
- 🔄 Currently working on: Core SALT calculation engine implementation
- ⏳ Next: Frontend integration with backend APIs
- ⏳ Pending: Excel validation and error handling

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
- **EY Data**: SALT rules are pre-stored in the system - users only upload portfolio data
- **Processing**: Synchronous processing (no async/queuing for prototype)
- **Security**: Basic file validation, no sensitive data storage yet
- **Future Migration**: Code should be structured to facilitate v1.3 microservices transition

## Common Development Tasks
### Adding New API Endpoint
1. Create route in `backend/app/api/`
2. Add Pydantic models in `backend/app/models/`
3. Implement service logic in `backend/app/services/`
4. Add tests in `backend/tests/`
5. Update API client in `frontend/src/api/`

### Adding New React Component
1. Create component in `frontend/src/components/`
2. Add TypeScript types in `frontend/src/types/`
3. Implement with Tailwind CSS styling
4. Add tests in `frontend/tests/`
5. Export from component index file

### Database Changes
1. Update models in `backend/app/models/`
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