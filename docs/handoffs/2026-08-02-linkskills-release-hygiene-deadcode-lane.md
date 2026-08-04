# Handoff — LiNKskills Release Hygiene Lane B (Dead-Code / Reference)

**Status:** Research complete. **Report-only** (`applied=false`). No deletes.
**Date:** 2026-08-02
**Branch:** `dev/cloudcursor/RELEASE-HYGIENE-CLEANUP` @ investigation base SHA `46797b2`
**Lane:** B — dead-code / reference prove-before-delete

**Machine-readable:** `/tmp/linkskills-hygiene-lane-b.json`

## 1. Session outcome

Proved references for root Logic-Engine-era artifacts, `scripts/`, `shared/`, `packages/*`, `lib/skill_runtime`, and sample ledger content. **No PROVEN_DEAD high-confidence temporary leftovers met the ≥2-item delete bar** without risking live skill/CI/compat paths or conflicting with Lane A’s keep of tracked `execution_ledger.jsonl` seed rows. Prefer report-only.

## 2. Method

For each candidate:

1. `rg` across repo excluding `archive/`, `docs/archive/`, `.venv`, `tools/gws/vendor`
2. Package `__init__.py` / `pyproject.toml` entry points
3. Tests under `tests/`
4. `scripts/`, `validator.py`, `.github/workflows/`, `configs/`
5. Classify: `PROVEN_DEAD` | `LIKELY_DEAD` | `KEEP` | `UNCERTAIN`

Concurrent note: Lane A archived root SOP/operator briefings during this pass; some script refs moved into `docs/archive/legacy-root/` mid-investigation. Classifications use **live** (non-archive) refs.

## 3. Evidence table

| Path | Class | Proof (rg / imports / CI) | Action |
|------|-------|---------------------------|--------|
| `lib/skill_runtime/*` | KEEP | Imported by `packages/client/.../compat.py`, gateway server, `scripts/flush-telemetry.py`, `scripts/build-catalog-index.py`, `tests/skill_runtime/` | Do not remove (compat path) |
| `packages/*` domain modules | KEEP | Exported via package `__init__` / entry points; covered by `tests/{core,gateway,client,mcp_server,publisher,eval_runner,librarian_domain,tool_runtime,contracts}` | Domain surface — out of scope |
| `validator.py` | KEEP | CI `.github/workflows/ci.yml` runs `--scan-all`; `scripts/validate_skills.py` delegates here | Keep |
| `global_evaluator.py` | KEEP | Not imported as a module; **CLI** used by `skills/skill-architect` + PRD/ADR; AST-orphan ≠ dead | Keep |
| `global_config.yaml` | KEEP | Loaded by `validator.py` (`load_global_config`) | Keep |
| `factory.json` | KEEP | Required by multiple skills/eval suites (studio-architect, software-pm, lead-engineer, …); ~19 live skill/catalog refs | Keep |
| `manifest.json` | KEEP | ADR 0001 kept doctrine asset; catalog seed comments still name it; superseded for discovery by `catalog/index.json` but not deleted | Keep |
| `execution_ledger.jsonl` | KEEP | Live path: validator requires file; skills append; `.gitignore` (Lane A) says keep tracked — seed rows are fixtures | Keep file + seeds |
| `global_blacklist.md` | PROVEN_DEAD (unref) | **0** live code/test/CI/script refs; validator uses per-skill `old-patterns.md` only; Lane A left at root | Report only — not clearly temp leftover |
| `shared/AIOS_RUNTIME_BINDING.md` | LIKELY_DEAD | **0** live refs (archive-only historically); AIOS/MVO-era contract | Leave; confirm with product before delete |
| `shared/templates/MASTER_FINANCE_TEMPLATES.md` | KEEP | Referenced by `skills/studio-controller`, `skills/smart-file-clerk` (+ eval suites) | Keep |
| `scripts/build-catalog-index.py` | KEEP | CI + `lib/skill_runtime/catalog.py` | Keep |
| `scripts/check-service-ownership.py` | KEEP | CI gate | Keep |
| `scripts/validate_skills.py` | KEEP | Thin wrapper; skill-architect/template/tool-architect instruct use | Keep |
| `scripts/flush-telemetry.py` | KEEP | Production runbook / PRD drain path | Keep |
| `scripts/audit-skill-suites.py` | LIKELY_DEAD (CI) | Only live doc hit: one handoff; produces `evidence/phase1/suite-audit.json` | Keep as operator audit; not CI |
| `scripts/audit-tool-packages.py` | LIKELY_DEAD (CI) | Same; produces `evidence/phase1/tool-audit.json` | Keep as operator audit |
| `scripts/ci-check-frontmatter.sh` | LIKELY_DEAD | **0** live refs after SOP archive; not in `ci.yml` | UNCERTAIN delete — operator gate may still be intentional |
| `scripts/lsl-{update,deploy}.sh`, `lsl-review.py` | LIKELY_DEAD (docs) | **0** live non-self refs after operator docs archived; still runnable git automation | Leave; re-home docs or archive later |
| `packages/gateway/.../auth_testing.py` | KEEP | Heavy test import surface (`mint_test_bearer`) | Keep |
| `packages/.../migrate_frontmatter.py` | KEEP | Exported + `tests/publisher/` | Keep |
| `tests/isolation_probe.py` | KEEP | Imported by eval_runner adversarial/deterministic tests | Keep |
| Scratch `*scratch*` / `*.bak` / temp py | — | None found under live tree | N/A |
| Large commented-out blocks in packages/lib/scripts | — | No ≥15-line commented code runs found | N/A |

## 4. Why `applied=false`

Prove-before-delete requires **≥2 PROVEN_DEAD high-confidence temporary/dev leftovers** before mutating. Closest candidates:

1. `global_blacklist.md` — unreferenced, but policy stub left at root by Lane A; not “clearly temporary.”
2. Ledger sample rows — look like `email-responder` fixture noise, but Lane A’s `.gitignore` comment explicitly treats them as **tracked fixtures**; truncating would fight that.

Deleting orphan `lsl-*` / `ci-check-frontmatter` without a docs re-home is risky operator-tooling loss, not temp cleanup.

## 5. Risks

- Archive of root SOP/OPERATOR docs orphaned operator script *documentation*, not necessarily the scripts.
- `manifest.json` vs `catalog/index.json` dual catalog story can confuse future agents into deleting `manifest.json` — ADR says keep.
- `global_evaluator.py` looks import-dead; it is CLI-live via skills.

## 6. Rollback

N/A — no tree mutations from this lane.

## 7. Suggested follow-ups

1. Product call: delete or archive `global_blacklist.md` and `shared/AIOS_RUNTIME_BINDING.md` in a dedicated docs/archive PR.
2. Re-document or archive `scripts/lsl-*` + `ci-check-frontmatter.sh` after Lane A’s legacy-root move (operator briefing currently archive-only).
3. Optional: wire `audit-skill-suites.py` / `audit-tool-packages.py` into a periodic/manual CI job if Phase-1 evidence must stay fresh.
4. Do **not** remove `lib/skill_runtime` or weaken eval/certification contracts.
