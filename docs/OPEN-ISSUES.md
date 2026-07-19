# LiNKskills — Open Issues

Append-only engineering build log for this repository. Prefer this file over stale prose elsewhere when asking “what is actually done / deferred?”

**Source of truth for product intent and design:** [`LINKSKILLS-INTENT.md`](./LINKSKILLS-INTENT.md), [`LINKSKILLS-TECHNICAL-PRD.md`](./LINKSKILLS-TECHNICAL-PRD.md), [`LINKSKILLS-OPERATIONS-MANUAL.md`](./LINKSKILLS-OPERATIONS-MANUAL.md).

---

## Still open / deliberately deferred

### 1. Live certification of skills to `usable`

**Status:** Open (operational).  
Filesystem catalog + eval-suite YAML exist for all 34 skills; generated `catalog/index.json` still defaults `certification_state` to `draft`. Consumers correctly use `require_usable=False` until Librarian eval_runs promote versions.  
**Blocked on:** applied `lskills` schema on target Supabase + supervised/live librarian-runner passes.

### 2. Confirm `lskills` migrations applied per environment

**Status:** Open (ops verify).  
Migrations `20260715_000002`, `000003` seed, `20260718_000004` PostgREST exposure are in-repo. Runbook expects `select count(*) from lskills.catalog` ≥ 34 when seeded.  
**Do not claim** every env is applied without checking.

### 3. Unsupervised production Librarian schedule

**Status:** Partially done.  
Runnable worker: `LiNKplatform/packages/librarian-runner` (skills half + brain half). First production passes should stay `LIBRARIAN_DRY_RUN=true` until trusted.  
**Remaining:** stage→prod confidence, monitoring, escalation briefing path for the Principal.

### 4. Org-scoped RLS on nullable `lskills.catalog.org_id`

**Status:** Deliberately deferred.  
Column is future-proofing only; no authorization semantics today (ADR 0001).

### 5. Root-level historical PRD / SOP / operator briefing docs

**Status:** Noted, not archived this pass (2026-07-19 judgment).  
Files such as `SOP.md`, `OPERATOR_BRIEFING.md`, `260319 LiNKskills PRD.md`, and the Phase 0–3 dossier remain at repo root. They contain stale MAS / pre-ADR framing. They are **not** source of truth; a later cleanup may `git mv` them into `docs/archive/` once no external runbook depends on their paths.

### 6. Dollar-cost accounting dashboard

**Status:** Deliberately deferred.  
Telemetry may carry observational `cost` jsonb; no billing ledger in this Program.

---

## Recently completed (selected)

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
- Root-level historical PRD/SOP/briefing files — noted in item 5 above; not moved this pass.
- `catalog/**` skill content and `.cursor/` — out of scope per cleanup brief.

**`README.md` rewritten** (not archived — repo live entry point) to point at the 4 new documents as source of truth and to correct stale “specs as SoT” claims.

**Verification performed after structural changes:** `python3 validator.py --repo-root . --scan-all`, `python3 scripts/build-catalog-index.py --check`, `python3 -m unittest discover -s tests/skill_runtime -v`, `python3 scripts/check-service-ownership.py` — expected green (documentation/file-organization pass; no skill package logic intentionally changed).

**What this deliberately does NOT do:** delete any archived document (moved only); touch Logic Engine archive or vendored gws docs; edit skill catalog content under `catalog/` beyond reference path updates in comments/docs that cite old paths; rename skill directories.
