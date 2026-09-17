# MCP production vs observed v0.1 adapter

- Production: `linkskills-mcp-v2` → MCP `2026-07-28`, resource-first
  `skills.api.v0.2`, shared `linkskills_core.provider_v2` domain.
- Observed compatibility: `linkskills-mcp-server` / `python -m linkskills_mcp`
  → MCP `2024-11-05`, 15 legacy tools, no resources.

`skills_run_*` and `skills_tool_*` on v2 return `legacy_execution_disabled`.
Rollback restores the retained v0.1 image; see
`packages/gateway/docs/INSTALL-UPGRADE-ROLLBACK.md`.
