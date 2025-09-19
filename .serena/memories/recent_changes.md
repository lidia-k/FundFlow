# Recent Changes

## SALT Rule Upload Improvements (Latest)
- Fixed validation flow by removing DB dependency before file validation
- Added draft rule set override for same year/quarter combinations
- Fixed UniqueConstraint column references in models (state_code -> state)
- Improved file storage path generation and quarter value handling
- Cleaned up test upload files from repository
- Streamlined error handling in upload workflow