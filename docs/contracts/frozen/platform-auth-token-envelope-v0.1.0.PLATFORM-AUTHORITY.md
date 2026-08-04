# FROZEN: platform.auth-token-envelope/0.1.0

| Field | Value |
|---|---|
| Contract ID | `platform.auth-token-envelope` |
| Semantic version | `0.1.0` |
| Contract version string | `platform.auth-token-envelope/0.1.0` |
| Schema version | `2026.07.30-f1` |
| Package | `@linktrend/platform-contracts` `0.3.0` |
| Freeze date | `2026-07-30` |
| Status | `frozen_for_integration` |
| Depends on | `platform.auth-claims/1.1.0` (**unchanged**) |
| Authority | ADR 0013 Accepted; Principal D1–D15 locked |
| OpenClaw pins | HEAD `bf10d35847c20c5077335070e3599fe91a81a0de`; handoff SHA-256 `c950ef577b7543f0632e2a6d0386ae8a3209d002527320e04c03c3b666c2b549` |

## Freeze notes

- RFC 8414: issuer **no trailing slash**; discovery = `issuer + "/.well-known/oauth-authorization-server"`.
- AuthClaims `correlationId` = mint correlation only; per-request `X-Request-Id` independent.
- Access-token multi-use; client-assertion `jti` replay reject.
- Omit `authorization_endpoint` (not null); `response_types_supported: []`.
- Crypto: consumers/issuer use **`jose` (panva)** — no custom crypto; **Lane 2 adds the dependency** (not this package).
- D12 authorizes full local/fake now; stage/prod gated.

## Artifacts

| Artifact | Path |
|---|---|
| JSON Schema | `packages/contracts/schemas/platform-auth-token-envelope.v0.1.0.json` |
| Package export | `@linktrend/platform-contracts/schemas/platform-auth-token-envelope.v0.1.0.json` |
| TypeScript | `packages/contracts/src/auth-token-envelope.ts` |
| Semantics doc | `docs/contracts/platform-auth-token-envelope-v0.1.md` |
| Fixtures | `packages/contracts/fixtures/auth-token-envelope/` |
| AuthClaims (unchanged) | `packages/contracts/schemas/platform-auth-claims.v1.1.0.json` |

## Hashes (SHA-256 hex)

### Schema

| Kind | SHA-256 |
|---|---|
| Schema file bytes | `7173b9f9bca59ce8a0e3e3dc2b78b680dd07fdd2451215e3ecd97ff3dd463eed` |
| Canonical content hash (`contentHash` / canonicalizeJson + sha256) | `9335b1855c3b3a5ec01b40c18ea85a98826192cbfba3110e07399d896e890a12` |

### TypeScript

| Kind | SHA-256 |
|---|---|
| `packages/contracts/src/auth-token-envelope.ts` file bytes | `a87501a95f6f37dbd67ac98f29994558a1f0f65a12adb20d32626a604289f4f7` |

### Fixtures (`packages/contracts/fixtures/auth-token-envelope/`)

| File | SHA-256 |
|---|---|
| `accept-valid.json` | `0ce305bdcddf455a0cca03c24f8608af316fb47f2bef6e3b45028ddaa5f776bb` |
| `accept-token-reuse-correlation.json` | `4ce3ccfc4a0873292720ff8e0f99078ee714b9be136a833fe0d45a2f37ff70aa` |
| `metadata-discovery-valid.json` | `5e24e2b66f0189f500de3595811dbe2536149b5eb258db84a266e7ce53ecb140` |
| `reject-cross-field-iss.json` | `6479213a3ff075f2b861974a3ea9a6aa60b3c3ab35fc9f84b03087568da9c13e` |
| `reject-extra-payload-field.json` | `3b217d50991d67b889d2fb0ed16e3340910f9057d6e22821a19d4f368f134b4d` |
| `reject-issuer-trailing-slash.json` | `b20223c48f6ddc2bc1cf7040ad4aece7e683d63baaaf70925f91f7f6ee588577` |
| `reject-nbf-not-iat.json` | `4a2c0536d401ed2baf1bd68e50393764de5bcdd0ecdfc40cba5271e36193f6e1` |

## Integration notes

- Consumers import schema via package export path above or `AuthTokenEnvelopePayload` / `assertAuthTokenEnvelopePayloadShape` from `@linktrend/platform-contracts`.
- Nested AuthClaims must remain `platform.auth-claims/1.1.0`.
- Do not mutate the schema file or fixtures without bumping the envelope contract semver and re-freezing.
- Signing/verification belongs in issuer/verifier runtimes with `jose`, not in this contracts package.

## Skills consumer pin (LiNKskills)

Skills consumes this freeze at certified Platform candidate HEAD
`421a35e97bc302be0f5e1f196d0a5e8d132f6fd8` (envelope `0.1.0` / package `0.3.0`;
schema/content hashes unchanged). See
`docs/contracts/frozen/platform-auth-token-envelope-v0.1.0.CONSUMER-PIN.md`.
Candidate is **not** live PACI/hosting/migration authority; stage/prod remain unproven.
