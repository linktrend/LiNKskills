# LiNKskills — Open Issues

Append-only engineering build log for this repository. Prefer this file over stale prose elsewhere when asking “what is actually done / deferred?”

**Source of truth for product intent and design:** [`LINKSKILLS-INTENT.md`](./LINKSKILLS-INTENT.md), [`LINKSKILLS-TECHNICAL-PRD.md`](./LINKSKILLS-TECHNICAL-PRD.md), [`LINKSKILLS-OPERATIONS-MANUAL.md`](./LINKSKILLS-OPERATIONS-MANUAL.md), approved plan [`LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md`](./LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md) (SHA-256 `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`), ADRs 0001–0008.

---

## Still open / deliberately deferred

### 1. Live certification of skills to `usable` / certified profiles

**Status:** Open (operational) — certification path corrected 2026-07-28.
Filesystem catalog + eval-suite YAML exist for all 34 skills; generated `catalog/index.json` still defaults `certification_state` to `draft`. Eval Runner now requires **sealed executor receipts** from real isolated execution; suite-authored `observed_output`/`fixture_output` cannot certify. Local canary-echo is receipt-bound only. Studio-wide promotion of published certified profiles still depends on executed evidence + publication + (when applicable) applied schema.
**Blocked on:** applied `lskills` schema (including registry foundation) on target Supabase + real eval evidence + supervised/live librarian passes.
**Do not** start multi-day Cursor canary until certification + Platform gates pass independent verification.

### 2. Confirm `lskills` migrations applied per environment (Platform-owned live apply)

**Status:** Open (ops verify; **outside full LiNKskills ownership**).
Migrations `20260715_000002`, `000003` seed, `20260718_000004` PostgREST exposure, and additive **`20260727_000005` registry foundation** are **packaged in this repo**. **LiNKplatform alone applies live.** Runbook still expects `select count(*) from lskills.catalog` ≥ 34 when seeded; registry tables require `000005` apply confirmation.
**Do not claim** every env is applied without Platform confirmation.

### 3. Unsupervised production Librarian schedule

**Status:** Partially done.
Runnable generic host: `LiNKplatform/packages/librarian-runner`. Skills domain worker package: `packages/librarian_domain`. First production passes should stay dry-run / supervised until trusted.
**Remaining:** stage→prod confidence, monitoring, escalation briefing path for the Principal.

### 4. Live Platform authentication issuer (claims shape consumed)

**Status:** Partially done / still blocked on live issuer + frozen PACI envelope.
Gateway/MCP consume AuthClaims `1.1.0` / `@linktrend/platform-contracts@0.2.2`. **2026-07-30 production packet:** Skills-owned PACI ES256/JWKS/introspection **consumer adapter** + Cursor `private_key_jwt` client landed locally and marked **implemented but not proven against frozen Platform PACI service** (envelope still `0.1.3-draft`). Live Platform token issuance / stage JWKS / introspection remain Platform gates.
Spoofed body identity is rejected.
**Correction (2026-07-28):** prior fake-shape acceptance on production verifier path is removed.
**Wave 2 (2026-07-28):** historical consume of frozen `platform.auth-claims/1.0.0` (`@linktrend/platform-contracts@0.2.1`) — rejection-only / historical pin retained at `docs/contracts/frozen/platform-auth-claims-v1.0.0.CONSUMER-PIN.md`.
**Wave 4 (2026-07-28):** unsigned production default removed; cryptographic authenticity required outside local-test. See `docs/handoffs/2026-07-28-grok-certification-correction-wave4.md`.
**Wave 5 (2026-07-28):** consumer repinned to `platform.auth-claims/1.1.0` (`orgId` null only for `actorKind: service`); exact `permittedOperations` enforcement. Package pin corrected to `@linktrend/platform-contracts@0.2.2` (2026-07-30). See `docs/contracts/frozen/platform-auth-claims-v1.1.0.CONSUMER-PIN.md`.

### 5. Live stage/prod internal-launch readiness

**Status:** Open / **not claimed**.
In-repo packages, local Gateway `/health`/`/ready`/`/metrics`/`/drain`, Postgres adapters (env-selected), and unit/ephemeral proofs are **not** evidence of shared stage/prod readiness. Remains blocked on Platform migration apply, frozen+live PACI, supervised ops, actor integration owners, OpenClaw/Lisa Skills gate, and independent Codex verification.

### 6. Independent Codex verification of issue #21 / plan execution

**Status:** Open (required).
Grok/Cursor implementation reports are provisional until the LiNKskills Codex verifier checks actual implementation and evidence against the approved plan hash. Coordinating cross-repo verification remains outside a single Skills-only claim.

### 7. Actor integration apply beyond Skills-owned canary

**Status:** Partially done / handed off.
Cursor product canary is **project-scoped only** (example fragment + notes). Codex and OpenClaw configuration **fragments are handed off** (`configs/fragments/`, `docs/integrations/*/HANDOFF.md`) and **must not be applied from this repo** to shared Codex host config or OpenClaw internals.

### 8. Org-scoped RLS on nullable `lskills.catalog.org_id`

**Status:** Deliberately deferred.
Column is future-proofing only; no authorization semantics today (ADR 0001).

### 9. Root-level historical PRD / SOP / operator briefing docs

**Status:** Noted, not archived this pass (2026-07-19 judgment; still accurate).
Files such as `SOP.md`, `OPERATOR_BRIEFING.md`, `260319 LiNKskills PRD.md`, and the Phase 0–3 dossier remain at repo root. They contain stale MAS / pre-ADR framing. They are **not** source of truth; a later cleanup may `git mv` them into `docs/archive/` once no external runbook depends on their paths.

### 10. Dollar-cost accounting dashboard

**Status:** Deliberately deferred.
Telemetry may carry observational `cost` jsonb; no billing ledger in this Program.

### 11. Compatibility git-checkout consumer path retirement

**Status:** Open (migration window).
`lib/skill_runtime` remains supported during migration. Steady-state delivery is Gateway + published releases (ADR 0002/0003). Do not remove the compatibility path until consumers have migrated and Principal/release owners agree.

---

## Recently completed (selected)

### Production packet (PACI adapter / Cursor client / Postgres / ops) — 2026-07-30

Principal-authorized production execution from `docs/CURSOR-GROK-PRODUCTION-EXECUTION-PROMPT-2026-07-30.md`. Landed Skills-owned: PACI JWT/JWKS/introspection consumer adapter (DRAFT envelope; not live-proven), Cursor `client_credentials`+`private_key_jwt` client, Postgres gateway/librarian/publisher adapters + additive migration `000007`, installable packages, Gateway health/ready/metrics/drain, ops rewrite, classification honesty, librarian/stage readiness packets. **Hard stop** for Platform frozen PACI + live stage, OpenClaw Lisa gate, Codex verification, paid hosts. Handoff: `docs/handoffs/2026-07-30-linkskills-production-execution-provisional.md`.

### A. Catalog + eval + telemetry schema — 2026-07-15

`lskills.catalog` / `telemetry` / `eval_runs` migration written; ADR 0001 accepted; Logic Engine archived under `archive/logic-engine-2026-07-14/`.

### B. Right-sized `format_profile` + Librarian skill instructions — 2026-07-15+

`validator.py` simple/heavy branching; `skill-template` / `skill-architect` updated; `self-improvement` reframed as async Librarian instructions; LiNKplatform librarian-runner addendum on ADR 0001.

### C. Eval-suite backfill — 2026-07-15 → 2026-07-18

Baseline `eval-suite.yaml` landed for all skills (priority batches then remaining). Validator requires suite presence/structure.

### D. Consumer runtime engineering (P0/P1) — 2026-07-18

`lib/skill_runtime`, `catalog/index.json`, telemetry flush script, CI catalog gates, deploy/runbook rewrite away from Logic Engine compose, PostgREST exposure migration.

---

## 1. Documentation cleanup — three new source-of-truth documents, legacy docs archived, this file created — 2026-07-19

Following the same playbook already completed on sibling repo LiNKdeveloper (2026-07-18, OPEN-ISSUES item #43 there), performed the Principal-requested documentation source-of-truth cleanup for LiNKskills.

**New source-of-truth documents created** (drafted against real code — `lib/skill_runtime`, `validator.py`, migrations, CI, `skills/`, and the LiNKplatform `librarian-runner` split — and with an explicit drift table vs the archived catalog/eval/telemetry spec):

- `docs/LINKSKILLS-INTENT.md` — why this Program exists, scope, out-of-scope (explicitly not governance), success criteria.
- `docs/LINKSKILLS-TECHNICAL-PRD.md` — exhaustive technical reference (architecture, glossary, authoring/validation pipeline, eval suites, telemetry, consumer load path, Librarian cross-repo relationship, package map, deferred items, §11 drift table).
- `docs/LINKSKILLS-OPERATIONS-MANUAL.md` — plain-English handbook for the Principal (non-technical audience).

**This file created:** `docs/OPEN-ISSUES.md` (no prior equivalent existed; unlike LiNKdeveloper there was no `NEXT-STEPS.md` to rename).

**Legacy documentation archived to `docs/archive/`** (moved, not deleted; `docs/archive/README.md` explains the supersession and links back to the new documents):

- `docs/README.md` → `docs/archive/README-docs-index.md` (name disambiguated from the archive folder’s own index)
- `docs/archive/DOCUMENTATION_GOVERNANCE.md`
- `docs/archive/RELEASE_GATE_CHECKLIST.md`
- `docs/archive/SOURCE_OF_TRUTH_RELEASE_DISCIPLINE.md`
- `docs/archive/BRANCHING_AND_DEPLOYMENT_POLICY.md`
- `docs/archive/specs/catalog-eval-telemetry-spec.md` → `docs/archive/specs/catalog-eval-telemetry-spec.md`
- `docs/archive/CONSUMER-SKILL-LOAD-PATH.md`

Every in-repo cross-reference to these old paths (README, AGENTS.md where needed, catalog README, runbook, validator comment, skill reference docs, eval-suite header comments) was updated to the new Intent/Technical PRD paths or to `docs/archive/...` — verified zero dangling references remain outside explicitly untouched trees (`archive/logic-engine-2026-07-14/**`, `tools/gws/vendor/**`, `.cursor/**`).

**Explicitly NOT archived (judgment call, parallel to LiNKdeveloper keeping `doctrine/` live):**

- `docs/adr/0001-retire-logic-engine-governance-layer.md` — still actively cited by AGENTS.md, migrations, consumer runtime docstring, archive/logic-engine README, and the new Intent/Technical PRD. Kept live.
- `docs/runbooks/PRODUCTION_OPERATIONS.md` — still the live VPS/host bootstrap runbook; references updated.
- `archive/logic-engine-2026-07-14/**` — already archived in a separate namespace; left completely alone.
- Root-level historical PRD/SOP/briefing files — noted in item 9 above; not moved this pass.
- `catalog/**` skill content and `.cursor/` — out of scope per cleanup brief.

**`README.md` rewritten** (not archived — repo live entry point) to point at the 4 new documents as source of truth and to correct stale “specs as SoT” claims.

**Verification performed after structural changes:** `python3 validator.py --repo-root . --scan-all`, `python3 scripts/build-catalog-index.py --check`, `python3 -m unittest discover -s tests/skill_runtime -v`, `python3 scripts/check-service-ownership.py` — expected green (documentation/file-organization pass; no skill package logic intentionally changed).

**What this deliberately does NOT do:** delete any archived document (moved only); touch Logic Engine archive or vendored gws docs; edit skill catalog content under `catalog/` beyond reference path updates in comments/docs that cite old paths; rename skill directories.

---

## 2. Issue #21 / internal-launch plan execution — architecture packages + SoT reconciliation — 2026-07-27

Executing approved plan [`LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md`](./LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md) (SHA-256 `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`) on branch `issue/21-linkskillsdevelopmentplan01`.

### Completed in this Program (implementation / packaging — not live readiness claims)

- **ADRs 0002–0008 accepted** alongside permanent ADR 0001 (git vs published authority; protocol-independent core + MCP/API; Skill Pack v0.1 progressive disclosure; tool execution binding / host authority; execution-profile certification; telemetry privacy/retention; Librarian ownership cross-repo contract).
- **Domain packages landed under `packages/`:** `contracts`, `core`, `publisher`, `eval_runner`, `tool_runtime`, `gateway`, `mcp_server`, `client`, `librarian_domain`.
- **`skills_*` MCP + stdlib HTTP Gateway** exist in-repo; live Platform auth uses **fakes** until Platform publishes.
- **Real Eval Runner** certification path **rejects prompt-only** / fake-judge evidence.
- **Additive migration `supabase/migrations/20260727_000005_lskills_registry_foundation.sql` packaged** with manifest under `docs/migrations/`; **LiNKplatform alone applies live**.
- **`lib/skill_runtime` retained** as compatibility / migration consumer path (not removed; not claimed as final sole load path).
- **Actor integration scoping:** Cursor canary **project-scoped only**; Codex/OpenClaw fragments under `configs/fragments/` + `docs/integrations/` **handed off, not applied here**.
- **Permission-to-act remains NEVER in this repo** (ADR 0001). **Brain/Skills remain separate services.**
- **Source-of-truth docs updated** (Intent, Technical PRD, Operations Manual, README, this file) to describe the launch architecture now being implemented — not only the 2026-07-19 git-checkout catalog snapshot.

### Explicitly still open after this item (see Still open above)

- Live stage/prod readiness (not claimed)
- Live migration apply confirmation (Platform-owned)
- Real Platform auth replacing fakes
- Independent Codex verification of plan execution
- Unsupervised production Librarian schedule
- Full consumer cutover off the git-checkout compatibility path

**What this item deliberately does NOT claim:** shared environment health; completed Codex verification; applied `000005` on stage/prod; real Platform auth in production; OpenClaw/Codex host config applied from Skills.
