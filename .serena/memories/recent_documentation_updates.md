# Recent Documentation Updates

## API Documentation Corrections (Epic 2A)
- Updated CLAUDE.md API reference section to match actual implementation
- Corrected endpoint paths from `/api/calculations/` to `/api/results/` 
- Updated data models to reflect current implementation (UserSession, Investor, Distribution, ValidationError)
- Updated database schema documentation with correct table names and structure
- Fixed file paths to match backend/src/ directory structure

## Task File Reorganization
- Removed old `prompts/development/tasks.md` 
- Added Epic 2A SALT task specifications in `specs/002-epic-2a-salt/tasks.md`
- Added new `prompts/development/implement_tasks.md` for development workflow

## Key Changes Made
- API endpoints now correctly documented as implemented
- Data models match actual Pydantic models in codebase
- Database schema reflects current SQLAlchemy models
- Development workflow paths updated to match project structure