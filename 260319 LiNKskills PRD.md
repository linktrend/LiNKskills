# 260319 LiNKskills PRD
## Version 4.0 (Chairman-Locked MVO)

Status: Source of Truth
Date: 2026-03-19
Scope: LiNKskills Logic Engine

## 1. Product Definition
LiNKskills is a centralized server that hosts skills and tools and serves them through controlled contracts to internal and external applications. For MVO, launch scope is internal workloads only.

## 2. MVO Scope Lock
- Class A: active at launch.
- Class B: scaffolding allowed, not commercially active.
- Class C: out of MVO execution scope.
- Execution mode for MVO: `MANAGED` only.
- Interface at launch: REST-first. MCP deferred.
- JIT client-side execution: deferred.

## 3. Source of Truth and Governance
- This PRD (`v4.0`) is product source of truth for LiNKskills.
- Where older repo docs conflict, this PRD plus Chairman-locked MVO decisions win.
- Golden skill anatomy/frontmatter is immutable through Phase 0-3.

## 4. Identity and Request Contract
Mandatory on write requests:
- `tenant_id`
- `principal_id`
- `idempotency_key`
- exactly one of `capability_id | package_id`

AIOS-origin requests must additionally include:
- `mission_id`
- `task_id`
- `dpr_id`

Run identifiers:
- `run_id` is server-generated on `POST /v1/runs`.
- `run_id` is mandatory for subsequent calls and logs.

Billing identity one-of:
- Track 1 requires `venture_id`.
- Track 2 requires `client_id`.
- Do not allow both in same billing context.

Canonical internal tenant for machine contracts:
- `00000000-0000-0000-0000-000000000001`
- slug: `linktrend_internal`

## 5. Idempotency
- Applies to write operations (`POST /v1/runs`, `POST /v1/disclosures/issue`).
- TTL window: 24 hours.
- Same key + same normalized payload: return original response/result.
- Same key + different payload: return `409 conflict`.

## 6. Auth Model (MVO)
- Machine-to-machine bearer service API key required.
- API key is bound to fixed `tenant_id + principal_id`.
- Caller principal override is not trusted.
- Supabase user JWT is not required for MVO run APIs.

## 7. Capability and Version Policy
- Omitted `version` resolves to latest certified internal active version allowed by class/tenant policy.
- Certification and activation metadata must exist at capability-version level.
- Package execution in MVO is linear `step_order` only.

## 8. DPR Validation
- `dpr_id` is validated strictly at ingress.
- Must pass DPR V3 format check.
- Must be active in DPR registry and policy-valid.
- Invalid identity is rejected and audited.

## 9. Disclosure and Execution Semantics
`POST /v1/disclosures/issue` must:
- run policy checks,
- issue scoped disclosure token/manifest,
- execute managed step immediately.

Timeout behavior:
- 30-second execution timeout for terminal response.
- If not finished: return running state and require polling on runs/receipts.
- No callback dependency for MVO.

Disclosure claims:
- `tenant_id`, `run_id`, `capability_id`, `version`, `step_scope`, `mode=MANAGED`, `exp`, `jti`.

## 10. Billing and Financial Source of Truth
Bill formula per run:
- token cost + complexity multiplier + external tool pass-through.

Complexity multiplier:
- effective-dated table keyed by `capability_id + version`.
- Librarian proposes.
- Finance approves billable multiplier (dual control).

Tool costs:
- prefer inline tool-reported run costs.
- if missing, estimate from provider pricing table and mark `estimated=true`.

Ledger authority:
- Supabase LiNKbrain ledger tables are financial source of truth.
- downstream external finance sync is non-authoritative.

## 11. Class B / Class C Policy Scaffolding
Class B (`STUDIO_PROPRIETARY`):
- entitlement truth is server-side finance registry.
- no client-side override.
- override authority: Head of Finance + COO/CEO.
- Chairman emergency override allowed.

Class C hidden-turn audit framework (for future activation):
- schema/policy checks,
- deterministic eval suite,
- adversarial/red-team checks.

## 12. Kill Switch and Automated Protection
Hybrid controls: manual + automated thresholds.

Level-2 default:
- block new runs immediately,
- allow in-flight runs to finish.

Hard-cancel in-flight only for critical security/runaway-cost incidents.

Level-2 automated triggers (explicit):
Runaway cost spike if any:
- rolling 15-min spend > $75, OR
- burn-rate > 3x 24h moving average for 10 minutes, OR
- projected month-end spend > $1000 hard cap in 2 consecutive 5-min windows.

Security anomaly if any:
- >= 3 critical security exceptions in 10 minutes, OR
- >= 10 invalid-signature/replay failures from one source in 5 minutes, OR
- confirmed credential-compromise signal.

Level-3 deterministic reversion trigger:
- confidence/pass score < 0.80 on rolling window (min sample 30, target 100), OR
- severe consecutive critical-failure condition,
- then rollback to last certified version.

## 13. Secrets and Production Safety
- Production requires GSM reads for execution paths.
- On GSM failure in production: fail closed for new execution.
- Enter controlled safe mode (health/read-only visibility allowed, execution denied).
- No production fallback to local/env secrets.
- Non-prod can use transitional fallback.

## 14. Retention and Compliance
- Success path: metadata only (no raw payload persistence).
- Failure traces: redacted diagnostics for 30 days.
- Disclosure/receipt/audit metadata: 180 days.
- Financial audit ledger: 7 years.
- Daily purge worker with auditable confirmations.

## 15. SLO and Launch Consumers
Class A launch SLO targets:
- uptime: 99.5%
- API response envelope p95: 2 seconds

MVO first consumers:
- AIOS
- LiNKautowork

External applications:
- deferred.

## 16. Technology Defaults
- Python 3.11 + FastAPI + Pydantic v2
- Supabase Postgres/Auth/Storage (single shared project with strict RLS + role/schema isolation)
- DigitalOcean compute for API/orchestration

## 17. Phase 0-3 Deliverable Intent
- Phase 0: governance/decision locks and terminology.
- Phase 1: deterministic registry extraction from manifest/skills/tools.
- Phase 2: internal control-plane API/auth/run foundation.
- Phase 3: managed progressive disclosure runtime, receipts, retention, and audit reconstruction.
