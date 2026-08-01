# PACI / Gateway stage gate (Lane A)

**Packet:** `SKILLS-W20-STAGE-READINESS`  
**Lane:** A (PACI/Gateway stage gate)  
**Evidence class:** reference-only / local fail-closed proofs — **not** live stage/prod  
**Platform pin (read-only):** `421a35e97bc302be0f5e1f196d0a5e8d132f6fd8`  
**Rule:** certified Platform candidate ≠ live PACI authority

## Purpose

Document the **required reference-only** stage config for Gateway/MCP machine-token
readiness, and the **hard blockers** that keep stage/canary closed until Platform
supplies real issuer/JWKS/credentials/endpoints.

This doc does **not** invent live URLs, issuers, JWKS hosts, or credentials.

## Artifacts

| Artifact | Path |
|---|---|
| Schema (candidate) | `packages/contracts/schemas/stage-gateway-config-v0.1.json` |
| Stage reference config | `configs/stage/gateway-stage.reference.json` |
| Canary reference config | `configs/stage/gateway-canary.reference.json` |
| Forbidden fixture | `configs/stage/gateway-stage.local-test.forbidden.json` |
| Config tests | `tests/config/test_stage_gateway_config.py` |
| Runtime selection proofs | `tests/gateway/test_paci_stage_gate.py` |

## Stage gates

### Ready (Skills-owned, local/reference)

| Condition | Status |
|---|---|
| Stage gateway config schema exists and validates reference configs | **Ready (local)** |
| `auth_mode` fixed to `production` for stage/canary/production targets | **Ready (schema + tests)** |
| `LINKSKILLS_AUTH_MODE=local-test` rejected for stage/canary targets | **Ready (fail-closed proofs)** |
| Machine token boundary: `private_key_jwt` + SecretRef **file path only** | **Ready (schema + runtime)** |
| HTTPS required outside local-test loopback | **Ready (runtime + tests)** |
| Production/stage requires Platform authenticator (no unsigned fallback) | **Ready (documented + selection proofs)** |
| Envelope pin `platform.auth-token-envelope/0.1.0` / contracts `0.3.0` retained | **Ready (pin)** |
| Explicit non-claim: certified candidate is not live PACI authority | **Ready (schema const false)** |

### Blocked (Platform / live)

| Condition | Status |
|---|---|
| Live Platform **stage PACI issuer** | **BLOCKED — absent** |
| Live stage JWKS (same origin as issuer) | **BLOCKED — absent** |
| Live stage token endpoint + introspection | **BLOCKED — absent** |
| Separate Skills stage machine credentials + SecretRef key injection | **BLOCKED — absent** |
| Durable https Skills stage Gateway/MCP base URL | **BLOCKED — absent** |
| Live mint/verify/introspect against stage PACI | **BLOCKED — not run** |
| Cursor multi-day canary (stages 3–8) | **BLOCKED — not started** |
| Production PACI / general launch | **BLOCKED** |

## Fail-closed local-vs-stage selection

Runtime modes (see `linkskills_gateway.auth.resolve_auth_mode` and MCP proxy):

| Intent | `LINKSKILLS_AUTH_MODE` | `LINKSKILLS_ENV` | Allowed? |
|---|---|---|---|
| Local unit / loopback | `local-test` | unset / `dev` | Yes (Skills-owned) |
| Stage Gateway/MCP | `production` | `stage` \| `staging` | Required shape; live still blocked |
| Canary | `production` | `stage` \| `staging` | `LINKSKILLS_CANARY=1`; local-test **forbidden** |
| Production | `production` | `production` \| `prod` | Requires Platform authenticator |

Hard rules:

1. **`LINKSKILLS_AUTH_MODE=local-test` is never valid for stage/canary/production.**
2. Canary + local-test → refuse (`paci_stdio_proxy.build_paci_client`).
3. Canary + static bearer env → refuse.
4. Outside local-test, JWKS/issuer/token/gateway URLs must be **https** (loopback http only under local-test).
5. Outside local-test, introspection uses **SecretRef** `LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE` (`private_key_jwt`); `LocalTestClientAssertionSigner` forbidden.
6. Production/stage Gateway store is **postgres** (no silent in-memory).
7. Missing Platform-supplied issuer/JWKS/credentials → remain **hard blockers**; do not invent values.

## Machine-token / SecretRef boundary

| Item | Rule |
|---|---|
| Auth method | `private_key_jwt` only |
| Algorithm | ES256 (P-256) |
| Private key | SecretRef **file path** via `LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE` |
| Forbidden | Inline PEM in git/config/argv/logs; GSM secret *values* in repo |
| Access token TTL | ≤ 900s (frozen envelope) |
| Assertion TTL | ≤ 300s |

## HTTPS policy

Coordinated client + gateway gate:

- `LINKSKILLS_AUTH_MODE=local-test` **and** loopback host (`127.0.0.1` / `localhost` / `::1`) → http allowed.
- Any other mode → **https required** for issuer, JWKS, token endpoint, introspection, and `GATEWAY_URL`.

## Hard blockers (must clear before stage claim)

1. **Platform stage PACI issuer absent** (primary).
2. Stage JWKS / token endpoint / introspection absent.
3. Skills stage credentials + SecretRef-rendered key path absent.
4. Durable https stage Gateway URL absent.
5. Certified candidate `421a35e…` is **not** live PACI authority.

Until Platform clears these with independently verified evidence, Skills stage/canary remains **blocked**. Reference configs keep `_PLATFORM_SUPPLIED_*` placeholders only.

## Do not claim

- Stage or production PACI live-proven
- Live canary or multi-day Cursor stages 3–8
- Invented issuer / JWKS / token / introspection / Gateway URLs as real
- Secrets present in git
- Certified Platform candidate equals live PACI service

## Related runtime (read-only reuse)

- `packages/gateway/linkskills_gateway/paci_authenticator.py`
- `packages/gateway/linkskills_gateway/paci_types.py`
- `packages/gateway/linkskills_gateway/jwks.py` (`assert_https_transport`)
- `packages/client/linkskills_client/paci_token_client.py`
- `packages/mcp_server/linkskills_mcp/paci_stdio_proxy.py`
