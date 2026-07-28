# FROZEN CONSUMER PIN — platform.auth-claims/1.0.0 (LiNKskills)

| Field | Value |
|---|---|
| Contract | `platform.auth-claims/1.0.0` |
| Platform package | `@linktrend/platform-contracts` `0.2.1` |
| Consumer | LiNKskills Gateway / MCP |
| Pin date | `2026-07-28` |
| Status | `consumed_for_integration` |

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
| Verifier | `packages/gateway/linkskills_gateway/auth.py` (`PlatformClaimsVerifier`) |

## Consumer rules

- Require `claimContractVersion === "platform.auth-claims/1.0.0"`.
- CamelCase only; `additionalProperties` rejected.
- `actorKind` enum only: `human` \| `persona` \| `service` \| `adapter` \| `program_executor`.
- Reject `actorKind: "agent"`, snake_case aliases, unknown fields, and `fake.*` tokens on non-test paths.
- Expired-fixture proofs use an injected evaluation clock (`now=` / `now_fn`), never permanently valid credentials.

Authority: LiNKplatform `docs/contracts/frozen/platform-auth-claims-v1.0.0.FROZEN.md`.
