# Cursor Canary Rollback (Project-Scoped Only)

- **Date:** 2026-08-01
- **Owner:** LiNKskills (Lane C — Cursor product canary)
- **Scope:** Project-scoped MCP / canary artifacts only
- **Live canary:** **false** — this packet does not start or roll back a live Cursor canary
- **Global Cursor:** **untouched** — never edit `~/.cursor/mcp.json` or user-level Cursor settings for this rollback
- **Mode:** **Revert-only** for Git; **project-scoped disable** for any applied project MCP entry

## Platform pin (read-only)

| Field | Value |
|---|---|
| Certified Platform candidate | `421a35e97bc302be0f5e1f196d0a5e8d132f6fd8` |
| Meaning | **Certified candidate ≠ live** PACI issuer, hosting, credentials, or migration authority |
| Envelope | Frozen `platform.auth-token-envelope/0.1.0` (not `0.1.3-draft`) |

## What this rollback covers

Project-scoped Cursor canary artifacts under LiNKskills:

- Example fragment: `configs/fragments/cursor-skills-canary.mcp.json.example`
- Docs: `docs/integrations/cursor/CANARY.md`, `ROLLBACK.md`, `TELEMETRY-CONTRACT.md`, `PACI-CLIENT-APPLICATION-HANDOFF.md`
- Honesty / stage evidence: `evidence/phase7/cursor-canary-status.json`
- Readiness summary: `evidence/stage-readiness/cursor-canary-readiness.json`
- Representative skill set (selection only): `evidence/phase1/canary-set.json`
- Contract tests: `tests/integrations/test_cursor_canary_contract.py`, `tests/config/test_cursor_canary_fragment_durable.py`

## Immediate stop (if a project-scoped canary profile was ever applied)

1. **Disable** the project-scoped `linkskills-canary` MCP server entry (or remove the copied fragment from the project MCP surface).
2. **Do not** touch `~/.cursor/mcp.json`, shared IDE Development `.cursor`, hooks, or user settings.
3. **Confirm** no `LINKSKILLS_CANARY=1` production process remains attached to this worktree.
4. **Leave secrets alone** — do not rotate Platform credentials from Skills; Platform owns issuer/credentials.
5. **Do not** flush or delete stage telemetry stores from Skills; local offline buffers (`.linkskills_event_buffer.jsonl`) may be removed from the worktree only if they contain no secrets (they must already be redacted per `TELEMETRY-CONTRACT.md`).

## Git rollback (this packet)

If Lane C doc/fragment/evidence edits need undoing:

```bash
# Revert only the Lane C commit on the correction branch (integrator-owned).
git revert <lane-c-commit-sha>
```

No live Gateway, PACI issuer, migration, Supabase, or global Cursor action is part of rollback.

## Honesty markers after rollback

- `evidence/phase7/cursor-canary-status.json` and `evidence/stage-readiness/cursor-canary-readiness.json` must keep `live_canary: false`, `global_cursor_mutation: false`, stages 3–8 blocked/not-started.
- Do not advertise `platform.auth-token-envelope/0.1.3-draft`.
- Do not imply the certified Platform candidate is a live stage PACI service.
- Telemetry contract docs remain “future stage / not live-proven” after revert or disable.
