# SOP_MACHINE_MVO_CLASS_A

Machine-facing protocol for LiNKskills Logic Engine after Phase 0-3 implementation.

## 1. Mission
- Execute Class A capabilities deterministically through managed server runtime.
- Enforce identity, idempotency, policy, billing, and audit controls per PRD v4.0.
- Preserve source skill frontmatter immutability.

## 2. Mandatory Contract for Write APIs
### `POST /v1/runs`
Required fields:
- `tenant_id`
- `principal_id`
- `idempotency_key`
- exactly one of `capability_id|package_id`
- `billing_track`
- one billing identity by track:
  - Track 1 => `venture_id`
  - Track 2 => `client_id`

AIOS-origin requirement:
- `origin=AIOS` requires `mission_id`, `task_id`, `dpr_id`.

### `POST /v1/disclosures/issue`
Required fields:
- `run_id`
- `step_scope`
- `idempotency_key`

## 3. Identity and Auth Protocol
- All `/v1/*` calls require `Authorization: Bearer <service-api-key>`.
- API key resolves fixed `(tenant_id, principal_id)`.
- Caller payload identity must match key binding.
- Reject identity override attempts.

## 4. DPR Enforcement
- Apply DPR V3 regex validation at ingress.
- Verify `dpr_id` is active in registry for tenant.
- Reject and audit failures.

## 5. Version and Policy Resolution
- If request version omitted, resolve latest certified internal active version permitted by policy.
- Enforce Class A only for MVO execution.
- Keep Class B/C scaffolding non-active in managed run path.

## 6. Managed Disclosure Runtime
- `POST /v1/disclosures/issue` performs disclosure issuance and managed step execution.
- Timeout envelope: 30 seconds.
- If terminal not reached within envelope, return running state and require polling:
  - `GET /v1/runs/{run_id}`
  - `GET /v1/receipts/{receipt_id}`

Disclosure claim contract:
- `tenant_id`, `run_id`, `capability_id`, `version`, `step_scope`, `mode=MANAGED`, `exp`, `jti`.

## 7. Idempotency Contract
- TTL: 24h.
- Same key + same normalized payload => return original response.
- Same key + different payload => `409`.
- Scope includes endpoint + tenant + principal + key + payload hash.

## 8. Costing and Ledger Protocol
Per-run cost:
- token cost + complexity multiplier + external tool pass-through.

Rules:
- prefer inline tool costs from run payload,
- estimate from pricing tables if missing and mark `estimated=true`.

Ledger:
- write financial ledger entry with track identity and retention metadata.

## 9. Kill-Switch and Safety Protocol
### Level behavior
- Level 2 blocks new runs immediately.
- In-flight runs finish by default.
- Hard-cancel only for critical security/runaway-cost conditions.

### Automated trigger thresholds (explicit)
Runaway cost:
- 15-min spend > $75, OR
- burn-rate > 3x 24h average for 10 min, OR
- projected month-end > $1000 in 2 consecutive 5-min windows.

Security:
- >= 3 critical security exceptions in 10 min, OR
- >= 10 invalid-signature/replay failures from one source in 5 min, OR
- credential-compromise confirmation.

Level-3 trigger:
- rolling confidence/pass < 0.80 (min 30 samples, target 100), OR
- severe consecutive critical failures,
- then deterministic rollback to last certified version.

## 10. Secret Provider and Safe Mode
- Production execution requires GSM-read secrets.
- GSM failure in production => fail closed for execution writes + safe mode enabled.
- Health and read-only surfaces remain available.

## 11. Retention Worker Protocol
Retention classes:
- success metadata only,
- failure diagnostics 30d,
- disclosure/receipt/audit metadata 180d,
- financial ledger 7y.

Daily task:
- run retention sweep and persist purge confirmation hash record.

## 12. Required Verification Commands
- `python3 validator.py --repo-root . --scan-all`
- `bash scripts/ci-check-frontmatter.sh`
- `python3 services/logic-engine/scripts/build_registry.py --repo-root . --output services/logic-engine/generated/catalog.json --packages services/logic-engine/config/packages.json`
- `python3 -m unittest discover -s services/logic-engine/tests -v`
