# FROZEN CONSUMER PIN — platform.auth-claims/1.0.0 (LiNKskills)

| Field | Value |
|---|---|
| Contract | `platform.auth-claims/1.0.0` |
| Platform package | `@linktrend/platform-contracts` `0.2.1` |
| Consumer | LiNKskills Gateway / MCP |
| Pin date | `2026-07-28` |
| Status | `historical_rejection_only` (superseded by `platform.auth-claims/1.1.0` / `@linktrend/platform-contracts@0.2.2`) |

## Exact hashes (must match Platform freeze)

| Kind | SHA-256 |
|---|---|
| Schema file bytes | `b0397cdf34e76ab0986c6d223ecb6c3c66d619ea59557f78cd45c0c015ff50fb` |
| Canonical contentHash | `6bf49618d846662976886f57d5d468f73a08ab1a6574968f68833d82429db251` |

## Vendored artifacts in this repo

| Artifact | Path |
|---|---|
| JSON Schema | `packages/contracts/schemas/platform-auth-claims.v1.0.0.json` |
| Fixtures | `packages/contracts/fixtures/platform-claims/` |
| Production verifier | `packages/gateway/linkskills_gateway/auth.py` (`PlatformClaimsVerifier`) |
| Local-test unsigned decoder | `packages/gateway/linkskills_gateway/auth.py` (`LocalUnsignedClaimsVerifier`) |
| Test-only mint helpers | `packages/gateway/linkskills_gateway/auth_testing.py` |

## Consumer rules

- Require `claimContractVersion === "platform.auth-claims/1.0.0"`.
- CamelCase only; `additionalProperties` rejected.
- `actorKind` enum only: `human` \| `persona` \| `service` \| `adapter` \| `program_executor`.
- Reject `actorKind: "agent"`, snake_case aliases, unknown fields, and `fake.*` tokens.
- **Authenticity (wave 4):** production `PlatformClaimsVerifier` requires an injected Platform-approved cryptographic authenticator (`LINKSKILLS_PLATFORM_AUTHENTICATOR=module:attr`). Unsigned `platform.<base64url(JSON)>` is rejected outside `LINKSKILLS_AUTH_MODE=local-test`.
- Gateway/MCP startup fails closed when production authenticator/config is unavailable — no fallback to the unsigned decoder.
- `LINKSKILLS_CANARY` cannot use local-test/unsigned auth.
- `mint_platform_token` is test-only (`auth_testing`); not a package-root export.
- Expired/revoked/rotated credential proofs use injected evaluation clock and credential status; claim-field names remain frozen.

Authority: LiNKplatform `docs/contracts/frozen/platform-auth-claims-v1.0.0.FROZEN.md`.
