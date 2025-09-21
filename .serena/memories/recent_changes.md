# Recent Project Changes

## Bug Fixes

### SaltSetDetails Component Data Transformation Fix
- **File**: `frontend/src/pages/SaltSetDetails.tsx`
- **Issue**: Incorrect property used for state grouping in data transformation functions
- **Fix**: Changed `rule.stateCode` to `rule.state` as grouping key in `transformWithholdingRules` and `transformCompositeRules`
- **Impact**: Ensures consistent data aggregation for SALT rule details display
- **Date**: 2025-09-21