
  With GitHub issue #{ISSUE_NUMBER}, please:

  1. **Set up branch**: Create a new branch `issue-{ISSUE_NUMBER}` from the main branch

  2. **Fetch and analyze the issue**: Use `gh issue view {ISSUE_NUMBER}` to get
  the full issue details including title, description, labels, and any comments.

  3. **Create an implementation plan** that:
     - Follows YAGNI principles (build only what's needed for the prototype)
     - Considers the current FundFlow v1.2.1 architecture and capabilities
     - Breaks down the work into specific, testable tasks
     - Identifies any potential risks or dependencies
     - Estimates complexity (Simple/Medium/Complex)
     - Use scratchpad to show the chain of thoughts during planning

  4. **Present the plan** including:
     - Issue summary and key requirements
     - Proposed solution approach
     - List of files that need to be modified/created
     - Any assumptions or clarifications needed
     - Timeline estimate

  5. **Ask for approval** before implementing anything

  6. **After user approval**:
     - Create a sub-agent to implement the solution as per the approved plan
     - Create a sub-agent to write unit tests to test the completed task
     - Use sub-agents for test, lint and build respectively to ensure quality and resolve any issue
     - Create a new Pull Request

  Remember: This is for the FundFlow prototype focused on validating user
  experience with 2-3 test partner clients. Keep solutions simple and avoid
  over-engineering.

