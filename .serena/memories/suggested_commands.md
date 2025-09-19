# FundFlow Development Commands

## Primary Development Commands

### Quick Start
```bash
make dev              # Start full development environment with Docker
make setup            # Initial project setup (install dependencies)
```

### Development Environment
```bash
make dev              # Start with Docker (recommended)
make dev-local        # Start locally (requires setup)
docker-compose up --build  # Alternative Docker start

# Access points:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/api/docs
```

## Testing Commands
```bash
make test             # Run all tests (backend + frontend)
make test-backend     # Run backend tests only (pytest)
make test-frontend    # Run frontend tests only (Jest)

# Direct commands:
npm run test                    # All tests
cd backend && python -m pytest # Backend tests
cd frontend && npm run test     # Frontend tests
```

## Code Quality Commands
```bash
make lint             # Run all linters (backend + frontend)
make lint-fix         # Auto-fix linting issues
make type-check       # TypeScript type checking

# Individual linting:
npm run lint:backend   # black --check, isort --check, flake8
npm run lint:frontend  # ESLint for TypeScript/React
npm run lint:fix       # Auto-fix all linting issues
```

## Build and Production
```bash
make build            # Build application for production
npm run build         # Same as above
npm run build:frontend # Build frontend only

make docker-build     # Build Docker images
make docker-up        # Start Docker containers in background
make docker-down      # Stop Docker containers
```

## Database Operations
```bash
make db-migrate       # Run database migrations
make db-seed          # Seed database with sample data

# Direct commands:
cd backend && alembic upgrade head  # Run migrations
cd backend && python scripts/seed_db.py  # Seed data
```

## Development Utilities
```bash
make logs             # View application logs
make docker-logs      # View Docker logs
make clean            # Clean Docker containers and images

# Individual service logs:
docker-compose logs backend   # Backend logs
docker-compose logs frontend  # Frontend logs
```

## Pre-commit Hooks
```bash
make setup-hooks      # Install pre-commit hooks
pre-commit run --all-files  # Run hooks manually
```

## Essential Development Workflow
```bash
# 1. Initial setup (first time only)
make setup
make setup-hooks

# 2. Start development
make dev

# 3. Before committing changes
make lint             # Check code style
make type-check       # Check TypeScript types
make test             # Run all tests

# 4. Build and verify
make build            # Test production build
```

## Package Management
**Backend**: Use standard pip with requirements.txt
```bash
cd backend
pip install -r requirements.txt  # Install dependencies
pip freeze > requirements.txt    # Update dependencies
```

**Frontend**: Use npm
```bash
cd frontend
npm install           # Install dependencies
npm install <package> # Add new dependency
```

## Common macOS/Darwin Commands
```bash
# System utilities (Darwin-specific)
find . -name "*.py" -type f        # Find Python files
grep -r "search_term" backend/     # Search in backend
ls -la                            # List files with details
tail -f logs/app.log              # Follow log files

# Port management (if needed)
lsof -i :3000                     # Check what's using port 3000
lsof -i :8000                     # Check what's using port 8000
```

## Task Completion Checklist
When completing any task, always run:
```bash
make lint             # Check and fix code style
make type-check       # Verify TypeScript types (if frontend changes)
make test             # Ensure all tests pass
```

## Troubleshooting
```bash
# Docker issues
docker-compose down && docker-compose up --build  # Rebuild containers
make clean && make dev                            # Clean and restart

# Port conflicts
make docker-down      # Stop containers
pkill -f "node"       # Kill Node processes (if needed)

# Database issues
rm backend/data/fundflow.db  # Reset SQLite database
make db-migrate              # Recreate database
make db-seed                 # Add sample data
```