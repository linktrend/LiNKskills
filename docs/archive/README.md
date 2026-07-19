# Archive — superseded by the current source-of-truth documents

Everything under `docs/archive/` is retained for history but is **no longer authoritative**. Some of it (especially the catalog/eval/telemetry design spec's "not done" follow-ups) is factually stale relative to the code as it stands today — see the Technical PRD §11 drift table.

**Current source of truth (2026-07-19):**

- [`../LINKSKILLS-INTENT.md`](../LINKSKILLS-INTENT.md) — why LiNKskills exists, scope, and what "done" means.
- [`../LINKSKILLS-TECHNICAL-PRD.md`](../LINKSKILLS-TECHNICAL-PRD.md) — the exhaustive technical reference for how the system actually works, including where archived documents have drifted from real code.
- [`../LINKSKILLS-OPERATIONS-MANUAL.md`](../LINKSKILLS-OPERATIONS-MANUAL.md) — plain-English handbook for the Principal.
- [`../OPEN-ISSUES.md`](../OPEN-ISSUES.md) — the append-only engineering build log and open/deferred items.
- [`../adr/0001-retire-logic-engine-governance-layer.md`](../adr/0001-retire-logic-engine-governance-layer.md) — still live/authoritative ADR (not archived; actively cited throughout the repo and migrations).
- [`../runbooks/PRODUCTION_OPERATIONS.md`](../runbooks/PRODUCTION_OPERATIONS.md) — still live VPS/host bootstrap runbook.

## What's here

- `README-docs-index.md` — former `docs/README.md` documentation index.
- `DOCUMENTATION_GOVERNANCE.md` — former docs governance rules (archive-before-delete principle is retained in spirit by this folder).
- `BRANCHING_AND_DEPLOYMENT_POLICY.md` — former branching/promotion writeup (flow still accurate; superseded as SoT by Intent/Technical PRD + live `.github/workflows/`).
- `RELEASE_GATE_CHECKLIST.md` / `SOURCE_OF_TRUTH_RELEASE_DISCIPLINE.md` — former release checklists.
- `CONSUMER-SKILL-LOAD-PATH.md` — former consumer load-path doc; content absorbed into Technical PRD §6.
- `specs/catalog-eval-telemetry-spec.md` — original catalog/eval/telemetry design spec; superseded where the build evolved (format_profile implemented, eval suites backfilled, Librarian runner in LiNKplatform, consumer runtime landed). See Technical PRD §11.

**Related but outside this folder:** `archive/logic-engine-2026-07-14/` at the repo root is the retired Logic Engine governance subsystem (separate archive namespace — do not revive or deploy).

If something here conflicts with the Intent, Technical PRD, or Operations Manual, **those three documents win.**
