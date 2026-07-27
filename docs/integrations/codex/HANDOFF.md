# Codex Handoff — LiNKskills Skills MCP Fragment

- **Status:** Fragment + conformance ownership handoff
- **Date:** 2026-07-27
- **Fragment:** `configs/fragments/codex-skills.config.toml.fragment`

## Ownership

| Asset | Owner |
|---|---|
| Independently named Skills MCP fragment + Skills conformance tests | **LiNKskills** |
| Shared Codex `config.toml` / host hooks application | **LiNKbrain** (default shared Codex host owner) |

LiNKskills does **not** edit shared Codex host configuration in this repo. The fragment is authored for the LiNKbrain owner to apply when ready.

## Delivered by LiNKskills

- `configs/fragments/codex-skills.config.toml.fragment` — independently named `mcp_servers.linkskills_skills` entry (no secrets).
- MCP/gateway conformance coverage under `tests/mcp_server/` and `tests/gateway/`.
- Auth spoof-rejection and HTTP/MCP `skills_list` parity proofs.

## Expected from LiNKbrain owner

1. Review the fragment for naming collisions with Brain MCP entries.
2. Apply into the shared Codex host config only when ready.
3. Notify LiNKskills so Skills-side validation can run against the configured host.
4. Keep credentials out of the fragment; use Platform-issued env injection.

## Explicit non-goals

- No LiNKskills agent mutation of shared Codex files merely to set up development.
- No combined Brain/Skills credential or MCP surface.
