# FROZEN CONSUMER PIN — platform.auth-token-envelope/0.1.0 (LiNKskills)

| Field | Value |
|---|---|
| Contract | `platform.auth-token-envelope/0.1.0` |
| Contract version string | `platform.auth-token-envelope/0.1.0` |
| Platform package | `@linktrend/platform-contracts` `0.3.0` |
| Platform HEAD | `421a35e97bc302be0f5e1f196d0a5e8d132f6fd8` (certified candidate; prior pin `0455846487d0b8c583859060ba8b4be70e7f0b48`) |
| Consumer | LiNKskills Gateway (Lane 1 PACI resource-server adapter) |
| Pin date | `2026-07-30` (repin `2026-08-01`) |
| Status | `consumed_for_integration` (local/fake fixtures); certified Platform candidate — **not** live PACI/hosting/migration authority; stage/prod PACI **not** live-proven |
| Depends on (unchanged) | `platform.auth-claims/1.1.0` |
| AuthClaims historical package | `0.2.2` (claim-shape only; PACI adoption uses `0.3.0`) |
| Supersedes | DRAFT adapter `platform.auth-token-envelope/0.1.3-draft` / `platform-auth-token-envelope-v0.1.CONSUMER-ADAPTER.md` |

## Exact hashes (must match Platform schema bytes)

| Kind | SHA-256 |
|---|---|
| Envelope schema file bytes | `7173b9f9bca59ce8a0e3e3dc2b78b680dd07fdd2451215e3ecd97ff3dd463eed` |
| Envelope contentHash | `9335b1855c3b3a5ec01b40c18ea85a98826192cbfba3110e07399d896e890a12` |
| AuthClaims schema file bytes | `c2e8bc68b3feb9a3dacc497f5a5d497b466c400804fb4f9e41734c10772ddfa1` |
| AuthClaims contentHash | `fb518834be897c32574df5f7235704fdb0de708bd3da1b48fc448246e3eca567` |

## Vendored artifacts in this repo

| Artifact | Path |
|---|---|
| JSON Schema | `packages/contracts/schemas/platform-auth-token-envelope.v0.1.0.json` |
| Fixtures | `packages/contracts/fixtures/auth-token-envelope/` |
| Platform freeze copy | `docs/contracts/frozen/platform-auth-token-envelope-v0.1.0.PLATFORM-AUTHORITY.md` |
| Consumer pin (this file) | `docs/contracts/frozen/platform-auth-token-envelope-v0.1.0.CONSUMER-PIN.md` |

## Modules

| Module | Role |
|---|---|
| `packages/gateway/linkskills_gateway/paci_types.py` | Frozen envelope pin, hashes, TTL=900, evidence markers |
| `packages/gateway/linkskills_gateway/jwks.py` | Same-origin / no-redirect JWKS; HTTPS required (HTTP only local-test loopback) |
| `packages/gateway/linkskills_gateway/paci_jwt.py` | Compact JWS + ES256 (`cryptography`) + unknown-field / array aud / UUID jti / TTL≤900 / zero skew |
| `packages/gateway/linkskills_gateway/introspection.py` | RFC 7662; exact active:true binding; SecretRef `private_key_jwt`; stub only behind local-test gate |
| `packages/gateway/linkskills_gateway/paci_authenticator.py` | `PaciJwtAuthenticator` + environ factory (fail-closed signer absence) |
| `tests/gateway/paci_fakes.py` | Ephemeral ES256 keys + in-memory JWKS/introspection fakes |
| `tests/gateway/test_paci_adversarial.py` | Adversarial conformance (incl. 3600s TTL reject, HTTPS, binding, signer) |
| `tests/gateway/test_paci_frozen_fixtures.py` | Platform frozen fixtures + signed 900/3600 cases |

## Consumer rules (Phase-1)

- Header: `typ=paci+jwt`, `alg=ES256`; reject `none` / HS* / embedded key headers.
- Payload: `additionalProperties: false`; `aud` **must** be a JSON array; `jti` RFC 4122 UUID; `nbf === iat`; issuer no trailing slash.
- Access-token lifetime `(exp - iat) ≤ 900` seconds; reject longer (including 3600). Never trust client `expires_in` above 900.
- Cross-field equality with AuthClaims 1.1.0 at whole-second UTC boundaries; clock skew = 0.
- Introspection `active:true`: require and exactly match `iss`, `aud` (set), `sub`, `credential_id`, `runtime_binding_id`, `jti`, `iat`, `exp`, `token_type=Bearer`, and required scope/ops. Response `client_id` must be a member of the trusted **mint** client allow-list (`LINKSKILLS_PACI_TRUSTED_MINT_CLIENT_IDS`), **not** the RS introspection assertion client id. Missing field or empty mint allow-list ⇒ deny.
- Outside `LINKSKILLS_AUTH_MODE=local-test`: real SecretRef file signer (`LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE`); `LocalTestClientAssertionSigner` forbidden on production/stage construction; missing `LINKSKILLS_PACI_TRUSTED_MINT_CLIENT_IDS` when introspection is configured fails closed.
- HTTPS required for issuer / JWKS / introspection (and client discovery/token) in non-test; HTTP only when local-test **and** loopback host.

## Wiring

```text
LINKSKILLS_PLATFORM_AUTHENTICATOR=linkskills_gateway.paci_authenticator:build_paci_authenticator_from_environ
LINKSKILLS_PACI_ISSUER=https://auth.stage.linkplatform.linktrend.dev
LINKSKILLS_PACI_JWKS_URI=https://auth.stage.linkplatform.linktrend.dev/.well-known/jwks.json
LINKSKILLS_PACI_AUDIENCE=lskills-api
LINKSKILLS_PACI_REQUIRED_SERVICE_SCOPES=lskills
LINKSKILLS_PACI_INTROSPECTION_URL=https://auth.stage.linkplatform.linktrend.dev/oauth/introspect
LINKSKILLS_PACI_INTROSPECTION_CLIENT_ID=<skills-rs-assertion-client-id>
LINKSKILLS_PACI_TRUSTED_MINT_CLIENT_IDS=<cursor-mint-client-id>[,...]
LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE=<SecretRef-injected PEM path>
```

Issuer values are Platform-locked strings (D8/D9); stage/prod PACI remain **not** enabled until Platform proves them.

`resolve_claims_verifier()` aligns outer AuthClaims `expected_issuer` with the
PACI authenticator's pinned issuer (`LINKSKILLS_PACI_ISSUER`) when the caller
does not pass an explicit `expected_issuer`. Non-PACI authenticators retain the
legacy default `linkplatform-issuer`. Wrong issuers still fail in PACI JWT
verification before policy.

Crypto backend: **`cryptography` 46.x** (ES256). Skills avoids adding PyJWT/jose unless a later Platform helper requires it.

## Explicit non-claims

- Not live-proven against a stage/prod PACI issuer, JWKS, or introspection endpoint.
- Does not mint production access tokens or hold Platform signing private keys in-repo.
- `LocalTestClientAssertionSigner` is local-test DI wiring only.

Authority: Platform freeze
`docs/contracts/frozen/platform-auth-token-envelope-v0.1.0.PLATFORM-AUTHORITY.md`
(and Platform `docs/contracts/frozen/platform-auth-token-envelope-v0.1.0.FROZEN.md`).
Skills does not edit Platform.
