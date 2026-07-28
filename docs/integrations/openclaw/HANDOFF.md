# OpenClaw Handoff — Skills MCP Contract Fragment

- **Status:** Contract / conformance ready for OpenClaw repin + countersign
- **Date:** 2026-07-28 (wave 2 update)
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
| Contract | `platform.auth-claims/1.0.0` |
| Package | `@linktrend/platform-contracts@0.2.1` |
| Schema bytes SHA-256 | `b0397cdf34e76ab0986c6d223ecb6c3c66d619ea59557f78cd45c0c015ff50fb` |
| contentHash | `6bf49618d846662976886f57d5d468f73a08ab1a6574968f68833d82429db251` |

LiNKskills consumer pin: `docs/contracts/frozen/platform-auth-claims-v1.0.0.CONSUMER-PIN.md`  
Vendored fixtures: `packages/contracts/fixtures/platform-claims/`  
Verifier: `packages/gateway/linkskills_gateway/auth.py`
- Production: `PlatformClaimsVerifier` + Platform-approved cryptographic authenticator (`LINKSKILLS_PLATFORM_AUTHENTICATOR`)
- Local-test only: `LocalUnsignedClaimsVerifier` (`LINKSKILLS_AUTH_MODE=local-test`)
- Canary must not use unsigned/local-test mode

Rules OpenClaw must mirror when presenting tokens to Skills:

- exact `claimContractVersion`
- camelCase only; no snake_case / unknown fields / `fake.*`
- `actorKind` ∈ {`human`,`persona`,`service`,`adapter`,`program_executor`} — **not** `agent`
- audience includes `lskills-api`; serviceScopes includes `lskills` for Skills calls

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

1. Repin OpenClaw/Lisa Skills integration to `platform.auth-claims/1.0.0` hashes above.
2. Countersign consumer conformance (or file defects back to LiNKskills).
3. Wire host-side MCP only under OpenClaw ownership.
4. Do not ask LiNKskills agents to edit OpenClaw/Lisa internals.

Correction evidence: `docs/handoffs/2026-07-28-grok-certification-correction-wave2.md`, `docs/handoffs/2026-07-28-grok-certification-correction-wave4.md`.
