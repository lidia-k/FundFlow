# FastAPI Dependency Injection Import Fix

## Summary
Fixed ModuleNotFoundError in upload_dependencies.py that was preventing backend container from starting.

## Issue
- Backend container failing with `ModuleNotFoundError: No module named 'src.services.file_handling_service'`
- upload_dependencies.py was importing non-existent services

## Solution
- Corrected imports to match actual service structure from upload_service_factory.py
- Added all required services: user, investor, fund, distribution, tax_calculation, validators
- Maintained proper FastAPI dependency injection pattern with @lru_cache for singletons
- Ensured UploadServiceDependencies container gets all required services

## Result
- Backend container now runs healthy
- FastAPI dependency injection refactoring complete and working
- No more import errors during container startup