# SOP_HUMAN_MVO_CLASS_A

Non-technical operating SOP updated for the implemented LiNKskills Logic Engine (Phase 0-3).

## 1. What This Is
LiNKskills now runs as both:
- a governed skill/tool library, and
- an internal managed execution server (`services/logic-engine`).

You request outcomes; the system enforces policy, identity, and audit controls before execution.

## 2. MVO Scope You Should Assume
- Active: Class A internal execution.
- Not active yet: Class B commercial usage, Class C execution.
- Execution mode: managed server execution only.
- Access mode: internal machine clients using service API keys.

## 2A. Google CLI Routing Standard
- Use `gws` for Google Workspace services.
- Use `ltr` for non-Workspace Google and non-Google lanes.
- Confirm ownership in `configs/service_ownership.json` before adding/changing service routes.

## 3. Inputs You Must Provide (Business Side)
For run requests, ensure the caller supplies:
- tenant and principal identity,
- idempotency key,
- one target (`capability_id` or `package_id`),
- billing track identity (`venture_id` for Track 1 or `client_id` for Track 2).

If origin is AIOS, also provide:
- `mission_id`
- `task_id`
- valid `dpr_id`

## 4. What the System Guarantees
- duplicate write requests are safely deduplicated for 24h,
- unsafe or invalid identity requests are rejected,
- run receipts and audit history are generated,
- successful runs do not persist raw payload bodies,
- retention windows are applied automatically.

## 5. Retention Rules (Operational)
- Success run data: metadata only.
- Failure diagnostics: redacted and kept 30 days.
- Disclosure/receipt/audit metadata: 180 days.
- Financial ledger records: 7 years.

## 6. Daily Human Checklist
1. Confirm secure environment and required keys are available.
2. Confirm policy inputs are complete before triggering work.
3. Verify run completion and receipt retrieval.
4. Review policy denials and escalations.
5. Review ops dashboard for safety/SLO alerts.

## 7. Common Errors and What They Mean
### `401` Unauthorized
- API key missing/invalid/revoked.

### `403` Access denied
- Request tenant/principal does not match bound API key identity.

### `409` Idempotency conflict
- Same idempotency key reused with different payload.

### `400` DPR or policy denied
- AIOS fields missing/invalid, DPR format invalid, or inactive DPR registry record.

### `503` Safe mode / secret unavailable
- Production secret source unavailable; execution is intentionally fail-closed.

## 8. Escalation
Escalate to platform/engineering when:
- safe mode remains active,
- kill-switch Level-2/3 is active,
- multiple policy denials occur for known-valid business requests,
- receipts or audit trails are not produced.
