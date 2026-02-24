# Old Patterns & Blacklist
> **AGENT INSTRUCTION**: This file is updated during Phase 5. Read this during the Decision Tree phase to avoid regression.

## Deprecated Heuristics
- **Stateless Plugin Pattern**: [Date Added]
  - **Reason**: Skills without persistence layers cannot resume tasks or maintain state across sessions.
  - **New Protocol**: Always include `.workdir/tasks/` structure and `persistence.required: true` in frontmatter.

- **Minimalist Scaffolding**: [Date Added]
  - **Reason**: Creating only SKILL.md without supporting folders leads to incomplete skills.
  - **New Protocol**: Always generate full structure: advanced/, examples/, references/, scripts/ directories.

- **Blind Third-Party Copying**: [Date Added]
  - **Reason**: Copying external prompts/skills without structural normalization imports hidden failure modes.
  - **New Protocol**: Use Structural Audit (tool extraction, 5-phase decomposition, decision-tree injection, failure seeding) before migration output.

- **One-Shot Refinement without Evidence**: [Date Added]
  - **Reason**: Updating SKILL.md without using ledger/pattern evidence causes regressions.
  - **New Protocol**: In REFINER mode, combine execution_ledger signals, old-pattern lessons, and user feature requests before patching.

- **Ignoring Intelligence Floor**: [Date Added]
  - **Reason**: Running complex skills on underpowered models causes unreliable reasoning and schema drift.
  - **New Protocol**: Require `engine` frontmatter and fail-fast if runtime tier/context does not meet minimums.

- **Skipping CLI-First Ordering**: [Date Added]
  - **Reason**: Direct API usage by default increases cost and reduces reproducibility.
  - **New Protocol**: Enforce tooling levels (Native CLI -> Wrapper Scripts -> API Exceptions -> MCP).

- **Unconditional JIT Loading**: [Date Added]
  - **Reason**: Enabling JIT for small specialist skills adds latency and planning overhead.
  - **New Protocol**: Activate JIT only for Generalist profile or tool count > 10.

- **No `get_tool_details` in JIT Mode**: [Date Added]
  - **Reason**: Planner blind spots occur when tool schemas are not fetched/cached.
  - **New Protocol**: Require `get_tool_details` and cache schema data in task-local state.

## Known Failure Modes
- **[Failure ID]**: [Date]
  - **Context**: [Task ID of the failed execution]
  - **Resolution**: [What the agent learned to do differently next time]

## Rejected Tones/Styles
- **Skipping Validation**: Always run validator.py after scaffolding, even if it seems correct.
- **Hardcoding Paths**: Use relative paths from repository root, not absolute paths.
- **Skipping Changelog Updates**: Every version/refinement must update references/changelog.md.
