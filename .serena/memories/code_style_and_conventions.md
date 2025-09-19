# FundFlow Code Style and Conventions

## Python (Backend) Style Guidelines

### Formatting and Linting
- **Black**: Line length 88, Python 3.11 target
- **isort**: Profile "black", multi-line output mode 3
- **flake8**: Max line length 88, ignore E203 and W503
- **mypy**: Strict typing, disallow untyped definitions
- **ruff**: Modern linting with E, W, F, I, N, B, UP rules

### Code Style
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Type Hints**: Required for all functions and classes
- **Imports**: Grouped by isort (stdlib, third-party, local)
- **Line Length**: 88 characters maximum
- **String Quotes**: Prefer double quotes for consistency

### Error Handling
- Custom exceptions in `app.core.exceptions`
- Structured error responses with Pydantic models
- Comprehensive validation with clear error messages
- Logging with Python logging, structured format

### Testing
- **pytest**: >90% coverage requirement
- **pytest-asyncio**: For async test functions
- Focus on services and API endpoints
- Real dependencies (SQLite, filesystem) in tests
- Test data in `data/test_files/`

## TypeScript (Frontend) Style Guidelines

### Formatting
- **Prettier**: 2-space indentation, single quotes, trailing commas
- **ESLint**: TypeScript recommended rules + React hooks
- **Line Length**: 80 characters (Prettier default)
- **Semicolons**: Required (`;`)

### Code Style
- **Naming**: camelCase for variables/functions, PascalCase for components
- **Components**: Functional components with hooks only
- **State Management**: React hooks (useState, useEffect) for local state
- **File Organization**: One component per file, named exports
- **Type Safety**: Strict TypeScript mode, no any types

### Component Structure
```typescript
interface ComponentProps {
  // Props definition
}

export const ComponentName = ({ prop1, prop2 }: ComponentProps) => {
  // Component implementation
};
```

### API Calls
- Custom hooks for data fetching
- axios for HTTP client
- Proper error handling with toast notifications
- Type-safe API responses

## File Organization

### Backend Structure
```
backend/app/
├── api/         # API route handlers
├── core/        # Configuration and utilities
├── models/      # Pydantic models and database schemas
├── services/    # Business logic and SALT calculations
└── utils/       # Utility functions
```

### Frontend Structure
```
frontend/src/
├── components/  # Reusable React components
├── pages/       # Page components (Upload, Dashboard, Results)
├── api/         # API client utilities
├── types/       # TypeScript type definitions
└── utils/       # Pure functions, well-tested utilities
```

## Git and Pre-commit Hooks

### Pre-commit Configuration
- **Python**: black, isort, flake8 (backend files only)
- **JavaScript/TypeScript**: prettier (frontend files only)
- **General**: trailing whitespace, end-of-file-fixer, yaml validation
- **File Size**: Max 10MB file limit

### Commit Standards
- Conventional commit format recommended
- Clear, descriptive commit messages
- Atomic commits (one logical change per commit)

## Import Standards

### Python Imports (isort profile: black)
```python
# Standard library
import os
from typing import List, Dict

# Third-party
from fastapi import FastAPI
from sqlalchemy import Column

# Local imports
from app.core.config import settings
from app.models import User
```

### TypeScript Imports
```typescript
// React and third-party
import React from 'react';
import axios from 'axios';

// Local components and types
import { Button } from '@/components/ui/button';
import type { ApiResponse } from '@/types/api';
```

## Database Conventions
- **Models**: SQLAlchemy ORM with Pydantic schemas
- **Naming**: snake_case table and column names
- **Migrations**: Alembic for schema changes
- **Relationships**: Explicit foreign keys and relationships