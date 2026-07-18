# Archived: LiNKskills Logic Engine (governance/control-plane design)

Owner: LiNKtrend Platform
Archived: 2026-07-14
Superseded by: [`docs/adr/0001-retire-logic-engine-governance-layer.md`](../../docs/adr/0001-retire-logic-engine-governance-layer.md)

## What this is

This folder preserves the **Logic Engine** subsystem that was built into LiNKskills
during PRD v4.0 "MVO Class A". The Logic Engine was a FastAPI control-plane layer
that added governance / permission-to-act machinery on top of the skills catalog:
per-tenant entitlements, disclosure tokens, kill-switches, safe-mode, a data-purge
registry (DPR), per-tenant capability policy, complexity multipliers, and a financial
ledger.

Contents:

| Path (here) | Original repo path | What it is |
|---|---|---|
| `logic-engine/` | `services/logic-engine/` | FastAPI control-plane: `src/logic_engine/` (api/engine/security/store/registry/retention/types/config), `sql/001_schema.sql` + `sql/002_rls.sql` (governance tables), `config/` (capability_policy, class_b_entitlements, override_approvals, dpr_registry, complexity_multipliers), `scripts/`, `tests/`, `docs/` |
| `PRD_LINKSKILLS_LOGIC_ENGINE.md` | `PRD_LINKSKILLS_LOGIC_ENGINE.md` | The PRD describing the control-plane design |
| `SOP_MACHINE_MVO_CLASS_A.md` | `SOP_MACHINE_MVO_CLASS_A.md` | MVO Class A machine SOP (entitlement/kill-switch/DPR language) |
| `SOP_MVO_CLASS_A.md` | `SOP_MVO_CLASS_A.md` | MVO Class A master SOP |
| `SOP_HUMAN_MVO_CLASS_A.md` | `SOP_HUMAN_MVO_CLASS_A.md` | MVO Class A human SOP |
| `cursor-rules/11-logic-engine.mdc` | `.cursor/rules/11-logic-engine.mdc` | Cursor rule scoping the Logic Engine service |

The governance tables carried by `logic-engine/sql/001_schema.sql` included
`class_b_entitlements`, `override_approvals`, `dpr_registry`, `capabilities`
(`certification_state` / `activation_state` / `license_type` / `visibility`),
`disclosures` (`token_jti` / `token_exp`), `kill_switch_state`, `safe_mode_state`,
`financial_ledger`, and `complexity_multipliers`.

## Why it was archived (not deleted)

The Principal explicitly reversed this design. Governance and permission-to-act do
**not** belong to LiNKskills. They belong to:

- **each Program's own Program Ledger** (Issue/Run/Gate/Event, capability-lease
  issuance and enforcement), and
- **`platform.capabilities` / `platform.capability_grants`** in the sibling
  **LiNKplatform** repo (the catalog + licensing policy that each Program's Ledger
  checks against).

See `LiNKplatform/docs/specs/shared-foundation-spec.md` §5 ("Replaces the earlier
(incorrect) idea of LiNKskills owning governance") and §7 (LiNKskills' corrected,
permanent scope).

LiNKskills is now permanently scoped to **catalog + mandatory eval-suite +
usage telemetry only** — no entitlements, no leases, no kill-switches, no financial
ledger, no per-tenant policy.

This subsystem is retained here for traceability (mirroring the studio's
"archive before delete" governance, and the sibling `LiNKsites/archive/` house
style) rather than hard-deleted. It is **not** live-wired into anything and should
not be revived. Do not import from or extend this folder; treat it as a frozen
historical record. Field *names* worth reusing (from `runs` / `usage_events`) were
carried forward into the new telemetry design **without** their tenant/entitlement/
authorization coupling — see the ADR and `docs/specs/catalog-eval-telemetry-spec.md`.

## Not archived (checked, deliberately left in place)

- `configs/activation.json` (+ `.example`) — **checked and left in place.** These are
  a local tool auto-load toggle (`active_uid_list`, `auto_load_on_startup`) for which
  tool packages load on startup, **not** the Logic Engine's governance `activation_state`.
  They are unrelated to the reversed design and remain a legitimate local dev config.
