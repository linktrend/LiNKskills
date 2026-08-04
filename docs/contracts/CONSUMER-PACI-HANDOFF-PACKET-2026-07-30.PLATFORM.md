# Consumer PACI handoff packet — 2026-07-30

**Status:** Sanitized Platform → consumer owner handoff (Brain, Skills, OpenClaw). **Not** Codex certification. **Not** live PACI enable.
**Timezone:** Asia/Taipei (CST, UTC+8)
**Platform branch:** `issue/LP-01-linkplatformdevelopmentplan01`
**Platform tip (implementation packet):** `d7524f1c4b4b5b0df39ea41309f49cd2bb759f2d`
**Authority:** Principal D1–D15 production lock; ADR 0013 Accepted (Phase-1 bounds); frozen envelope + local/fake PACI
**Does not edit:** LiNKbrain, LiNKskills, openclaw_prime, or any sibling repository

---

## What Platform published (local/fake — stage/prod NOT live)

| Item | Value |
|---|---|
| Contracts package | `@linktrend/platform-contracts@0.3.0` |
| Auth token envelope (frozen) | `platform.auth-token-envelope/0.1.0` |
| AuthClaims (unchanged) | `platform.auth-claims/1.1.0` |
| PACI package | `@linktrend/platform-paci@0.1.0` — local/fake authorization server + TypeScript verifier helpers |
| Persistence migration | `supabase/migrations/20260730_000009_platform_paci_registry.sql` (**not** live-applied) |
| Librarian host | PACI env slots wired; **all PACI/domain flags default disabled** |
| Stage / prod PACI | **`paci_enabled: false`** / not enabled — consumers **must not** assume live PACI |

Freeze record: `docs/contracts/frozen/platform-auth-token-envelope-v0.1.0.FROZEN.md`
Semantics: `docs/contracts/platform-auth-token-envelope-v0.1.md`
Local/fake AS: `packages/paci/`

---

## Decision locks consumers must honor

### D14 — OpenClaw owner seam (authorized; Platform will not edit OpenClaw)

Principal **authorizes the OpenClaw owner** to implement a **generic** `client_credentials` + `private_key_jwt` machine-token seam against Platform PACI contracts.

- Platform **will not** edit `openclaw_prime` for this seam.
- Platform supplies frozen envelope + local/fake AS + verifier helpers only.
- OpenClaw remains owner of product/runtime wiring inside OpenClaw.

### D15 — Shared-secret client auth **forbid**

| Rule | Value |
|---|---|
| `client_secret_*` / shared-secret client auth | **`forbid`** in every environment |
| Phase-1 client auth method | `private_key_jwt` only |
| Exception | Requires a **separately recorded** Principal decision (none granted) |

Do not advertise, provision, or fall back to shared-secret client authentication.

### Issuer URIs (D8 / D9) — locked strings; not live

| Env | Issuer URI (**no trailing slash**) | Live status |
|---|---|---|
| Stage (D8) | `https://auth.stage.linkplatform.linktrend.dev` | DNS/control **not** proven; stage PACI **not** enabled |
| Prod (D9) | `https://auth.linkplatform.linktrend.dev` | DNS/control **not** proven; prod PACI **forbidden** until verified stage |

RFC 8414 discovery = `issuer + "/.well-known/oauth-authorization-server"` (no `//.well-known` from a trailing slash on issuer).

### Mint `correlationId` vs per-request `X-Request-Id`

| Field | Scope | Rule |
|---|---|---|
| AuthClaims `correlationId` | **Token mint / issuance** | Assigned **once** at mint; stable for that access token’s lifetime; issuance audit only |
| `X-Request-Id` (Phase-1 proposed) | **Single HTTP/MCP request** | Independent per request; required (or freshly generated) on token reuse |

**Must not:** treat mint `correlationId` as Gateway request correlation; copy token `correlationId` into the request-correlation slot; overwrite a caller-supplied request id with the mint value.

---

## Exact OpenClaw evidence pins (authoritative for PACI capability)

| Pin | Value |
|---|---|
| OpenClaw HEAD | `bf10d35847c20c5077335070e3599fe91a81a0de` |
| Handoff path (OpenClaw) | `docs/execution/openclawdevelopmentplan01/PLATFORM-PACI-OPENCLAW-COMPATIBILITY-HANDOFF-2026-07-30.md` |
| Handoff SHA-256 | `c950ef577b7543f0632e2a6d0386ae8a3209d002527320e04c03c3b666c2b549` |

These pins supersede older OpenClaw reconcile HEADs for **PACI compatibility evidence**. They do not mean OpenClaw has already implemented the D14 seam.

---

## Brain / Skills claim-shape heads (from existing reconcile manifest)

AuthClaims **shape** reconcile remains against frozen `platform.auth-claims/1.1.0`. Reviewed heads from `docs/contracts/CONSUMER-RECONCILE-MANIFEST-auth-claims-1.1.0.json` (reviewed 2026-07-30):

| Consumer | Reviewed HEAD | Notes |
|---|---|---|
| Brain | `cfa8e931952fb12326ae53f43e73f77b9b0b09ea` | Claim-shape head; PACI crypto consumption not assumed live |
| Skills | `af1177a6428e3128b5360da5b92aecd670502589` | Claim-shape head; historical contracts pin `0.2.2` for AuthClaims only — envelope/`0.3.0` is a **new** consumer action when adopting PACI |
| OpenClaw (AuthClaims reconcile row) | `86cb29a645043416494294317128313183757b3f` | Historical AuthClaims fixture countersign — **PACI evidence** uses OpenClaw pins in the table above, not this row |

Consumers adopting PACI locally should plan to consume:

1. `@linktrend/platform-contracts@0.3.0` (envelope `0.1.0` + AuthClaims `1.1.0`)
2. `@linktrend/platform-paci@0.1.0` verifier helpers / local AS for fakes only
3. D15 `private_key_jwt` client posture — no shared secret

---

## Explicit non-assumptions

- Stage and production PACI are **not** enabled; DNS for D8/D9 issuers was **NXDOMAIN** at last Platform probe.
- No live token mint, GSM client-assertion key create, or stage flip is authorized by this packet.
- Platform agents do **not** edit sibling repos; D14 work is OpenClaw-owner-owned.
- This packet does **not** self-certify Codex verification or merge readiness.

## Platform pointers

- Decisions: `docs/evidence/phase-0/PRINCIPAL-DECISIONS-AUTHCLAIMS-CRYPTO.md`
- Stage gate: `docs/evidence/phase-0/PACI-STAGE-ACTIVATION-GATE-2026-07-30.md`
- Infra placeholders: `docs/infra/paci-placeholders.md`
- Seven-class ledger: `docs/evidence/phase-1/PACI-PRODUCTION-SEVEN-CLASSIFICATION-2026-07-30.md`
- AuthClaims repin (shape only): `docs/contracts/CONSUMER-REPIN-PACKET-auth-claims-1.1.0.md`
