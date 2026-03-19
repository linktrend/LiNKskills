# AIOS Integration Contract (Internal, Phase 2-3)

## Request Flow
1. AIOS calls `POST /v1/runs` with internal `tenant_id`, `principal_id`, and `capability_id` or `package_id`.
2. LiNKskills returns `run_id`, current status, and next action (`/v1/disclosures/issue`).
3. AIOS calls `POST /v1/disclosures/issue` with `run_id` and step scope.
4. LiNKskills performs policy checks, issues disclosure token + manifest reference, executes managed step, finalizes run, and stores receipt.
5. AIOS polls `GET /v1/runs/{run_id}` and `GET /v1/receipts/{receipt_id}`.

## Response Contract Guarantees
- Stable run identifier (`run_id`) for all downstream queries.
- Deterministic policy decision records in audit stream.
- Metadata-only success storage.
- Receipt includes retention class and purge metadata.

## Security Scope
- Internal tenants only.
- Managed mode only.
- No public capabilities.
