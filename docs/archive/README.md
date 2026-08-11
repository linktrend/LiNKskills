# Archive — superseded by the current source-of-truth documents

Everything under `docs/archive/` is retained for history but is **no longer authoritative**. Some of it (especially the catalog/eval/telemetry design spec's "not done" follow-ups) is factually stale relative to the code as it stands today — see the Technical PRD §12 drift table.

**Current source of truth (refreshed 2026-08-11):**

- [`../LINKSKILLS-INTENT.md`](../LINKSKILLS-INTENT.md) — why LiNKskills exists, scope, and what "done" means.
- [`../LINKSKILLS-TECHNICAL-PRD.md`](../LINKSKILLS-TECHNICAL-PRD.md) — the exhaustive technical reference for how the system actually works, including where archived documents have drifted from real code.
- [`../LINKSKILLS-OPERATIONS-MANUAL.md`](../LINKSKILLS-OPERATIONS-MANUAL.md) — plain-English handbook for the Principal.
- [`../OPEN-ISSUES.md`](../OPEN-ISSUES.md) — the append-only engineering build log and open/deferred items.
- [`../LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md`](../LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md) — approved plan (SHA-256 `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`).
- [`../adr/0001-retire-logic-engine-governance-layer.md`](../adr/0001-retire-logic-engine-governance-layer.md) through [`../adr/0008-librarian-ownership-cross-repo-contract.md`](../adr/0008-librarian-ownership-cross-repo-contract.md) — still live/authoritative ADRs (not archived).
- [`../runbooks/PRODUCTION_OPERATIONS.md`](../runbooks/PRODUCTION_OPERATIONS.md) — still live VPS/host bootstrap runbook.

**Do not treat this archive (or root README status text) as stage/prod readiness.** W20 stage readiness remains **BLOCKED**; PACI pins are local/fake only (Platform `421a35e`, AuthClaims `1.1.0`, contracts `0.2.2` / `0.3.0`).

## What's here

### `legacy-root/` (archived 2026-08-02 — release-hygiene docs lane)

Former **repo-root** historical PRD / SOP / operator / catalogue material moved via `git mv` (not deleted). Superseded as SoT by Intent / Technical PRD / Operations Manual / OPEN-ISSUES. Includes:

- `SOP.md`, `SOP_HUMAN.md`, `SOP_MACHINE.md`
- `OPERATOR_BRIEFING.md`, `OPERATOR_BRIEFING_MVO_CLASS_A.md`
- `260319 LiNKskills PRD.md`
- `LiNKskills PRD v4.0 Implementation Dossier (Phase 0-3).md`
- `COMMAND_REFERENCE.md`
- `SKILLS_CATALOGUE.md`
- `GIT_STRATEGY.md` (historical git remote/branch notes; live flow is AGENTS.md + `.github/workflows/` + Intent/Technical PRD)

Filename mentions of these paths in live ADRs (especially ADR 0001) are **historical prose** — the files now live under this folder.

### Earlier archive contents (2026-07-19 SoT cleanup)

- `README-docs-index.md` — former `docs/README.md` documentation index.
- `DOCUMENTATION_GOVERNANCE.md` — former docs governance rules (archive-before-delete principle is retained in spirit by this folder).
- `BRANCHING_AND_DEPLOYMENT_POLICY.md` — former branching/promotion writeup (flow still accurate; superseded as SoT by Intent/Technical PRD + live `.github/workflows/`).
- `RELEASE_GATE_CHECKLIST.md` / `SOURCE_OF_TRUTH_RELEASE_DISCIPLINE.md` — former release checklists.
- `CONSUMER-SKILL-LOAD-PATH.md` — former consumer load-path doc; content absorbed into Technical PRD §6.
- `specs/catalog-eval-telemetry-spec.md` — original catalog/eval/telemetry design spec; superseded where the build evolved (format_profile implemented, eval suites backfilled, Librarian runner in LiNKplatform, consumer runtime landed). See Technical PRD §12.

**Related but outside this folder:** `archive/logic-engine-2026-07-14/` at the repo root is a self-contained retired code snapshot (separate archive namespace — do not revive or deploy). It stays outside `docs/` to preserve its historical directory structure. Runtime-consumed certification artifacts likewise remain at root-level `evidence/`.

The former root `global_blacklist.md` and `shared/AIOS_RUNTIME_BINDING.md` were
archived here on 2026-08-11. They had no live code, test, CI, or operational
references and described superseded AIOS/MVO-era behavior.

**Not archived here (left live on purpose):** `docs/CURSOR-GROK-*.md` execution/correction prompts — still cited as authority by ADRs 0002–0008 and inventories; do not move without updating every citation.

If something here conflicts with the Intent, Technical PRD, or Operations Manual, **those three documents win.**
