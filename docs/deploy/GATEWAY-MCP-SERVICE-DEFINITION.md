# Gateway + MCP service definition (Platform-consumable)

Status: Skills-owned contract for Platform hosting. **No secrets in this file.**  
Last updated: 2026-07-30

## Identity

| Field | Value |
|---|---|
| Service family | `lskills` |
| HTTP service | `linkskills-gateway` |
| MCP service | `linkskills-mcp` |
| Package installs | `linkskills-gateway`, `linkskills-mcp` (+ `linkskills-core` / `linkskills-client` / `linkskills-librarian` as needed) |
| Runtime | Python ≥ 3.11, **stdlib HTTP** (no FastAPI/uvicorn required for Gateway) |
| PACI audience | `lskills-api` |
| Required service scope | `lskills` |
| Claim contract | Platform AuthClaims / PACI consumer pin (see `docs/contracts/frozen/`) |

LiNKskills is **not** LiNKbrain. Do not co-host as a combined Brain+Skills binary.

Logic Engine is retired (ADR 0001). Do not schedule archived compose services.

## Processes

### Gateway

| Field | Value |
|---|---|
| Entrypoint | `linkskills-gateway` or `python -m linkskills_gateway.server` |
| Default bind | `LINKSKILLS_GATEWAY_HOST` / `LINKSKILLS_GATEWAY_PORT` (default `127.0.0.1:8787`) |
| Protocol | HTTP/1.1 JSON |
| Operations | `POST /v1/{operation}` for approved `skills_*` surface |

### MCP

| Field | Value |
|---|---|
| Entrypoint | `linkskills-mcp` or `python -m linkskills_mcp.server` |
| Transport | stdio newline-delimited JSON-RPC (host-wired) |
| Tools | Same `skills_*` operation names as Gateway |

## Health endpoints (Gateway)

| Path | Type | Success | Semantics |
|---|---|---|---|
| `GET /health` | Liveness | `200` | Process up |
| `GET /ready` | Readiness | `200` / `503` | Catalog loaded + auth mode configured; optional store probe |
| `GET /metrics` | Metrics | `200` | Prometheus text; counters only (no payloads/secrets) |
| `GET /drain` | Ops | `200` | Drain flag + in-flight |
| `POST /drain` | Ops | `200` | Begin graceful drain |
| `POST /drain/cancel` | Ops | `200` | Clear drain |

Platform load balancers should use `/health` for liveness and `/ready` for
readiness. Treat `/drain` as operator-local / mesh-admin only.

## Environment variables (names only)

### Core process

| Name | Required | Example / notes |
|---|---|---|
| `LINKSKILLS_ENV` | recommended | `stage` / `prod` |
| `LINKSKILLS_REPO_ROOT` | recommended | Absolute checkout path |
| `LINKSKILLS_GATEWAY_HOST` | optional | Default `127.0.0.1` |
| `LINKSKILLS_GATEWAY_PORT` | optional | Default `8787` |
| `LINKSKILLS_AUTH_MODE` | production: yes | `production` or `local-test` |
| `LINKSKILLS_PLATFORM_AUTHENTICATOR` | production: yes | `module.path:Factory` (presence checked by `/ready`; module loaded at request verify / startup) |
| `LINKSKILLS_DRAIN` | optional | `1` to start drained |
| `LINKSKILLS_GATEWAY_DURABLE` | optional | `1` enables durable store + ready store probe |
| `LINKSKILLS_STATE_DIR` | optional | Durable state directory |
| `LINKSKILLS_STORE_PROBE` | optional | `1` force store reachability probe on `/ready` |
| `LINKSKILLS_STORE_URL` | optional | Store DSN or placeholder; prefer SecretRef companion |
| `LINKSKILLS_DATABASE_URL` | optional | Alias for store probe configuration |
| `LINKSKILLS_POSTGRES_URL` | optional | Alias for store probe configuration |

### PACI / Platform auth (placeholders)

| Name | Required | Notes |
|---|---|---|
| `LINKSKILLS_PACI_ISSUER` | when PACI live | Issuer URL (no secrets) |
| `LINKSKILLS_PACI_AUDIENCE` | when PACI live | Expected audience; default `lskills-api` |
| `LINKSKILLS_PACI_JWKS_URL` | when PACI live | JWKS URL |
| `LINKSKILLS_PACI_INTROSPECTION_URL` | when PACI live | Introspection URL for high-risk writes |
| `LINKSKILLS_PACI_REQUIRED_SERVICE` | optional | Default `lskills` |
| `LINKSKILLS_PACI_CLIENT_ID` | client canary | Public client id |
| `LINKSKILLS_PACI_TOKEN_URL` | client canary | Token endpoint |
| `LINKSKILLS_PACI_CLIENT_ASSERTION_KEY_SECRET_NAME` | SecretRef | GSM name for private_key_jwt material |
| `LINKSKILLS_CANARY` | optional | `1` for canary MCP identity path |
| `LINKSKILLS_CANARY_AUTHORIZATION_SECRET_NAME` | SecretRef | GSM name for canary bearer |
| `GATEWAY_TOKEN_SECRET_NAME` | SecretRef | Legacy alias name only |

### Shared platform data (ops)

| Name | Notes |
|---|---|
| `LINKTREND_PLATFORM_STAGE_SUPABASE_URL` | Non-secret URL |
| `LINKTREND_PLATFORM_STAGE_SUPABASE_SECRET_KEY_SECRET_NAME` | GSM SecretRef name |
| `LINKTREND_PLATFORM_PROD_SUPABASE_URL` | Non-secret URL |
| `LINKTREND_PLATFORM_PROD_SUPABASE_SECRET_KEY_SECRET_NAME` | GSM SecretRef name |
| `GCP_PROJECT_ID` / `GOOGLE_CLOUD_PROJECT` | For GSM render |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to host SA JSON (host-managed) |

## Install contract

```bash
pip install -e packages/core
pip install -e packages/gateway
pip install -e packages/mcp_server
# consumers:
pip install -e packages/client
# librarian domain (Platform host imports worker):
pip install -e packages/librarian_domain
```

See [`docs/runbooks/PRODUCTION_OPERATIONS.md`](../runbooks/PRODUCTION_OPERATIONS.md).

## Out of scope for Platform from this definition

- Creating paid cloud resources
- Applying live Supabase migrations (Platform migration control owns apply)
- Issuing PACI signing keys (Platform auth owns keys)
- Reviving Logic Engine or merging Brain+Skills
