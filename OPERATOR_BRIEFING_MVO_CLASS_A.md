# LiNKskills Operator Briefing (MVO Class A)

## Audience
This document is for operators coordinating LiNKskills Logic Engine usage after the Phase 0-3 implementation.

## What Changed
The repository is no longer only a static library. It now includes an internal control-plane service under `services/logic-engine` that executes managed runs through REST APIs with policy, billing, and retention controls.

## MVO Scope (Now)
- Class A execution is active.
- Class B/C remain scaffolded but non-active for commercial execution.
- Managed execution only (`MANAGED`).
- REST-first operations.
- Internal machine callers only for MVO.

## Core Operational Rules
1. Do not edit golden skill frontmatter in `skills/*/SKILL.md` for Logic Engine remediation.
2. Use service API keys for machine-to-machine access.
3. Always supply idempotency keys on write requests.
4. For AIOS-origin requests, include `mission_id`, `task_id`, and `dpr_id`.
5. Use one billing identity per run context (`venture_id` or `client_id` only, based on track).

## Required API Contract Snapshot
For `POST /v1/runs`, include:
- `tenant_id`
- `principal_id`
- `idempotency_key`
- one-of `capability_id|package_id`
- `billing_track`
- Track 1: `venture_id`; Track 2: `client_id`

For AIOS-origin calls, also include:
- `origin=AIOS`
- `mission_id`
- `task_id`
- `dpr_id`

For `POST /v1/disclosures/issue`, include:
- `run_id`
- `step_scope`
- `idempotency_key`

## Runtime Behavior Operators Must Expect
### Idempotency
- Duplicate write with same payload in 24h returns original response.
- Same key with different payload returns `409`.

### Execution
- `run_id` is server-generated.
- Disclosure endpoint triggers managed step execution immediately.
- If execution exceeds timeout, response returns running status and operators poll run/receipt endpoints.

### Production Secret Safety
- Production execution requires GSM-read secret availability.
- GSM failure enters safe mode and denies new execution writes.

## Kill-Switch Operations
### Levels
- Level 1: normal operation.
- Level 2: protective halt (default behavior blocks new runs).
- Level 3: deterministic reversion and emergency control.

### Automated Level-2 Thresholds
Runaway cost spike if any:
- rolling 15-min spend > $75, OR
- burn-rate > 3x 24h moving average for 10 min, OR
- projected month-end > $1000 in 2 consecutive 5-min windows.

Security anomaly if any:
- >= 3 critical security exceptions in 10 min, OR
- >= 10 invalid-signature/replay failures from one source in 5 min, OR
- confirmed credential-compromise signal.

## Data Handling and Retention
- Success runs: metadata-only persistence.
- Failure diagnostics: redacted, retained 30 days.
- Disclosure/receipt/audit metadata: retained 180 days.
- Financial ledger metadata: retained 7 years.

## Daily Operator Runbook
1. Validate repository structure:
   - `python3 validator.py --repo-root . --scan-all`
2. Verify frontmatter immutability gate:
   - `bash scripts/ci-check-frontmatter.sh`
3. Rebuild service catalog from manifest:
   - `python3 services/logic-engine/scripts/build_registry.py --repo-root . --output services/logic-engine/generated/catalog.json --packages services/logic-engine/config/packages.json`
4. Run service (non-prod validation):
   - `python3 services/logic-engine/scripts/run_api.py`
5. Review dashboard/safety surfaces:
   - `/v1/ops/slo`
   - `/v1/ops/dashboard`
   - `/v1/ops/safe-mode`
6. Run retention worker:
   - `python3 services/logic-engine/scripts/run_retention_worker.py`

## Escalation Conditions
Escalate to engineering/platform owners when:
- repeated DPR validation failures occur for valid requests,
- safe mode is active in production,
- Level-2 or Level-3 triggers fire,
- billing identity conflicts or unresolved policy denials appear,
- idempotency conflicts indicate client contract misuse.

## Current Internal Tenant Lock
Canonical internal tenant UUID:
- `00000000-0000-0000-0000-000000000001`

Human label:
- `linktrend_internal`
