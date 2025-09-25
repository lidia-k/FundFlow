# Recent Changes

## Refactoring: Factory Pattern to FastAPI Dependency Injection
- **Date**: 2025-09-26
- **Branch**: feat/issue-6
- **Type**: Backend refactoring

### Changes Made
- Removed `upload_service_factory.py` factory pattern implementation
- Moved `UploadServiceDependencies` dataclass to `upload_dependencies.py`
- Updated all pipeline steps and orchestrator imports to use new dependency location
- Maintained clean service boundaries while leveraging FastAPI's built-in DI system

### Files Modified
- `backend/src/api/upload.py` - Updated import paths
- `backend/src/services/file_upload_orchestrator.py` - Updated imports
- `backend/src/services/upload_dependencies.py` - Added UploadServiceDependencies dataclass
- All pipeline steps - Updated import paths
- Deleted `backend/src/services/upload_service_factory.py`

### Architecture Impact
- Eliminates factory anti-pattern in favor of FastAPI dependency injection
- Follows SOLID principles more closely
- Maintains existing functionality while improving code organization