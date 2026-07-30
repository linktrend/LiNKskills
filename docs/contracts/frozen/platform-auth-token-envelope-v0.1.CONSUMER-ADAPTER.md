# CONSUMER ADAPTER — platform.auth-token-envelope/0.1.3-draft (LiNKskills)

| Field | Value |
|---|---|
| Contract | `platform.auth-token-envelope/0.1.3-draft` |
| Status | **DRAFT pin — not frozen — not live-proven** |
| Consumer | LiNKskills Gateway (Lane 1 PACI resource-server adapter) |
| Depends on (frozen) | `platform.auth-claims/1.1.0` / package `0.2.2` |
| AuthClaims schema bytes SHA-256 | `c2e8bc68b3feb9a3dacc497f5a5d497b466c400804fb4f9e41734c10772ddfa1` |
| AuthClaims contentHash | `fb518834be897c32574df5f7235704fdb0de708bd3da1b48fc448246e3eca567` |
| Evidence class | `fake_local` unit proofs only |
| Evidence status | **implemented but not proven against frozen Platform PACI service** |

## What this is

A Skills-owned narrow consumer adapter that verifies Platform PACI compact JWS
access tokens (`typ=paci+jwt`, `alg=ES256`) carrying namespaced AuthClaims at
`https://linktrend.dev/claims/auth`, with same-origin JWKS lookup and RFC 7662
introspection for high-risk Skills writes.

This is **not** a competing security contract. It tracks the Platform DRAFT
envelope at LiNKplatform
`docs/contracts/platform-auth-token-envelope-v0.1.DRAFT.md` (semantic version
`0.1.3-draft`). Until Platform freezes and publishes a live PACI service,
Skills treats this adapter as **implementable against the draft + fakes only**.

## Modules

| Module | Role |
|---|---|
| `packages/gateway/linkskills_gateway/paci_types.py` | Envelope constants, draft pin, evidence markers |
| `packages/gateway/linkskills_gateway/jwks.py` | Same-origin / no-redirect JWKS client, ≤5min cache, kid collision reject, purge |
| `packages/gateway/linkskills_gateway/paci_jwt.py` | Compact JWS parse + ES256 verify (`cryptography`) + registered claims + AuthClaims cross-field equality (zero skew) |
| `packages/gateway/linkskills_gateway/introspection.py` | RFC 7662 client, ≤30s jti cache, private_key_jwt signer Protocol + stub |
| `packages/gateway/linkskills_gateway/paci_authenticator.py` | `PaciJwtAuthenticator` implementing `PlatformTokenAuthenticator` |
| `packages/gateway/linkskills_gateway/auth.py` | Additive `HIGH_RISK_WRITE_OPERATIONS`; existing env loader unchanged |
| `tests/gateway/paci_fakes.py` | Ephemeral ES256 keys + in-memory JWKS/introspection fakes |
| `tests/gateway/test_paci_adversarial.py` | Adversarial conformance (unsigned, alg confusion, iss/aud/sub, kid, clock, JWKS outage, introspection fail-closed) |

## Wiring

```text
LINKSKILLS_PLATFORM_AUTHENTICATOR=linkskills_gateway.paci_authenticator:build_paci_authenticator_from_environ
LINKSKILLS_PACI_ISSUER=https://auth.stage.linkplatform.linktrend.dev
LINKSKILLS_PACI_JWKS_URI=https://auth.stage.linkplatform.linktrend.dev/.well-known/jwks.json
LINKSKILLS_PACI_AUDIENCE=lskills-api
LINKSKILLS_PACI_REQUIRED_SERVICE_SCOPES=lskills
LINKSKILLS_PACI_INTROSPECTION_URL=https://auth.stage.linkplatform.linktrend.dev/oauth/introspect
LINKSKILLS_PACI_INTROSPECTION_CLIENT_ID=<skills-introspection-client-id>
```

Issuer values above are **placeholders** from the Platform draft (Principal D8/D9
pending). Do not treat them as live endpoints.

Crypto backend: **`cryptography` 46.x** (ES256). Skills deliberately avoids
adding PyJWT/jose unless a later Platform-published helper requires it.

## High-risk writes (introspection required)

Matches Skills Gateway mutating writes (`WRITE_OPERATIONS`):

- `skills_run_start`
- `skills_run_update`
- `skills_run_complete`
- `skills_run_fail`
- `skills_tool_invoke`
- `skills_feedback_submit`
- `skills_trace_candidate_submit`

Call `PaciJwtAuthenticator.authenticate_for_operation(token, operation=...)`.
Plain `authenticate(token)` verifies JWT/AuthClaims only (reads / non-high-risk).

## Explicit non-claims

- Not frozen.
- Not proven against a live stage/prod PACI issuer, JWKS, or introspection endpoint.
- Not a substitute for Platform ADR 0013 acceptance.
- Does not mint production access tokens or hold Platform signing private keys.
- `StubClientAssertionSigner` is interface wiring only — production must inject a
  real `private_key_jwt` signer via secret injection.

## Delta packet — what Platform must still freeze / publish

Skills cannot close live PACI proof until Platform delivers **all** of:

1. **Freeze** `platform.auth-token-envelope` (drop `-draft`; Principal-accepted ADR 0013).
2. Published **JSON Schema** + content hashes for the envelope (bundling AuthClaims 1.1.0).
3. Live **stage** issuer identifier (no trailing slash / no path), discovery document
   (`/.well-known/oauth-authorization-server`), `jwks_uri`, `token_endpoint`,
   `introspection_endpoint`.
4. Skills-dedicated `client_id` / credential / runtime binding with least-privilege
   audiences (`lskills-api`) and scopes (`lskills`) — separate from Brain.
5. JWKS publication of ES256 verification keys (`kid` UUID, no collisions) + rotation
   / purge signalling contract.
6. Introspection behaviour exactly as draft §7 (401 vs 200+`active:false` vs
   200+`active:true` field set) with `private_key_jwt` client auth.
7. Optional: versioned Platform Python verifier helper Skills can pin instead of
   this draft adapter (preferred when published).
8. Environment-readiness evidence (stage health, secret injection receipts) so
   Skills can mark evidence `live_stage` instead of `fake_local`.

Until then, every Skills PACI surface must continue to carry:

> **implemented but not proven against frozen Platform PACI service**

Authority (Platform draft): `docs/contracts/platform-auth-token-envelope-v0.1.DRAFT.md`
in LiNKplatform. Skills does not edit Platform.
