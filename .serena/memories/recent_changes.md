# Recent Changes to FundFlow

## SHA256 Hashing and Duplicate Detection Removal (Latest)

**Date**: 2025-09-19
**Files Modified**: 
- `backend/src/services/file_service.py`
- `backend/src/models/source_file.py` 
- `backend/src/api/salt_rules.py`

**Changes**:
- Removed SHA256 hashing and duplicate detection functionality for prototype simplification
- File uploads now override existing files with same name instead of detecting duplicates
- Updated file size limit from 20MB to 10MB for prototype
- Simplified file storage path structure from hash-based to filename-based
- Removed ConflictResponse model and related API logic
- Updated SourceFile model to remove sha256_hash field and related constraints

**Impact**: Significantly simplified file upload workflow, making it more user-friendly for prototype validation.