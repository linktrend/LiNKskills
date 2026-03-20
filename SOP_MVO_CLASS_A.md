# LiNKskills Master SOP (MVO Class A, Post Phase 0-3)

This SOP is the updated operating standard after implementation of the LiNKskills Logic Engine Phase 0-3 scope aligned to PRD v4.0.

## 1. System State
LiNKskills now has two coordinated planes:
1. Authoring/governance plane (skills/tools repository).
2. Runtime control plane (`services/logic-engine`) serving managed capability execution.

## 2. Scope and Activation
- Active in MVO: Class A internal managed execution.
- Deferred: Class B commercialization and Class C activation.
- Interface: REST-first.
- Runtime mode: managed only.

## 2A. Google CLI Ownership Standard
- Workspace services are owned by `gws`.
- Non-Workspace Google, non-Google, and interim gap services are owned by `ltr`.
- Ownership source of truth: `configs/service_ownership.json`.

## 3. Security and Identity Baseline
### Fortress Controls
- Vault-based secret handling remains required.
- Frontmatter immutability remains enforced.

### Machine Identity
- Service API keys are authoritative identity mechanism for MVO run path.
- Each key binds fixed tenant/principal identity.
- Caller identity override is rejected.

### Canonical Internal Tenant
- UUID: `00000000-0000-0000-0000-000000000001`
- slug: `linktrend_internal`

## 4. API Operating Contract
### Run creation (`POST /v1/runs`)
Must include:
- `tenant_id`
- `principal_id`
- `idempotency_key`
- exactly one target (`capability_id` or `package_id`)
- billing identity per track (`venture_id` or `client_id`)

AIOS-origin must also include:
- `mission_id`
- `task_id`
- `dpr_id`

### Disclosure execution (`POST /v1/disclosures/issue`)
Must include:
- `run_id`
- `step_scope`
- `idempotency_key`

Semantics:
- disclosure issuance and managed step execution are coupled.
- terminal response if complete within 30s.
- otherwise returns running state and relies on polling endpoints.

## 5. Idempotency Standard
- 24-hour dedupe window on write APIs.
- Same key and normalized payload => replay original output.
- Same key with payload mismatch => `409 conflict`.

## 6. Capability Policy and Versioning
- If version omitted, resolve latest certified internal active version allowed for tenant policy.
- Managed execution enforces class and lifecycle/visibility gates.
- Package execution is linear `step_order` only in MVO.

## 7. DPR and AIOS Controls
- DPR is strict ingress gate for AIOS requests.
- Validate DPR V3 format and active registry state.
- Invalid DPR is rejected and audited.

## 8. Costing and Financial Ledger SOP
Per-run billing uses:
- token cost,
- complexity multiplier,
- external tool pass-through cost.

Rules:
- consume inline tool cost when supplied,
- estimate from pricing table when missing, set `estimated=true`.

Authority:
- financial source of truth is Supabase ledger model (LiNKbrain domain).

## 9. Class B/C Scaffolding SOP
### Class B (`STUDIO_PROPRIETARY`)
- entitlement source must be server-side finance registry.
- client-side override is prohibited.
- override authority path:
  - Head of Finance + COO/CEO,
  - Chairman emergency override.

### Class C
- hidden-turn audit framework modeled but non-active in MVO.

## 10. Kill-Switch SOP
### Levels
- Level 1: normal operations.
- Level 2: protective halt.
- Level 3: deterministic reversion/emergency rollback.

### Level-2 automated thresholds
Runaway cost:
- 15-min spend > $75, OR
- burn-rate > 3x 24h average for 10 min, OR
- projected month-end > $1000 in 2 consecutive 5-min windows.

Security:
- >= 3 critical exceptions in 10 min, OR
- >= 10 invalid-signature/replay failures from one source in 5 min, OR
- credential-compromise signal.

Operational default:
- block new runs immediately.
- in-flight runs complete unless hard-cancel condition applies.

## 11. Production Secret and Safe-Mode SOP
- Production execution path requires GSM reads.
- If GSM read fails in production:
  - enable safe mode,
  - reject execution writes (fail closed),
  - maintain health/read visibility.

## 12. Retention and Purge SOP
Retention classes:
- success run: metadata only,
- failure traces: redacted diagnostics 30 days,
- disclosure/receipt/audit metadata: 180 days,
- financial ledger metadata: 7 years.

Operation:
- run daily retention sweep worker,
- persist purge confirmation metadata/hash.

## 13. Observability and SLO SOP
SLO for Class A MVO:
- uptime target: 99.5%
- API envelope p95 target: 2s

Operational endpoints:
- `/v1/ops/slo`
- `/v1/ops/dashboard`
- `/v1/ops/safe-mode`

## 14. Validation and Release Checklist
1. `python3 validator.py --repo-root . --scan-all`
2. `bash scripts/ci-check-frontmatter.sh`
3. rebuild catalog via registry compiler.
4. run logic-engine test suite.
5. verify ops endpoints and retention worker.

## 15. Document Control
- This file is the updated SOP companion for post-implementation operations.
- Original baseline SOP remains unchanged at `SOP.md`.
