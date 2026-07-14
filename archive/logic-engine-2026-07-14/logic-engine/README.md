# LiNKskills Logic Engine (Phase 0-3)

Internal control-plane service for LiNKskills. This module implements Phase 0-3 of the Logic Engine roadmap without modifying skill frontmatter.

## Scope (Implemented)
- Phase 0: governance and normalization documents.
- Phase 1: deterministic registry extraction from repository artifacts.
- Phase 2: internal-only API/auth/run foundation with API-key bound tenant+principal identity.
- Phase 3: managed disclosure tokens, immediate managed execution, receipt/cost ledger, and retention sweep.
- PRD v4.0 controls: idempotency (24h), strict AIOS identity fields, DPR registry checks, kill-switch hierarchy, SLO telemetry.

## Not in Scope (Deferred)
- External/public tenant onboarding.
- Client-side JIT execution.
- MCP transport (REST-first launch).
- Class B/C commercial activation (policy scaffolding only).

## Local Setup
```bash
cd services/logic-engine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Build Registry
```bash
python scripts/build_registry.py \
  --repo-root ../.. \
  --output generated/catalog.json \
  --packages config/packages.json
```

## Run API
```bash
export LOGIC_ENGINE_REPO_ROOT=/absolute/path/to/LiNKskills
export LOGIC_ENGINE_DATA_PATH=/absolute/path/to/LiNKskills/services/logic-engine/runtime/store.json
export LOGIC_ENGINE_SECRET_PROVIDER=gsm
export LOGIC_ENGINE_GCP_PROJECT_ID=<your-gcp-project-id>
python scripts/run_api.py
```

Production secret contract:
- Dev/prod execution paths require GSM-backed secret resolution.
- `LOGIC_ENGINE_ENV=production` requires GSM file reads (`LOGIC_ENGINE_GSM_SECRET_FILE`) for execution paths.
- GSM read failure is fail-closed for writes and enables controlled safe mode.

## Supabase Schema Standard
- Shared internal Supabase project schema for LiNKskills: `lskills_core`.
- Database sessions should use `search_path=lskills_core,public`.
- Migration naming standard for new migrations: `YYYYMMDD_HHMMSS_lskills_<change>.sql`.
- Apply SQL migrations in order:
```bash
psql "$DATABASE_URL" -f sql/001_schema.sql
psql "$DATABASE_URL" -f sql/002_rls.sql
```

## Run Retention Sweep
```bash
python scripts/run_retention_worker.py
```

## Core Endpoints
- `GET /v1/catalog/skills`
- `GET /v1/catalog/packages`
- `GET /v1/skills/{skill_id}`
- `POST /v1/runs`
- `GET /v1/runs/{run_id}`
- `POST /v1/disclosures/issue`
- `GET /v1/receipts/{receipt_id}`
- `GET /v1/ops/slo`
- `GET /v1/ops/dashboard`
- `GET /v1/ops/safe-mode`

Write contract highlights:
- Service API key bearer auth required for all `/v1/*` except `GET /v1/ops/safe-mode` (orchestration health probe).
- `POST /v1/runs` requires `idempotency_key`, one of `capability_id|package_id`, and billing identity by track.
- `origin=AIOS` additionally requires `mission_id`, `task_id`, `dpr_id` (regex + active registry check).
- `POST /v1/disclosures/issue` requires `idempotency_key` and executes managed step immediately (30s timeout, else polling).

## Data Retention Defaults
- Success: metadata-only.
- Failure/blocked: redacted diagnostics retained for 30 days.
- Disclosure and audit metadata: retained for 180 days.
- Financial ledger metadata: retained for 7 years.
