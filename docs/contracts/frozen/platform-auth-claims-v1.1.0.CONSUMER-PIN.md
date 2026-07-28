# FROZEN CONSUMER PIN — platform.auth-claims/1.1.0 (LiNKskills)

| Field | Value |
|---|---|
| Contract | `platform.auth-claims/1.1.0` |
| Platform package | `@linktrend/platform-contracts` `0.2.1` (schema vendored from LiNKplatform) |
| Consumer | LiNKskills Gateway / MCP |
| Pin date | `2026-07-28` |
| Status | `consumed_for_integration` |
| Prior pin | `platform.auth-claims/1.0.0` (superseded for Skills consumers) |

## Exact hashes (must match Platform schema bytes)

| Kind | SHA-256 |
|---|---|
| Schema file bytes | `c2e8bc68b3feb9a3dacc497f5a5d497b466c400804fb4f9e41734c10772ddfa1` |
| Canonical contentHash | `fb518834be897c32574df5f7235704fdb0de708bd3da1b48fc448246e3eca567` |

## Vendored artifacts in this repo

| Artifact | Path |
|---|---|
| JSON Schema | `packages/contracts/schemas/platform-auth-claims.v1.1.0.json` |
| Fixtures | `packages/contracts/fixtures/platform-claims/` |
| Production verifier | `packages/gateway/linkskills_gateway/auth.py` (`PlatformClaimsVerifier`) |
| Local-test unsigned decoder | `packages/gateway/linkskills_gateway/auth.py` (`LocalUnsignedClaimsVerifier`) |
| Test-only mint helpers | `packages/gateway/linkskills_gateway/auth_testing.py` |

## Consumer rules

- Require `claimContractVersion === "platform.auth-claims/1.1.0"`.
- CamelCase only; `additionalProperties` rejected.
- `actorKind` enum only: `human` \| `persona` \| `service` \| `adapter` \| `program_executor`.
- `orgId` may be `null` only when `actorKind` is `service`; non-service null is rejected.
- Reject `actorKind: "agent"`, snake_case aliases, unknown fields, and `fake.*` tokens.
- Enforce exact `permittedOperations` membership for every Gateway/MCP read and mutation; empty ops fail closed.
- **Authenticity (wave 4):** production `PlatformClaimsVerifier` requires an injected Platform-approved cryptographic authenticator (`LINKSKILLS_PLATFORM_AUTHENTICATOR=module:attr`). Unsigned `platform.<base64url(JSON)>` is rejected outside `LINKSKILLS_AUTH_MODE=local-test`.
- Gateway/MCP startup fails closed when production authenticator/config is unavailable — no fallback to the unsigned decoder.
- `LINKSKILLS_CANARY` cannot use local-test/unsigned auth.
- `mint_platform_token` is test-only (`auth_testing`); not a package-root export.

Authority: LiNKplatform schema `packages/contracts/schemas/platform-auth-claims.v1.1.0.json` (consumed; Skills does not edit Platform).
