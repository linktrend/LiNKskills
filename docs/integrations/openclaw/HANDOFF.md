# OpenClaw Handoff — Skills MCP Contract Fragment

- **Status:** Contract / conformance ready for OpenClaw repin + countersign
- **Date:** 2026-07-28 (wave 5 AuthClaims 1.1.0 pin)
- **Fragment:** `configs/fragments/openclaw-skills.mcp.json.fragment`

## Ownership

| Asset | Owner |
|---|---|
| Skills MCP contract fragment + Gateway auth consumer pin in LiNKskills | **LiNKskills** |
| OpenClaw/Lisa managed MCP, plugins, hooks, buffers, profiles | **OpenClaw Prime** |

## Auth claims pin (ready for OpenClaw repin)

Consume exact frozen Platform contract:

| Field | Value |
|---|---|
| Contract | `platform.auth-claims/1.1.0` |
| Package | `@linktrend/platform-contracts@0.2.2` (schema vendored from LiNKplatform) |
| Schema bytes SHA-256 | `c2e8bc68b3feb9a3dacc497f5a5d497b466c400804fb4f9e41734c10772ddfa1` |
| contentHash | `fb518834be897c32574df5f7235704fdb0de708bd3da1b48fc448246e3eca567` |

LiNKskills consumer pin: `docs/contracts/frozen/platform-auth-claims-v1.1.0.CONSUMER-PIN.md`
Vendored fixtures: `packages/contracts/fixtures/platform-claims/`
Verifier: `packages/gateway/linkskills_gateway/auth.py`
- Production: `PlatformClaimsVerifier` + Platform-approved cryptographic authenticator (`LINKSKILLS_PLATFORM_AUTHENTICATOR`)
- Local-test only: `LocalUnsignedClaimsVerifier` (`LINKSKILLS_AUTH_MODE=local-test`)
- Canary must not use unsigned/local-test mode

Rules OpenClaw must mirror when presenting tokens to Skills:

- exact `claimContractVersion` (`platform.auth-claims/1.1.0`)
- camelCase only; no snake_case / unknown fields / `fake.*`
- `actorKind` ∈ {`human`,`persona`,`service`,`adapter`,`program_executor`} — **not** `agent`
- `orgId` may be null only when `actorKind` is `service`
- audience includes `lskills-api`; serviceScopes includes `lskills` for Skills calls
- `permittedOperations` must authorize each Skills op (empty ops fail closed)

## Scope of this handoff

This repository supplies a **contract fragment** describing Skills MCP operations, auth claim requirements, and local gateway wiring. It does **not** mutate OpenClaw.

Proven here:

- Platform AuthClaims consumer against frozen schema hashes;
- gateway + MCP operation surface;
- no-secrets fragment shape.

Not proven / not performed here:

- live OpenClaw plugin install;
- OpenClaw profile or managed MCP edits;
- production credential wiring.

## Ask of OpenClaw owner

1. Repin OpenClaw/Lisa Skills integration to `platform.auth-claims/1.1.0` hashes above.
2. Countersign consumer conformance (or file defects back to LiNKskills).
3. Wire host-side MCP only under OpenClaw ownership.
4. Do not ask LiNKskills agents to edit OpenClaw/Lisa internals.

Correction evidence: `docs/handoffs/2026-07-28-grok-certification-correction-wave2.md`, `docs/handoffs/2026-07-28-grok-certification-correction-wave4.md`, `docs/handoffs/2026-07-28-grok-certification-correction-wave5.md`.
