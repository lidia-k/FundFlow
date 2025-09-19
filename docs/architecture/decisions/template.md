# ADR-XXXX: [Short noun phrase describing the decision]

## Status
[Proposed | Accepted | Rejected | Superseded by ADR-YYYY]

## Date
[YYYY-MM-DD when the decision was made]

## Context

[Describe the architectural, business, or technical forces at play. What problem are we trying to solve? What constraints exist? Include enough context so that future team members can understand the situation.]

[Examples of good context:
- Performance requirements that drove technology choice
- Team expertise limitations
- Budget/timeline constraints
- Integration requirements with existing systems
- Compliance or security requirements
- Scale requirements]

## Decision

[State the architecture decision and provide a brief justification.]

[Example: "We will use FastAPI instead of Flask for the backend REST API framework."]

## Rationale

[Explain why this decision makes sense. Include the main factors that influenced the choice.]

### [Factor 1: e.g., Performance]
[Detailed reasoning about this factor]

### [Factor 2: e.g., Developer Experience]
[Detailed reasoning about this factor]

### [Factor 3: e.g., Ecosystem Support]
[Detailed reasoning about this factor]

## Consequences

### Positive
- [Positive consequence 1]
- [Positive consequence 2]
- [...]

### Negative
- [Negative consequence 1]
- [Negative consequence 2]
- [...]

### Neutral
- [Consequence that is neither clearly positive nor negative]
- [...]

## Alternatives Considered

### [Alternative 1: e.g., Flask]
**Pros**: [Benefits of this alternative]
**Cons**: [Drawbacks of this alternative]
**Rejected because**: [Specific reason this was not chosen]

### [Alternative 2: e.g., Django]
**Pros**: [Benefits of this alternative]
**Cons**: [Drawbacks of this alternative]
**Rejected because**: [Specific reason this was not chosen]

## Implementation Guidelines

[Optional: Specific guidance for implementing this decision]

[Examples:
- Configuration requirements
- Migration steps if replacing existing technology
- Code organization patterns to follow
- Testing requirements
- Monitoring/observability requirements]

## Success Criteria

[Optional: How will we know if this decision was correct?]

[Examples:
- Performance benchmarks to meet
- Developer productivity metrics
- System reliability targets
- User experience improvements]

## References

[Links to supporting documentation, research, benchmarks, etc.]

- [Link 1: Technology documentation]
- [Link 2: Performance benchmarks]
- [Link 3: Team discussion notes]
- [Link 4: Related ADRs]

## Related Decisions

[List other ADRs that are related to this decision]

- ADR-YYYY: [Related decision title]
- ADR-ZZZZ: [Another related decision]

---

## ADR Writing Guidelines

### When to Write an ADR
- Choosing between major technology alternatives
- Adopting new architectural patterns
- Making decisions that affect multiple teams/systems
- Decisions that are difficult to reverse
- Decisions with significant trade-offs

### When NOT to Write an ADR
- Minor implementation details
- Temporary workarounds
- Decisions easily reversed
- Personal coding style preferences

### Tips for Good ADRs
1. **Be specific**: "Use PostgreSQL" not "Use a database"
2. **Include constraints**: Budget, timeline, team skills, compliance
3. **Show your work**: Explain the analysis process
4. **Be honest about downsides**: Every decision has trade-offs
5. **Keep it concise**: 1-2 pages max, focus on the essential information
6. **Update status**: Mark as superseded when replaced by newer decisions