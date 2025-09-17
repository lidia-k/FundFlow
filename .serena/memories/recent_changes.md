# Recent Changes

## Enhanced InvestorEntityType Enum with SALT Coding Support
- Added SALT coding attributes to InvestorEntityType enum values for tax calculation requirements
- Implemented helper methods: get_by_coding(), get_all_codings(), get_unique_codings() 
- Centralized enum imports in models module
- Updated Epic 1 plan status showing phases 3-4 completed
- Added backend/tests/ directory structure
- Cleaned up project by removing obsolete todo.md file

This enhancement supports the core SALT calculation business logic by providing proper entity type coding for tax processing.