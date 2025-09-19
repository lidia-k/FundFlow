# SALT Rules DRAFT Status Removal

## Changes Made
- Removed RuleSetStatus.DRAFT enum value, simplified to only ACTIVE and ARCHIVED states
- Updated upload endpoint to create rule sets as ACTIVE immediately upon successful validation
- Modified system to archive existing ACTIVE rule sets when new ones are uploaded
- Simplified validation service by removing unused complex validation pipeline functions
- Adjusted tax rate constraints to allow rates up to 10.0000 (1000%) for both withholding and composite rules
- Streamlined Excel processing by removing redundant validation layers

## Technical Impact
- Simplified rule set lifecycle from 3-state (DRAFT/ACTIVE/ARCHIVED) to 2-state (ACTIVE/ARCHIVED)
- Immediate activation of uploaded rule sets removes intermediate draft approval step
- Previous ACTIVE rule sets are automatically archived when new ones are uploaded
- Cleaner validation service with only actively used methods

## Files Modified
- backend/src/models/enums.py - Removed DRAFT status
- backend/src/api/salt_rules.py - Updated upload/publish/delete logic
- backend/src/models/salt_rule_set.py - Changed default status to ACTIVE
- backend/src/services/rule_set_service.py - Updated service methods
- backend/src/services/validation_service.py - Simplified to only used methods
- backend/src/services/excel_processor.py - Streamlined processing
- backend/src/models/withholding_rule.py - Increased tax rate limit
- backend/src/models/composite_rule.py - Increased tax rate limit