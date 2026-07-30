# LiNKskills stage readiness packet

**Status:** Skills-owned packet prepared — **stage/prod blocked** until Platform supplies independently verified environment  
**Date:** 2026-07-30 (Asia/Taipei)  
**Evidence separation:** local/fake (proven in-repo) vs stage/prod (**not run; endpoints not invented**)  
**Related:** `docs/handoffs/2026-07-30-linkskills-librarian-stage-packet.md`, `evidence/phase10/CLASSIFICATION-HONESTY.md`, `evidence/phase7/cursor-canary-status.json`

## 1. Evidence class matrix

| Class | What is allowed | Status in this packet |
|---|---|---|
| **local/fake** | Unit tests, FakeLibrarianHost, local-test AuthClaims, unsigned verifier under `LINKSKILLS_AUTH_MODE=local-test`, project-scoped Cursor fragment examples | **In-repo proofs exist** |
| **stage** | Authenticated Gateway/MCP against Platform stage PACI + applied migrations + separate Skills credentials | **BLOCKED** — no stage endpoint inventing |
| **prod** | Same bar as stage with prod issuer/JWKS/credentials | **BLOCKED** |

Do not begin multi-day canaries or claim general launch from this packet alone.

## 2. Artifact hashes (placeholders until release pin)

Fill SHA-256 at the Skills commit Platform consumes. Placeholders mark required slots — **do not invent live URLs**.

| Artifact | Path / identity | SHA-256 |
|---|---|---|
| Skills checkout pin | git commit of LiNKskills for stage | `_PLACEHOLDER_SKILLS_COMMIT_SHA256_` |
| Librarian domain worker package tree | `packages/librarian_domain/` | `_PLACEHOLDER_LIBRARIAN_DOMAIN_TREE_SHA256_` |
| Gateway package tree | `packages/gateway/` | `_PLACEHOLDER_GATEWAY_TREE_SHA256_` |
| MCP server package tree | `packages/mcp_server/` | `_PLACEHOLDER_MCP_SERVER_TREE_SHA256_` |
| Client package tree | `packages/client/` | `_PLACEHOLDER_CLIENT_TREE_SHA256_` |
| AuthClaims schema bytes | `packages/contracts/schemas/platform-auth-claims.v1.1.0.json` | `c2e8bc68b3feb9a3dacc497f5a5d497b466c400804fb4f9e41734c10772ddfa1` |
| AuthClaims contentHash | frozen consumer pin | `fb518834be897c32574df5f7235704fdb0de708bd3da1b48fc448246e3eca567` |
| Classification ledger | `evidence/phase10/skill-classification-draft.json` | recompute at pin time |
| Cursor canary fragment (example) | `configs/fragments/cursor-skills-canary.mcp.json.example` | recompute at pin time |
| Codex Skills fragment | `configs/fragments/codex-skills.config.toml.fragment` | recompute at pin time |
| OpenClaw Skills fragment | `configs/fragments/openclaw-skills.mcp.json.fragment` | recompute at pin time |

## 3. Migration manifest pin

**Authority:** LiNKplatform alone applies live.  
**Manifest:** `docs/migrations/MANIFEST-20260727-lskills-registry-v0.1.md`

| Order | File | SHA-256 (verified 2026-07-30) |
|---|---|---|
| 1 | `supabase/migrations/20260715_000002_lskills_catalog_core.sql` | `4991dd628cc501a1013a4d7c3d8f859274e62ff847e768f106b0e3c2b89d8414` |
| 2 | `supabase/migrations/20260715_000003_lskills_catalog_seed.sql` | `5e8f58a7159ad09f0c6389e12060c6a9cc76ff73dcfc2397ddea256d47a75e82` |
| 3 | `supabase/migrations/20260718_000004_lskills_postgrest_exposure.sql` | `4220d70b626313f572a38720958fb78550b3b89c0efab5366a449d33c0b22ca0` |
| 4 | `supabase/migrations/20260727_000005_lskills_registry_foundation.sql` | `36081765032f21dfd2dcca223035555e1e54b71298874235def8e0362c55c4ed` |
| 5 | `supabase/migrations/20260728_000006_lskills_rls_actor_org_scope.sql` | `12c2e45e94fd9216a5857ce53ce299a953dc2ee869f89bcdb392857133df763d` |

**Stage gate after apply (Platform evidence required):** `lskills.catalog` count ≥ 34; registry tables present with RLS; Platform foundation present.

## 4. PACI verifier / client pins

| Pin | Value | Evidence class |
|---|---|---|
| AuthClaims contract | `platform.auth-claims/1.1.0` | Frozen (consumer pin) |
| Platform contracts package | `@linktrend/platform-contracts@0.2.2` | Frozen consumer pin |
| Schema bytes SHA-256 | `c2e8bc68b3feb9a3dacc497f5a5d497b466c400804fb4f9e41734c10772ddfa1` | Frozen |
| contentHash | `fb518834be897c32574df5f7235704fdb0de708bd3da1b48fc448246e3eca567` | Frozen |
| PACI token envelope | `platform.auth-token-envelope/0.1.3-draft` | **DRAFT** adapter only |
| Envelope status | `implemented but not proven against frozen Platform PACI service` | See `paci_types.py` |
| Algorithm | ES256 (`paci+jwt`) | DRAFT envelope rules |
| Expected audience (Skills) | `lskills-api` | local/fake + intended stage |
| Service scope | `lskills` | must not reuse Brain/OpenClaw audiences |
| Local-test mode | `LINKSKILLS_AUTH_MODE=local-test` + `LocalUnsignedClaimsVerifier` | **never** stage/prod / `LINKSKILLS_CANARY` |

Consumer pin doc: `docs/contracts/frozen/platform-auth-claims-v1.1.0.CONSUMER-PIN.md`  
Envelope constants: `packages/gateway/linkskills_gateway/paci_types.py`

## 5. Endpoint / audience / credential requirements

### local/fake (Skills-owned)

- In-process Gateway/MCP tests; no public stage URL.
- Audience `lskills-api`; AuthClaims 1.1.0 shape; fake/unsigned only under explicit local-test mode.

### stage/prod (Platform-supplied — leave blank until real)

| Requirement | Stage value | Prod value |
|---|---|---|
| Skills Gateway/MCP base URL | `_PLATFORM_SUPPLIED_STAGE_ENDPOINT_` | `_PLATFORM_SUPPLIED_PROD_ENDPOINT_` |
| PACI issuer | `_PLATFORM_SUPPLIED_` | `_PLATFORM_SUPPLIED_` |
| JWKS URL | `_PLATFORM_SUPPLIED_` | `_PLATFORM_SUPPLIED_` |
| Introspection URL (high-risk writes) | `_PLATFORM_SUPPLIED_` | `_PLATFORM_SUPPLIED_` |
| Audience | `lskills-api` (exact) | `lskills-api` (exact) |
| Skills runtime credential | Platform-issued; name e.g. `svc_lskills_runtime` | separate from stage |
| Librarian credential | Platform-issued; name e.g. `svc_lskills_librarian` | separate; never actor-distributed |
| Secret injection | GSM / Platform SecretRef only | same |
| Authenticator module | `LINKSKILLS_PLATFORM_AUTHENTICATOR=module:attr` | required fail-closed |

**Do not invent** issuer URLs, JWKS hosts, or public endpoints in Skills docs.

## 6. Service definition (Skills surface)

Long-lived Skills Gateway/MCP (post–Logic Engine):

- Packages: `packages/gateway`, `packages/mcp_server`, `packages/client`
- Ops baseline: `docs/runbooks/PRODUCTION_OPERATIONS.md` (refresh as packaging lane lands)
- Librarian domain: versioned worker loaded by **Platform** generic host (ADR 0008)
- No combined Brain/Skills service; no revival of archived Logic Engine

## 7. Runbooks

| Runbook | Path | Notes |
|---|---|---|
| Host / VPS / catalog | `docs/runbooks/PRODUCTION_OPERATIONS.md` | Catalog checkout + telemetry flush; Librarian schedule is Platform |
| Cursor canary stages | `docs/integrations/cursor/CANARY.md` | Stages 1–2 local/fake only |
| Librarian packet | `docs/handoffs/2026-07-30-linkskills-librarian-stage-packet.md` | Fake-host proof + Platform handoff |
| Classification honesty | `evidence/phase10/CLASSIFICATION-HONESTY.md` | No macOS certification |

## 8. Alerts / failure / recovery (Skills expectations)

| Failure | Detection | Recovery |
|---|---|---|
| Missing production authenticator | Gateway/MCP refuse start | Supply Platform authenticator; never fall back to unsigned |
| Wrong audience / service / ops | AuthError reject | Fix credential binding; do not broaden audience |
| JWKS / introspection outage | Verifier fail-closed | Platform restore issuer; Skills remain degraded until healthy |
| Migration partial apply | Verification SQL fails | Platform forward-fix / documented down; Skills do not apply |
| Eval isolation unproven | Receipt `network_isolation != denied` | Run on Linux bwrap host; macOS cannot certify |
| Idempotency / fence conflict | Gateway reserve/replay path | Replay completed envelope; do not invent new side effects |
| Offline buffer | Local client buffer | Flush when stage reachable; prove idempotency |
| Librarian policy refuse | Domain worker response | Escalate review queue; no staging/main push |

## 9. Rollback

| Layer | Action | Owner |
|---|---|---|
| Skills service binary/package | Redeploy prior Skills SHA; disable canary flag | Platform host + Skills pin |
| PACI pin | Remain on AuthClaims 1.1.0 / package 0.2.2; do not silently re-advertise 0.2.1 | Skills consumer |
| Envelope draft | If Platform freezes a new envelope version, bump adapter intentionally | Skills + Platform |
| Migrations | Additive down only; never cascade-drop `lskills` | Platform |
| Classification | All skills stay `draft` until sealed evidence — nothing to un-promote today | Skills |
| Cursor / Codex / OpenClaw fragments | Owners revert their host apply; Skills fragment stays immutable in-repo | Fragment owners |

## 10. Evidence schema (certification)

Certifying eval evidence must include sealed executor receipts with:

- `network_isolation == "denied"`
- suite / skill_release / execution_profile / toolchain / result hashes
- issuer provenance accepted by `sealed_executor_receipt`

Non-certifying: prompt-only, suite-authored outputs, `allow_unproven`, macOS unproven isolation, synthetic unit seals.

Ledger: `evidence/phase10/skill-classification-draft.json` (`live_certification: "not performed"`, `macos_certifiable: false`, `linux_bwrap_required: true`).

## 11. Minimum scenario / run / activity counts

### Local/fake (already used for readiness planning)

| Set | Source | Minimum |
|---|---|---|
| Representative canary set | `evidence/phase1/canary-set.json` | **10** skills selected |
| Per canary skill scenarios | suite audit / canary-set | **≥ 3** scenarios each (canary-set records 3–4) |
| Librarian unit suite | `tests/librarian_domain` | **9** tests OK (2026-07-30) |

### Stage canary (blocked until Platform readiness)

Per production execution prompt — **do not start** until Platform supplies endpoint, migrations applied, PACI issuer/JWKS/introspection, separate Skills credentials, secret injection, hosting, backup/restore, audit, rollback receipts:

| Gate | Minimum |
|---|---|
| Cursor stages 3–7 | Each stage completed with dated evidence |
| Stage 8 multi-day use | **≥ 3 active operating days** **and** approved minimum run/scenario counts, whichever longer |
| Representative canary skills exercised | Full 10-skill canary set (or Principal-approved subset with rationale) |
| Sealed certifying evals | Only on Linux bwrap (or approved container/VM); macOS evidence non-certifying |
| Catalog classification for general launch | Deliberate ledger update with sealed evidence paths — not default draft |

Current Cursor status (`evidence/phase7/cursor-canary-status.json`): stages 3–8 **blocked**; stage 8 **not started**.

## 12. Residual external gates

1. Platform frozen PACI service + live JWKS/issuer (envelope still DRAFT `0.1.3-draft`).
2. Platform stage endpoint + applied `lskills` migrations + independent apply receipts.
3. Separate Skills stage credentials + GSM SecretRef injection.
4. Platform generic Librarian host loads Skills worker (Platform ADR 0008).
5. Linux certifiable isolation host for sealed receipts (no paid host without Principal approval).
6. OpenClaw/Lisa Skills prerequisite gate (owner-side).
7. Independent LiNKskills Codex verification.
8. No sibling-repo edits from Skills; fragments handed off immutable.

## 13. Local proof recorded this packet

```text
PYTHONPATH="packages/contracts:packages/core:...:packages/librarian_domain:." \
  python3 -m unittest discover -s tests/librarian_domain -v
→ Ran 9 tests — OK (2026-07-30)
```

No live stage calls. No multi-day canary start. No invented endpoints.
