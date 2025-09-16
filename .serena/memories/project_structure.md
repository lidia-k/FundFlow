# FundFlow Project Structure

## Root Directory Overview
```
FundFlow/
├── README.md                    # Project overview and quick start
├── CLAUDE.md                    # Project instructions and conventions
├── Makefile                     # Development commands
├── package.json                 # Root package.json for scripts
├── docker-compose.yml           # Docker development environment
├── docker-compose.override.yml  # Docker overrides
├── .pre-commit-config.yaml     # Pre-commit hook configuration
├── .gitignore                  # Git ignore patterns
├── todo.md                     # Development todo list
│
├── backend/                    # Python FastAPI backend
├── frontend/                   # React TypeScript frontend
├── data/                       # Data storage and templates
├── docs/                       # Project documentation
├── specs/                      # Specifications and requirements
├── scripts/                    # Setup and utility scripts
├── docker/                     # Docker configurations
├── shared/                     # Shared utilities and types
├── archive/                    # Archived files
├── prototype/                  # Prototype documentation
└── prompts/                    # Development prompts and guides
```

## Backend Structure (`backend/`)
```
backend/
├── app/                        # FastAPI application
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   └── core/                   # Core configuration
│       ├── __init__.py
│       └── config.py           # Settings and configuration
│
├── src/                        # Source code (main implementation)
│   ├── api/                    # API routes and endpoints
│   ├── models/                 # Database models (SQLAlchemy)
│   ├── services/               # Business logic layer
│   ├── database/               # Database connection and setup
│   └── utils/                  # Utility functions
│
├── tests/                      # Backend tests (pytest)
├── alembic/                    # Database migration files
├── data/                       # SQLite database and uploads
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Python project configuration
└── .env.example               # Environment variables example
```

## Frontend Structure (`frontend/`)
```
frontend/
├── src/                        # React application source
│   ├── components/             # Reusable UI components
│   │   ├── ui/                 # Shadcn UI components
│   │   ├── forms/              # Form components
│   │   └── layout/             # Layout components
│   ├── pages/                  # Page components
│   │   ├── Dashboard.tsx       # Main dashboard
│   │   ├── Upload.tsx          # File upload page
│   │   └── Results.tsx         # Results viewing page
│   ├── api/                    # API client utilities
│   ├── types/                  # TypeScript type definitions
│   ├── utils/                  # Utility functions
│   ├── hooks/                  # Custom React hooks
│   └── styles/                 # Global styles
│
├── public/                     # Static assets
├── tests/                      # Frontend tests (Jest)
├── package.json               # Node.js dependencies
├── tsconfig.json              # TypeScript configuration
├── vite.config.ts             # Vite build configuration
├── tailwind.config.js         # Tailwind CSS configuration
├── .eslintrc.cjs             # ESLint configuration
├── .prettierrc               # Prettier configuration
├── playwright.config.ts       # E2E testing configuration
└── SHADCN_USAGE.md           # Shadcn UI usage guide
```

## Data Structure (`data/`)
```
data/
├── uploads/                    # User uploaded Excel files
├── results/                    # Generated calculation results
├── templates/                  # Excel template files
└── test_files/                 # Sample files for testing
```

## Key Configuration Files

### Root Configuration
- **Makefile**: Development commands and shortcuts
- **docker-compose.yml**: Docker development environment setup
- **.pre-commit-config.yaml**: Code quality pre-commit hooks
- **package.json**: Root-level npm scripts orchestrating backend/frontend

### Backend Configuration
- **requirements.txt**: Python dependencies (pip-based)
- **pyproject.toml**: Python project settings, tool configurations (black, isort, pytest)
- **alembic.ini**: Database migration configuration
- **.env.example**: Environment variable template

### Frontend Configuration
- **package.json**: Node.js dependencies and scripts
- **tsconfig.json**: TypeScript compiler settings (strict mode)
- **vite.config.ts**: Build tool configuration with proxy setup
- **tailwind.config.js**: Tailwind CSS configuration
- **.eslintrc.cjs**: ESLint rules for TypeScript/React
- **.prettierrc**: Code formatting rules

## Important Entry Points

### Application Entry Points
- **Backend**: `backend/app/main.py` - FastAPI application
- **Frontend**: `frontend/src/main.tsx` - React application root

### Database
- **Models**: `backend/src/models/` - SQLAlchemy models
- **Migrations**: `backend/alembic/` - Database schema changes
- **Connection**: `backend/src/database/connection.py`

### API Layer
- **Routes**: `backend/src/api/` - API endpoint definitions
- **Services**: `backend/src/services/` - Business logic implementation

### UI Components
- **Shadcn UI**: `frontend/src/components/ui/` - Base UI components
- **Pages**: `frontend/src/pages/` - Route-level components
- **API Client**: `frontend/src/api/` - Backend communication

## Development Files
- **Scripts**: `scripts/` - Setup and utility scripts
- **Documentation**: `docs/` - Architecture decisions, specifications
- **Specifications**: `specs/` - Detailed feature specifications
- **Testing**: `frontend/tests/`, `backend/tests/` - Test suites

## Docker Structure
- **docker-compose.yml**: Main container orchestration
- **docker-compose.override.yml**: Local development overrides
- **docker/**: Additional Docker configuration files