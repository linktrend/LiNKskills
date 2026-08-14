# Provider v2 source operations and operational HOLDs

`skills.api.v0.2` uses MCP `2026-07-28` sessionless semantics. Read-only
material is resource-first: capability/domain guide, bounded catalogue/search,
release history/summary/qualification, exact manifest/entrypoint, sections,
fragments, resources, content and package. Bounded tools are release
verification, telemetry/feedback submission and receipt status, and Librarian
status. `skills_run_*` and `skills_tool_*` are excluded from v2.

The source-level status surface returns per-capability state (`available`,
`degraded`, `offline`, `unauthorized`, `forbidden`, `contract_incompatible`,
`stale`, `disabled`). Liveness only proves process existence. Readiness never
proves qualification, consumer configuration/execution, workflow completion,
deployment or production readiness.

Source proof does not activate a trusted signing key, sandbox container,
database migration, hosted Librarian runner, consumer connection, availability
target, alert receiver, backup/restore system, stage/prod release, or canary.
