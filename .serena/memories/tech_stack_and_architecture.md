# FundFlow Tech Stack and Architecture

## Architecture Overview
**Simplified 3-Tier Web Application (Monolithic)**
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS (Single Page Application)
- **Backend**: Python 3.11 + FastAPI + SQLite (synchronous processing)
- **File Processing**: pandas + openpyxl for Excel handling
- **Storage**: Local file system with SQLite database
- **Deployment**: Docker + Docker Compose for development

## Backend Tech Stack
- **Framework**: FastAPI 0.104+ (async/await support)
- **Database**: SQLite with SQLAlchemy ORM
- **File Processing**: pandas 2.1+, openpyxl 3.1+ (Excel parsing and validation)
- **Validation**: Pydantic v2, structured error collection
- **Testing**: pytest, pytest-asyncio, real dependencies (SQLite, filesystem)
- **Code Quality**: black, isort, flake8, mypy, ruff, pre-commit hooks

### Key Backend Dependencies
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
pandas==2.1.3
openpyxl==3.1.2
python-multipart==0.0.6
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
```

## Frontend Tech Stack
- **Framework**: React 18 + TypeScript 5.0+
- **Build Tool**: Vite 4.0+
- **Styling**: Tailwind CSS 3.3+ with Shadcn UI components
- **HTTP Client**: axios
- **UI Components**: @radix-ui components, @headlessui/react, @heroicons/react
- **File Upload**: react-dropzone
- **Notifications**: react-hot-toast
- **Routing**: react-router-dom
- **Testing**: Jest, React Testing Library, Playwright (E2E)
- **Code Quality**: ESLint, Prettier with Tailwind plugin

### Key Frontend Dependencies
```
react: ^18.2.0
react-dom: ^18.2.0
react-router-dom: ^6.18.0
axios: ^1.6.2
react-dropzone: ^14.2.3
tailwindcss: ^3.3.5
typescript: ^5.2.2
vite: ^4.5.0
```

## Database Schema
### Key Tables
- `users` - User accounts and profiles
- `user_sessions` - User sessions and file uploads
- `investors` - LP investor information
- `distributions` - Distribution data from portfolio companies
- `validation_errors` - File validation errors and warnings

## API Architecture
### Core Endpoints
- `POST /api/upload` - Upload Excel file for processing
- `GET /api/sessions/{session_id}` - Get session status and data
- `GET /api/sessions/{session_id}/download` - Download results as Excel
- `GET /api/template` - Download Excel template
- `GET /api/sessions` - List all user sessions
- `GET /health` - Health check

## Development Environment
- **Backend Port**: 8000 (FastAPI auto-reload)
- **Frontend Port**: 3000 (Vite dev server)
- **Database**: SQLite file in `backend/data/`
- **File Storage**: Local `data/uploads/` and `data/results/` directories
- **Docker**: Full containerized development environment

## Design Principles
1. **Simplicity over complexity** - Monolithic architecture for rapid prototyping
2. **User experience validation focus** - Clean, intuitive UI/UX
3. **Future scalability considerations** - Clean service boundaries for v1.3 microservices
4. **Robust error handling** - Comprehensive validation and user feedback