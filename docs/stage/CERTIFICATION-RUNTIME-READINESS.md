# Certification runtime readiness — local vs stage

**Packet:** SKILLS-W20-STAGE-READINESS
**Lane:** B (runtime / isolation honesty adjacent to migration gate)
**Host of this evaluation:** macOS (Darwin) agent worktree — **not** a sealed Linux certifier

## Proven locally (this lane)

| Claim | Status | Notes |
|---|---|---|
| Migration manifest SHA-256 rows match SQL bytes | Proven | Eight files `000002`–`000009` |
| Structural migration package tests | Proven | No live DB required |
| Ephemeral disposable Postgres apply + RLS/gateway/review_queue | Proven when suite green | Docker/ephemeral only; never stage/prod |
| Fail-closed confinement refuses unproven isolation under default mode | Proven | `run_confined` raises without `allow_unproven` |
| With `LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven` | Stamps `unproven` | Explicitly **not** certifiable |

## Blocked for stage / certification

| Claim | Status | Why |
|---|---|---|
| Stage `lskills` schema applied | **BLOCKED** | Platform-only live apply; no stage apply receipt |
| Backup/restore readiness on shared DB | **BLOCKED** | Template only |
| `network_isolation=denied` sealed executor receipts on this host | **BLOCKED** | macOS path-allowlist sandbox does not boot certifiably; see gap doc |
| Catalog skill `usable` / sealed live certification | **BLOCKED** | Requires sealed Linux (or approved container/VM) receipts |
| Stage PACI / live Gateway against shared DB | Out of Lane B apply scope; still **not claimed** | No invented endpoints |

## Separation rule

Local ephemeral Postgres success **≠** stage migration success.
Local `unproven` executor runs **≠** sealed certification.

## References

- ADR 0009 / `evidence/phase10/CLASSIFICATION-HONESTY.md`
- `packages/tool_runtime/linkskills_tool_runtime/confined_exec.py`
- `docs/migrations/PREFLIGHT-STAGE-READINESS.md`
- `docs/stage/MIGRATION-RUNTIME-STAGE-GATE.md`
