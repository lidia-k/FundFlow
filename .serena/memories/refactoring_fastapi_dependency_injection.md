# FastAPI Dependency Injection Refactoring

## Summary
Replaced factory pattern with FastAPI's native dependency injection system in upload endpoint.

## Key Changes
- **New file**: `backend/src/services/upload_dependencies.py` - Service dependency functions with @lru_cache and Depends()
- **Modified**: `backend/src/api/upload.py` - Uses FastAPI Depends() instead of UploadServiceFactory
- **Updated**: Documentation patterns to reflect FastAPI DI approach

## Benefits
- More idiomatic FastAPI code
- Better performance with cached singleton services  
- Easier testing with dependency overrides
- Cleaner separation of concerns

## Pattern Used
```python
@lru_cache()
def get_service() -> Service:
    return Service()

def get_services(
    service: Service = Depends(get_service),
    db: Session = Depends(get_db)
) -> ServiceDependencies:
    return ServiceDependencies(service=service, db=db)
```