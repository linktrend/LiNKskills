# Cursor Canary Plan (Stages 1–8)

- **Status:** Plan + fake/contract evidence only
- **Date:** 2026-07-27
- **Owner:** LiNKskills (Cursor product canary)
- **Fragment:** `configs/fragments/cursor-skills-canary.mcp.json.example`

## Proven in this repo

**Only the fake/contract stage is proven here.** Project-scoped MCP/gateway unit tests and the example fragment exist. **No global Cursor mutation was performed** (no edits to `~/.cursor/mcp.json`, shared IDE Development `.cursor` symlink target, or user-level Cursor settings).

## Stages

| Stage | Intent | Status in this repo |
|---|---|---|
| 1 | Prove fake/contract tests with isolated or project-scoped configuration | **Proven (fake/contract)** via gateway/MCP/client tests + example fragment |
| 2 | Inspect `.cursor` symlinks and shared/global settings read-only; record ownership | Documented in `docs/inventories/cursor-codex-mutation-surfaces.md` — no mutation |
| 3 | Stage read-only discovery | Not run against live Cursor in this change set |
| 4 | Stage run/telemetry with non-side-effecting skills | Not run live |
| 5 | Exact packaged tool + artifact validation | Not run live |
| 6 | Controlled failures / feedback / offline buffer | Client `LocalEventBuffer` unit-covered; not live Cursor |
| 7 | Librarian dry-run then evidence-backed write mode | Domain worker conformance only |
| 8 | Multi-day real use of representative canary set | Not started |

## Guardrails

- Prefer project-scoped configuration from the example fragment.
- If global Cursor mutation becomes unavoidable, stop, obtain the coordinated maintenance window, and record rollback evidence before changing anything.
- Secrets never belong in the fragment; Platform issues actor credentials separately.
