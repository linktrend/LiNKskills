# LiNKskills

LiNKskills is LiNKtrend's **centralized skill catalog**. It provides progressive-disclosure skills, a mandatory per-skill eval suite, usage telemetry, and Librarian curation — and deliberately does **not** own governance or permission-to-act.

## Start here (source of truth)

These documents are the current, authoritative description of this Program. If anything elsewhere in this repo (including older docs under `docs/archive/`) disagrees with them, **these win**:

- **[`docs/LINKSKILLS-INTENT.md`](docs/LINKSKILLS-INTENT.md)** — why LiNKskills exists, who it's for, scope, and what "done" means.
- **[`docs/LINKSKILLS-TECHNICAL-PRD.md`](docs/LINKSKILLS-TECHNICAL-PRD.md)** — the exhaustive technical reference: architecture, authoring/validation, eval suites, telemetry, consumer load path, Librarian split, and what is / isn't built.
- **[`docs/LINKSKILLS-OPERATIONS-MANUAL.md`](docs/LINKSKILLS-OPERATIONS-MANUAL.md)** — a plain-English handbook for the Principal: what your role is and what isn't fully live yet.
- **[`docs/OPEN-ISSUES.md`](docs/OPEN-ISSUES.md)** — append-only engineering build log and open/deferred items.

Still-live supporting docs (not archived):

- [`docs/adr/0001-retire-logic-engine-governance-layer.md`](docs/adr/0001-retire-logic-engine-governance-layer.md) — permanent scope boundary (no entitlements/leases/kill-switches here).
- [`docs/runbooks/PRODUCTION_OPERATIONS.md`](docs/runbooks/PRODUCTION_OPERATIONS.md) — VPS/host checkout bootstrap.

## Scope boundary (important)

LiNKskills does **not** own governance or permission-to-act. It has no entitlements, leases, kill-switches, financial ledger, or per-tenant policy. Permission-to-act lives in **each Program's own Program Ledger** and in **`platform.capabilities` / `platform.capability_grants`** (LiNKplatform). The earlier Logic Engine control plane is retired — see ADR 0001 and [`archive/logic-engine-2026-07-14/`](archive/logic-engine-2026-07-14/).

## Layout

- `skills/` — progressive-disclosure skill packages (`SKILL.md` + `advanced/` / `examples/` / `references/` / `scripts/`). Authoring meta-skills: `skill-architect`, `skill-template`, `tool-architect`. Librarian instructions: `self-improvement`.
- `catalog/index.json` — machine discovery index (regenerate with `python3 scripts/build-catalog-index.py`).
- `lib/skill_runtime/` — consumer Python package (catalog, loader, telemetry).
- `validator.py` — structural Golden Template + eval-suite gate (CI).
- `supabase/migrations/` — `lskills.catalog` / `telemetry` / `eval_runs`.
- `tools/` — global CLI tool packages (`gws`, `ltr`, …).
- `docs/archive/` — superseded documentation retained for history.
- `archive/logic-engine-2026-07-14/` — retired governance subsystem (do not deploy).

## Consumer runtime

Programs load skills from a **git checkout** of this repo (not a LiNKskills API):

```python
from lib.skill_runtime import load_skill, record_invocation, InvocationEvent

bundle = load_skill("git-safeguard", repo_root="/opt/linkskills", require_usable=False)
# ... use bundle.skill_md ...
record_invocation(InvocationEvent(skill=bundle.skill_id, status="completed", summary="..."), repo_root="/opt/linkskills")
```

Full load-path, telemetry flush, and Librarian relationship: Technical PRD §§5–7.

## Core commands

```bash
python3 validator.py --repo-root . --scan-all
python3 scripts/build-catalog-index.py
python3 scripts/build-catalog-index.py --check
python3 -m unittest discover -s tests/skill_runtime -v
python3 scripts/flush-telemetry.py
python3 scripts/check-service-ownership.py
```

## Status

**Catalog + consumer runtime structurally complete as of 2026-07-19.** All skills ship baseline eval-suite YAML; CI runs validator, catalog freshness, unit tests, and ownership gates. Live promotion of every skill to `usable` via the Librarian against applied `lskills` schema remains an operational milestone — see Technical PRD §10 and Operations Manual "Current status."

The runnable Librarian worker lives in **`LiNKplatform/packages/librarian-runner`** (this repo holds the skill-side instructions and the schema gates only).
