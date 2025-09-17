# Recent Changes

## Distribution Service Refactor (Latest)
- Refactored distribution_service.py to support dynamic state-based processing
- Replaced hardcoded TX_NM/CO jurisdiction handling with flexible approach
- Added support for variable number of states from parsed Excel data
- Uses USJurisdiction enum for proper state validation
- Dynamically builds totals and exemption summaries for any supported states
- Improves data structure handling for distributions, exemptions, and composites
- Enables system to handle Excel files with different state configurations

## Claude Settings Update
- Added additional MCP Serena tool permissions for better code analysis capabilities