# Example Trace: Reverse-Engineering Mode

## Scenario
User provides a third-party "email-helper" prompt and asks for conversion into LiNKskills standards.

## Trace
**User**: "Use skill-architect to convert this third-party prompt into a production LiNKskills skill."

**Action**: Select mode `REVERSE_ENGINEER`.
**Action**: Structural Audit:
- Step A: Extract tools (`read_file`, `write_file`, `mcp-email`).
- Step B: Map source instructions to Phase 1-5 workflow.
- Step C: Inject Decision Tree with fail-fast checks and `task_id` persistence.
- Step D: Seed `references/old-patterns.md` with migration-specific failure modes.

**Action**: Generate full skill folder and contracts.
**Action**: Run `validator.py`.

**Response**: Converted skill now follows Golden Template structure, includes resumability, schema contracts, old-patterns, and changelog versioning.

