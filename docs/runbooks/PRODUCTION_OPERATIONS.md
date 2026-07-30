# LiNKskills production operations — Gateway + MCP (post–Logic Engine)

Owner: LiNKtrend Platform (hosting) + LiNKskills (domain packages / runbooks)
Last updated: 2026-07-30

## Posture (current)

LiNKskills steady-state delivery is a **long-lived Gateway** (stdlib HTTP JSON
`skills_*` API) plus an **MCP adapter** over the same in-process service.
Git checkout loading via `lib/skill_runtime` remains a **migration bridge**,
not the final sole load path.

| Component | Where it lives | Notes |
|---|---|---|
| Gateway (`linkskills-gateway`) | Host / VPS process | Stdlib `ThreadingHTTPServer`; default port `8787` |
| MCP (`linkskills-mcp`) | Stdio MCP process (or host-wired) | Same `SkillsGatewayService`; no duplicated business logic |
| Skill catalog + packages | Git checkout pinned SHA/tag | Catalog index + `packages/*` |
| `lskills.*` tables | Shared Supabase (Platform-owned live apply) | Catalog, telemetry, eval runs |
| Librarian domain worker | `packages/librarian_domain` | Hosted by LiNKplatform generic runner |
| Local telemetry buffer | Host file / client buffer | Flush when Gateway / DB reachable |

### Retired — do not start

- Logic Engine FastAPI stack under `archive/logic-engine-2026-07-14/` (ADR 0001)
- `deploy/production/docker-compose.yml` — **retired stub** (`services: {}`)
- Any combined Brain+Skills service — **forbidden** (Brain remains separate)

## Package install (editable)

Stdlib Gateway — no ASGI framework required.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip setuptools wheel

pip install -e packages/core
pip install -e packages/gateway
pip install -e packages/mcp_server
pip install -e packages/client
pip install -e packages/librarian_domain

# Optional umbrella meta-package (after the path packages above resolve):
# pip install -e .
```

Legacy `PYTHONPATH=packages/...:.` still works for tests without install.

Entry points after install:

```bash
linkskills-gateway --host 127.0.0.1 --port 8787
linkskills-mcp   # stdio JSON-RPC
```

Platform-consumable env/ports/health contract:
[`docs/deploy/GATEWAY-MCP-SERVICE-DEFINITION.md`](../deploy/GATEWAY-MCP-SERVICE-DEFINITION.md).

## Host bootstrap

1. Clone `linktrend/LiNKskills` and check out a pinned tag/SHA.
2. Install Python 3.11+ and the editable packages above.
3. Copy `deploy/vps/.env.example` → `deploy/vps/.env`. Fill **names only**
   (no secret values in git). Prefer GSM SecretRef *names* rendered to local
   file paths for `LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE`.
4. Render runtime secrets when GSM is available:

```bash
./deploy/vps/render-env-from-gsm.sh
set -a && source deploy/vps/.env.runtime && set +a
```

5. Validate catalog + packages:

```bash
python3 validator.py --repo-root . --scan-all
python3 scripts/build-catalog-index.py --check
PYTHONPATH="packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:." \
  python3 -m pytest -q
```

6. Start Gateway (production auth fails closed without authenticator env):

```bash
export LINKSKILLS_AUTH_MODE=production
export LINKSKILLS_PLATFORM_AUTHENTICATOR='platform.approved.module:Factory'
linkskills-gateway --host 0.0.0.0 --port 8787
```

MCP (stdio) is started by the consumer host (Cursor / OpenClaw / Platform),
not by the retired compose file.

## SecretRef templates (names only)

Never commit secret values. `.env` holds placeholders and `*_SECRET_NAME`
keys; `render-env-from-gsm.sh` writes `.env.runtime` (mode `600`, gitignored).
Private key material reaches the PACI client only as a **file path** via
`LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE` (never CLI args, never logs).

| Concern | Env / SecretRef name pattern | Notes |
|---|---|---|
| Platform authenticator module | `LINKSKILLS_PLATFORM_AUTHENTICATOR` | `module.path:attr` — not a secret |
| PACI issuer | `LINKSKILLS_PACI_ISSUER` | Public URL |
| PACI JWKS | `LINKSKILLS_PACI_JWKS_URI` | Same origin as issuer |
| PACI audience | `LINKSKILLS_PACI_AUDIENCE` | Default `lskills-api` |
| Required service scopes | `LINKSKILLS_PACI_REQUIRED_SERVICE_SCOPES` | CSV; default `lskills` |
| Introspection | `LINKSKILLS_PACI_INTROSPECTION_URL` / `LINKSKILLS_PACI_INTROSPECTION_CLIENT_ID` | High-risk writes |
| Token mint | `LINKSKILLS_PACI_TOKEN_ENDPOINT` / `LINKSKILLS_PACI_CLIENT_ID` | Client credentials |
| Client private key file | `LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE` | Absolute SecretRef path to ES256 PEM |
| Client assertion kid | `LINKSKILLS_PACI_CLIENT_KID` | Optional JOSE `kid` |
| Mint scope / resource audience | `LINKSKILLS_PACI_SCOPE` / `LINKSKILLS_PACI_RESOURCE_AUDIENCE` | Optional Skills-pinned |
| Auth mode | `LINKSKILLS_AUTH_MODE` | `production` or `local-test` |
| Canary bearer | `LINKSKILLS_CANARY_AUTHORIZATION_SECRET_NAME` | Optional; local-test legacy |
| Supabase (ops flush / librarian) | `LINKTREND_PLATFORM_*_SUPABASE_*_SECRET_NAME` | Existing VPS pattern |
| Eval receipt issuer | `LINKSKILLS_EVAL_RUNNER_ISSUER_KEY_SECRET_NAME` | Sealing key via GSM |

Ready probes check authenticator **env presence** in production; they do
**not** load GSM secrets or import the authenticator module.

## Health, ready, metrics, drain, signals

| Path | Meaning | Success |
|---|---|---|
| `GET /health` | Process up (liveness) | `200` |
| `GET /ready` | Catalog loaded + auth mode configured (+ optional store probe) | `200` / `503` |
| `GET /metrics` | Prometheus text counters (requests / auth_fail / ready / drain) | `200` |
| `GET /drain` | Drain flag + in-flight count | `200` |
| `POST /drain` | Enable graceful drain (reject new `/v1/*`, finish in-flight) | `200` |
| `POST /drain/cancel` | Clear drain flag | `200` |

Also: `LINKSKILLS_DRAIN=1` starts the process already draining.

**Process signals:** `SIGTERM` / `SIGINT` enable drain, wait up to
`LINKSKILLS_SHUTDOWN_TIMEOUT_S` (default `30`) for in-flight work to finish,
persist/close the durable store when present, then exit `0` (clean) or `1`
(timeout with remaining work — honest incomplete exit). Supervisors should
prefer `SIGTERM` over `SIGKILL` so drain can complete.

Do **not** expose `/drain` on a public ingress without host network policy.
`/health` must not be treated as studio stage/prod readiness evidence.

Optional store probe when any of:

- `LINKSKILLS_STORE_PROBE=1`
- `LINKSKILLS_GATEWAY_DURABLE=1`
- `LINKSKILLS_STORE_URL` / `LINKSKILLS_DATABASE_URL` / `LINKSKILLS_POSTGRES_URL` set

## Degraded modes (honest)

| Mode | Behavior | Operator action |
|---|---|---|
| Auth misconfigured (prod) | Process may fail closed at start; `/ready` → `503` if running under test harness with env stripped | Fix `LINKSKILLS_PLATFORM_AUTHENTICATOR` / PACI wiring via Platform |
| Catalog empty / missing index | `/ready` → `503` (`catalog_loaded=false`) | Restore checkout + rebuild `catalog/index.json` |
| Store unreachable (probe on) | `/ready` → `503` (`store_reachable=false`) | Repair durable store / DSN; in-memory mode skips probe |
| Draining | New `/v1/*` → `503` `draining`; health/metrics stay up | Finish cutover; `POST /drain/cancel` or restart without `LINKSKILLS_DRAIN` |
| Shutdown timeout | Exit code `1`; remaining in-flight not guaranteed finished | Investigate stuck work; restart; do not claim clean drain |
| Downstream DB / PostgREST unavailable | Gateway may still serve catalog reads from local index; telemetry flush / librarian writes buffer or fail closed per adapter | Platform restores shared DB; flush buffers |
| MCP host down | HTTP Gateway can continue independently | Restart MCP under consumer host |

No silent fallback to unsigned Platform claims outside
`LINKSKILLS_AUTH_MODE=local-test`.

## Rollback

1. **Drain**: `POST /drain` (or set `LINKSKILLS_DRAIN=1` and restart), or send `SIGTERM` and let bounded shutdown run.
2. Wait for `/drain` → `in_flight: 0` (and no new consumer traffic), or confirm clean exit code `0`.
3. Stop Gateway/MCP processes (host supervisor / systemd — Platform-owned units).
4. Check out previous known-good tag/SHA.
5. Re-install editable packages at that SHA if needed.
6. Restore prior `.env.runtime` SecretRefs (do not invent new secrets).
7. Start Gateway; confirm `GET /health` = 200 and `GET /ready` = 200.
8. Clear drain if set; re-attach MCP consumers to the pinned SHA.
9. If a Skills SQL migration was applied by Platform and must reverse:
   **Platform alone** runs the rollback migration — LiNKskills does not apply
   live DDL from this runbook.

Do not revive Logic Engine compose or archived control-plane images as a
rollback path.

## Librarian (skills half)

Deploy and schedule from **LiNKplatform**, not this repo:

- Package: `LiNKplatform/packages/librarian-runner`
- Domain worker: `packages/librarian_domain` in this repo
- Set `LINKSKILLS_REPO_PATH` to this checkout
- Prefer dry-run for the first supervised pass

## Compatibility checkout path

During migration, consumer Programs may still point
`LINKSKILLS_REPO_PATH` / `repo_root=` at this checkout for
`lib.skill_runtime`. Prefer Gateway/`skills_*` for new work. See
[`LINKSKILLS-TECHNICAL-PRD.md`](../LINKSKILLS-TECHNICAL-PRD.md).

## Optional: scheduled telemetry flush

```bash
*/15 * * * * cd /opt/LiNKskills && set -a && . deploy/vps/.env.runtime && set +a && python3 scripts/flush-telemetry.py >> /var/log/linkskills-telemetry.flush.log 2>&1
```
