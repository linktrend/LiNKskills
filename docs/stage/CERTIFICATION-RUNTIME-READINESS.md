# Certification runtime readiness — local vs stage

**Packet:** SKILLS-STAGE-CERTIFICATION (canary lifecycle)
**Host of sealed canary proof:** local privileged Docker Linux + `bwrap` (not stage / not VPS)
**macOS agent worktree:** still **not** a sealed certifier by itself

## Proven locally (this lane)

| Claim | Status | Notes |
|---|---|---|
| Migration manifest SHA-256 rows match SQL bytes | Proven | Eight files `000002`–`000009` |
| Structural migration package tests | Proven | No live DB required |
| Ephemeral disposable Postgres apply + RLS/gateway/review_queue | Proven when suite green | Docker/ephemeral only; never stage/prod |
| Fail-closed confinement refuses unproven isolation under default mode | Proven | `run_confined` raises without `allow_unproven` |
| With `LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven` | Stamps `unproven` | Explicitly **not** certifiable |
| Privileged Docker Linux + `bwrap` sealed catalog canary | Proven | release mode: external issuer key + digest-pinned image → `canary-echo` `usable`; `--local-non-promoting` stays non-promoting |

## Blocked for stage / shared runtime

| Claim | Status | Why |
|---|---|---|
| Stage `lskills` schema applied | **BLOCKED** | Platform-only live apply; no stage apply receipt |
| Backup/restore readiness on shared DB | **BLOCKED** | Template only |
| macOS host stamps `network_isolation=denied` | **BLOCKED** | path-allowlist sandbox does not boot certifiably |
| Remaining 34 catalog skills `usable` | **BLOCKED** | Suites lack executable `execute` blocks / sealed receipts |
| Stage PACI / live Gateway against shared DB | Out of apply scope; still **not claimed** | No invented endpoints |

## Separation rule

Local ephemeral Postgres success **≠** stage migration success.
Local `unproven` executor runs **≠** sealed certification.
Local privileged Docker sealed canary **≠** stage/prod shared readiness.

## Reproducible sealed canary command

```bash
# Release/promoting (default): external issuer key + digest-pinned image required
LINKSKILLS_EVAL_RUNNER_ISSUER_KEY=… \
LINKSKILLS_SEALED_CERT_IMAGE=python@sha256:<digest> \
  ./scripts/run-sealed-linux-certify.sh
# or targeted:
LINKSKILLS_EVAL_RUNNER_ISSUER_KEY=… \
LINKSKILLS_SEALED_CERT_IMAGE=python@sha256:<digest> \
  ./scripts/run-sealed-linux-certify.sh --skill canary-echo

# Local non-promoting smoke (no usable promotion / no sealed release evidence write)
./scripts/run-sealed-linux-certify.sh --local-non-promoting --skill canary-echo

python3 scripts/build-catalog-index.py --check
```

## References

- ADR 0009 / `evidence/phase10/CLASSIFICATION-HONESTY.md`
- `packages/tool_runtime/linkskills_tool_runtime/confined_exec.py`
- `scripts/certify-catalog.py` / `scripts/run-sealed-linux-certify.sh`
- `docs/migrations/PREFLIGHT-STAGE-READINESS.md`
- `docs/stage/MIGRATION-RUNTIME-STAGE-GATE.md`
