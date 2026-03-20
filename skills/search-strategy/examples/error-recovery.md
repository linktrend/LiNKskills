# Error Recovery Pattern

Scenario: agent needs deep brief mode but has no operator approval.

1. Agent logs intent event through LTRAuditLogger.
2. Agent checkpoints `PENDING_APPROVAL` and waits.
3. Operator sends `PROCEED`.
4. Agent resumes, executes deep brief, and finalizes output.
