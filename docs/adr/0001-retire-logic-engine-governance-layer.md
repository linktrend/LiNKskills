# ADR 0001 — Retire the Logic Engine Governance Layer; Scope LiNKskills to Catalog + Eval + Telemetry

- **Status:** Accepted
- **Date:** 2026-07-14
- **Decided by:** Principal, per the reversal recorded in `LiNKplatform/docs/specs/shared-foundation-spec.md` §5 and §7; executed as a LiNKskills-side retirement
- **Context source:** `LiNKplatform/docs/specs/shared-foundation-spec.md` (§1, §5, §7, §10 step 3), the archived subsystem now under `archive/logic-engine-2026-07-14/`, and the LiNKskills audit completed 2026-07-14. Aligns with `LiNKplatform/docs/adr/0001` (§Follow-up) and `LiNKsites/docs/adr/0003` (Decision 3).

## Context

LiNKskills was originally scoped as a **centralized skills catalog** — a library of
progressive-disclosure skills (`SKILL.md` + `advanced/` + `examples/` + `references/` +
`scripts/`) authored via the `skill-architect` / `skill-template` pattern, plus a
structural validator (`validator.py`), a telemetry aggregator (`global_evaluator.py`),
a thin execution ledger (`execution_ledger.jsonl`), and a catalog (`manifest.json`,
`SKILLS_CATALOGUE.md`).

At some point during PRD v4.0 ("MVO Class A"), a **Logic Engine** control-plane layer was
added on top of the catalog. It introduced governance / permission-to-act machinery that
LiNKskills was never meant to own:

- a FastAPI control plane (`services/logic-engine/src/logic_engine/`: api / engine /
  security / store / registry / retention / types / config),
- governance tables (`services/logic-engine/sql/001_schema.sql`, `002_rls.sql`):
  `class_b_entitlements`, `override_approvals`, `dpr_registry`,
  `capabilities.certification_state` / `activation_state` / `license_type` / `visibility`,
  `disclosures` (`token_jti` / `token_exp`), `kill_switch_state`, `safe_mode_state`,
  `financial_ledger`, `complexity_multipliers`,
- per-tenant policy config (`config/capability_policy.json` with
  `allowed_tenants` / `license_type` / `activation_state`, `class_b_entitlements.json`,
  `override_approvals.json`, `dpr_registry.json`),
- and the surrounding PRD / SOP layer (`PRD_LINKSKILLS_LOGIC_ENGINE.md`,
  `SOP_MACHINE_MVO_CLASS_A.md`, `SOP_MVO_CLASS_A.md`, `SOP_HUMAN_MVO_CLASS_A.md`) plus a
  Cursor rule (`.cursor/rules/11-logic-engine.mdc`).

This is a per-tenant entitlement, disclosure-token, kill-switch, data-purge, and
financial-ledger system — i.e. a governance and capability-permission-to-act plane. The
Principal has now explicitly reversed that design.

`LiNKplatform/docs/specs/shared-foundation-spec.md` §5 states the correction directly:
"Replaces the earlier (incorrect) idea of LiNKskills owning governance. This is the actual
home for 'what external capabilities exist and who may use them' … each Program still
enforces its own leases/gates via its own Program Ledger; this registry is the catalog +
licensing policy those Ledgers check against." §7 fixes LiNKskills' permanent scope to
catalog + mandatory-eval-suite + telemetry only. The build sequence (§10 step 3) names the
LiNKskills repo work as exactly that — "catalog + mandatory eval schema + telemetry."

## Decision

**1. Retire the Logic Engine governance layer.** Governance and permission-to-act are
removed from LiNKskills' scope permanently. Per this repo's own "archive before delete"
governance (`docs/DOCUMENTATION_GOVERNANCE.md`) and the sibling `LiNKsites/archive/` house
style, the subsystem is **archived, not deleted** — moved with history preserved
(`git mv`) into `archive/logic-engine-2026-07-14/`:

- `services/logic-engine/` → `archive/logic-engine-2026-07-14/logic-engine/`
- `PRD_LINKSKILLS_LOGIC_ENGINE.md`
- `SOP_MACHINE_MVO_CLASS_A.md`, `SOP_MVO_CLASS_A.md`, `SOP_HUMAN_MVO_CLASS_A.md`
- `.cursor/rules/11-logic-engine.mdc` → `archive/logic-engine-2026-07-14/cursor-rules/11-logic-engine.mdc`

Local, gitignored runtime artifacts that were physically co-located in
`services/logic-engine/runtime/` (`gsm-secrets.json`, `store.json`) were **not** carried
into the archive — they were never source-of-truth, were never tracked in git, and (in the
case of `gsm-secrets.json`) are secrets-shaped and must never be committed. The stale
`.gitignore` rules that pointed at the old `services/logic-engine/runtime/` path were
repointed at the archive path.

`configs/activation.json` (+ `.example`) was **checked and deliberately left in place.**
Despite the superficially governance-sounding name, its contents are a local tool
auto-load toggle (`active_uid_list`, `auto_load_on_startup`) controlling which tool
packages load on startup — it is **not** the Logic Engine's governance `activation_state`
and is unrelated to the reversed design.

**2. LiNKskills is now permanently scoped to catalog + mandatory eval-suite + usage
telemetry only.** Specifically (detailed in `docs/specs/catalog-eval-telemetry-spec.md`):

- the skills **catalog** (`lskills_catalog`) with a **not-null `eval_suite_ref`** and an
  internal `certification_state` promotion gate,
- a mandatory per-skill **eval suite** (`lskills_eval_runs` recording rubric scores, not
  just pass/fail), and
- usage **telemetry** (`lskills_telemetry`), extended from the thin
  `execution_ledger.jsonl`,
- curated by the **Librarian** process (the promoted `self-improvement` skill) reading
  telemetry + eval runs and proposing versioned upgrades.

LiNKskills holds **no** entitlements, leases, kill-switches, safe-mode, financial ledger,
disclosure tokens, or per-tenant policy. It never decides whether a Program may *act*.

**3. Governance / permission-to-act lives elsewhere, by design and permanently.**

- **Each Program's own Program Ledger** owns capability-lease issuance and enforcement
  (Issue / Run / Gate / Event, idempotency, fencing). LiNKsites already has one
  (`packages/program-ledger`, `lsites_ledger`); every future Program builds or adapts its
  own.
- **`platform.capabilities` / `platform.capability_grants`** (LiNKplatform repo) is the
  registry of what external capabilities exist and which tenant may use them. A Program's
  Ledger checks `platform.capability_grants` before issuing a lease for anything touching
  an external system (spec §5).

This mirrors and confirms `LiNKsites/docs/adr/0003` Decision 3 (LiNKsites' own Ledger is
the permanent home for its leases; no future LiNKskills integration for governance is
expected) and closes out the follow-up flagged in `LiNKplatform/docs/adr/0001`.

## Rationale

- **The reversal is authoritative and specific.** The shared-foundation spec does not
  merely deprioritize LiNKskills governance — it states the earlier idea was *incorrect*
  and relocates the responsibility explicitly (§5, §7). Leaving the Logic Engine in place
  would leave a second, competing home for permission-to-act, exactly the cross-service
  responsibility bleed the ecosystem-boundaries doctrine forbids ("no service should
  absorb another service's responsibility").
- **The subsystem is self-contained and not live-wired.** It lived under
  `services/logic-engine/` with its own SQL, config, and FastAPI runtime; no Supabase
  project exists for LiNKskills, so nothing in production reads or writes its tables today.
  Archiving it removes a dormant governance surface at low risk.
- **Archive, not delete,** preserves the design as a historical record (and keeps
  reusable field *names* discoverable) without leaving it as a tempting live dependency.
  This matches the repo's documented governance and the sibling repos' precedent.
- **A single, coherent permission model.** Concentrating permission-to-act in each
  Program's Ledger + the shared capability registry gives one auditable trust boundary per
  Program instead of a central LiNKskills chokepoint that every Program would have to
  couple to (recreating the exact single-point-of-coupling problem `LiNKplatform` ADR 0001
  was created to avoid).

## Consequences

- LiNKskills' surface shrinks to catalog + eval + telemetry + Librarian curation. The
  doctrine-aligned assets are kept and evolved in place: `skills/` (all skill folders and
  the progressive-disclosure shape), the authoring meta-skills (`skill-architect`,
  `skill-template`, `tool-architect`), `self-improvement` (to be promoted to the
  Librarian), `validator.py`, `global_evaluator.py`, `execution_ledger.jsonl`,
  `manifest.json`, `SKILLS_CATALOGUE.md`, and `tools/`.
- No Program should expect or plan a LiNKskills integration for leases or governance. The
  one expected integration is narrow and one-directional: a Program's Ledger checking
  `platform.capability_grants` — a licensing lookup against LiNKplatform, not a hand-off to
  LiNKskills.
- A new `certification_state` gate is introduced in the catalog design. It is legitimately
  **LiNKskills-internal** — permission for the *curation process* to promote a skill to
  `usable` once it has an eval suite — and is explicitly **not** the old Logic Engine's
  tenant `activation_state` / entitlement, and not a Program-execution permission.
- `docs/adr/` is established in this repo starting at 0001 (no prior ADR numbering existed
  here).

## Alternatives considered

- **Delete the Logic Engine outright:** rejected — the studio's governance requires
  "archive first, then schedule deletion in a later cleanup" for superseded work, and the
  design retains value as a historical record and as a source of already-vetted telemetry
  field names. Hard-deletion also discards `git` history unnecessarily.
- **Keep the Logic Engine but disable it / mark it interim:** rejected — the reversal is
  stated as the corrected *permanent* design, not a temporary gap. Leaving a dormant
  governance plane in the live tree invites future re-wiring and keeps two competing homes
  for permission-to-act.
- **Fold LiNKskills governance into LiNKplatform instead of removing it:** rejected — that
  is not what was decided. Permission-to-act enforcement belongs to each Program's own
  Ledger; LiNKplatform owns only the capability *registry/licensing catalog* those Ledgers
  check against (spec §5). Moving the Logic Engine wholesale into LiNKplatform would
  recreate a central enforcement chokepoint there instead.
- **Archive `configs/activation.json` alongside the subsystem because of its name:**
  rejected after reading it — it is an unrelated local tool auto-load config, not
  governance state.

## Follow-up

- Implement the catalog + telemetry + right-sized-template design in
  `docs/specs/catalog-eval-telemetry-spec.md`; backfill per-skill eval suites behind the
  `certification_state != usable` gate, prioritized by real usage telemetry.
- Promote `skills/self-improvement/` to the doctrine's "Librarian" (async scheduling,
  eval-suite re-runs alongside ledger review) — specified in the spec doc; not executed
  here.
- Wire this repo's `.cursor/` to the shared IDE Development `.cursor` system, and refresh
  the older local rule set (currently uses "Chairman" and a pre-`development` git-flow) —
  tracked as a separate follow-up, **not** done in this change.
- A live `lskills_` schema / migration is deferred until LiNKskills gets its own Supabase
  project or schema in the shared platform (spec §10 step 3) — no migration is written in
  this change.
