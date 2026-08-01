# Cursor Canary Rollback (Project-Scoped Only)

- **Date:** 2026-08-01
- **Owner:** LiNKskills (Lane C — Cursor product canary)
- **Scope:** Project-scoped MCP / canary artifacts only
- **Live canary:** **false** — this packet does not start or roll back a live Cursor canary
- **Global Cursor:** **untouched** — never edit `~/.cursor/mcp.json` or user-level Cursor settings for this rollback

## Platform pin (read-only)

| Field | Value |
|---|---|
| Certified Platform candidate | `421a35e97bc302be0f5e1f196d0a5e8d132f6fd8` |
| Meaning | **Certified candidate ≠ live** PACI issuer, hosting, credentials, or migration authority |
| Envelope | Frozen `platform.auth-token-envelope/0.1.0` (not `0.1.3-draft`) |

## What this rollback covers

Project-scoped Cursor canary artifacts under LiNKskills:

- Example fragment: `configs/fragments/cursor-skills-canary.mcp.json.example`
- Docs: `docs/integrations/cursor/**`
- Honesty / stage evidence: `evidence/phase7/cursor-canary-status.json`
- Representative skill set (selection only): `evidence/phase1/canary-set.json`

## Immediate stop (if a project-scoped canary profile was ever applied)

1. **Disable** the project-scoped `linkskills-canary` MCP server entry (or remove the copied fragment from the project MCP surface).
2. **Do not** touch `~/.cursor/mcp.json`, shared IDE Development `.cursor`, hooks, or user settings.
3. **Confirm** no `LINKSKILLS_CANARY=1` production process remains attached to this worktree.
4. **Leave secrets alone** — do not rotate Platform credentials from Skills; Platform owns issuer/credentials.

## Git rollback (this packet)

If Lane C doc/fragment/evidence edits need undoing:

```bash
# Revert only the Lane C commit on the correction branch (integrator-owned).
git revert <lane-c-commit-sha>
```

No live Gateway, PACI issuer, migration, or global Cursor action is part of rollback.

## Honesty markers after rollback

- `evidence/phase7/cursor-canary-status.json` must keep `live_proven: false`, stages 3–8 blocked/not-started.
- Do not advertise `platform.auth-token-envelope/0.1.3-draft`.
- Do not imply the certified Platform candidate is a live stage PACI service.
