# FundFlow Task Completion Guidelines

## Essential Commands After Any Code Changes

### 1. Code Quality Checks (ALWAYS RUN)
```bash
make lint             # Run all linters (backend + frontend)
make lint-fix         # Auto-fix any linting issues
```

### 2. Type Checking (for TypeScript changes)
```bash
make type-check       # Check TypeScript types in frontend
```

### 3. Test Execution (CRITICAL)
```bash
make test             # Run all tests (backend + frontend)
# OR individually:
make test-backend     # Backend tests only (pytest)
make test-frontend    # Frontend tests only (Jest)
```

### 4. Build Verification (for significant changes)
```bash
make build            # Verify production build works
```

## Task Completion Workflow

### Standard Task Completion Checklist
1. **Complete the implementation**
2. **Run linting**: `make lint` or `make lint-fix`
3. **Check types** (if frontend changes): `make type-check`
4. **Run tests**: `make test` 
5. **Verify build** (if significant): `make build`
6. **Commit changes** (if requested by user)

### For Backend Changes
```bash
cd backend
black .                    # Format code
isort .                    # Sort imports
python -m pytest          # Run tests
```

### For Frontend Changes
```bash
cd frontend
npm run lint:fix           # Fix linting and formatting
npm run type-check         # TypeScript type checking
npm run test               # Run tests
```

### For Database Changes
```bash
make db-migrate            # Apply migrations
make db-seed               # Seed with test data (if needed)
make test                  # Ensure tests still pass
```

## Pre-commit Hook Integration
- Pre-commit hooks are configured to automatically run:
  - **black** and **isort** for Python files
  - **prettier** for TypeScript/JavaScript files
  - **flake8** for Python linting
  - General file checks (trailing whitespace, large files)

## Quality Standards

### Code Coverage
- **Backend**: Target >90% test coverage
- **Frontend**: Focus on critical user flows
- Use `pytest --cov` for backend coverage reports

### Performance Checks
- Monitor Excel processing time (<30min for typical files)
- Check memory usage for large file uploads
- Verify API response times remain reasonable

### Error Handling
- All API endpoints must have proper error responses
- Frontend must handle API errors gracefully
- Database operations must be wrapped in try/catch

## Development Best Practices

### When Adding New Features
1. **Design API contracts first** (OpenAPI/Swagger)
2. **Write tests before implementation** (TDD approach)
3. **Implement backend services** with proper error handling
4. **Create frontend components** with TypeScript types
5. **Test end-to-end workflow** manually
6. **Run full test suite** before completion

### When Fixing Bugs
1. **Reproduce the bug** with a test case
2. **Fix the implementation**
3. **Verify the test passes**
4. **Run regression tests** to ensure no side effects
5. **Update documentation** if behavior changed

### When Refactoring
1. **Ensure all tests pass** before starting
2. **Make small, incremental changes**
3. **Run tests after each change**
4. **Update type definitions** if interfaces change
5. **Verify frontend still compiles and works**

## Documentation Updates
When completing tasks that affect:
- **API changes**: Update OpenAPI docs at `/api/docs`
- **Database schema**: Update model documentation
- **UI changes**: Update component documentation if significant
- **Configuration**: Update `.env.example` and README

## Deployment Readiness
Before marking any task as "deployment ready":
1. **All tests pass**: `make test` succeeds
2. **Production build works**: `make build` succeeds  
3. **Docker containers healthy**: `make dev` shows all services up
4. **No linting errors**: `make lint` passes clean
5. **TypeScript compiles**: `make type-check` passes
6. **Manual testing complete**: Core user workflows verified

## Monitoring and Logging
- Check application logs during testing: `make logs`
- Monitor Docker container health: `docker-compose ps`
- Verify database operations: Check SQLite file for expected data
- Test error scenarios: Ensure proper error messages shown to users

## Version Control Best Practices
- **Atomic commits**: One logical change per commit
- **Clear commit messages**: Describe what and why
- **Branch naming**: Use descriptive names (feature/bug/refactor)
- **Pre-commit hooks**: Let them catch issues before committing