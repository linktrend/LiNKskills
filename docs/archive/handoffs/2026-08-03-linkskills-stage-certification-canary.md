# Handoff — Stage certification canary (sealed local usable skill)

**Date:** 2026-08-03
**Branch:** `dev/cloudcursor/skills-stage-certification`
**Base SHA:** `0e03745a177acabfb5a5440e0bbdbc669c4081b6`
**Verdict:** **PASS** for the local sealed catalog canary gate; **HOLD** for stage/shared readiness

## What changed

1. Catalog skill `skills/canary-echo` (simple, no-side-effect, packaged `text-echo`).
2. Classification ledger overlay wired into `scripts/build-catalog-index.py`
   (`lib/skill_runtime/certification_overlay.py`) — `usable` requires sealed evidence paths.
3. Batch certifier `scripts/certify-catalog.py` evaluates every catalog skill:
   promotes sealed passes; leaves others `draft` with machine-readable `reason_code`.
4. Reproducible sealed host runner `./scripts/run-sealed-linux-certify.sh`
   (privileged local Docker Linux + `bwrap`; not stage/cloud/VPS).
5. Confined executor fixes so container Python works under `bwrap`
   (absolute argv0; FHS `/lib` symlink bind; `/usr/local` bind order; PATH).
6. Evidence: `evidence/phase10/sealed/canary-echo-sealed.json`,
   `evidence/phase10/catalog-certification-report.json`, updated ledger + `catalog/index.json`.

## Counts (post-certify)

| Metric | Value |
|---|---|
| Catalog skills | 35 |
| `usable` | 1 (`canary-echo`) |
| `draft` | 34 |
| Sealed receipt evidence paths | 1 |

## Policy answer

Repo expects production-facing **runs** to be `usable`, but does **not** require every
filesystem-shipped skill to already be `usable`. Draft is honest default until sealed
evidence. Batch automation certifies every skill that satisfies the standard and leaves
failing ones draft with reasons (mostly `suite_not_executable`).

## Verification run

```bash
python3 validator.py --repo-root . --scan-all          # PASS (54 targets)
python3 scripts/build-catalog-index.py --check         # PASS (35 skills, usable=1)
python3 -m unittest discover -s tests/skill_runtime -v # PASS (11)
PYTHONPATH=packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:. \
  LINKSKILLS_EVAL_RUNNER_ISSUER_KEY=linkskills-local-eval-runner-issuer-key-not-for-production \
  LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven \
  python3 -m pytest tests/tool_runtime/test_wave5_confinement.py tests/skill_runtime \
    tests/eval_runner/test_runner_deterministic.py tests/core/test_core.py -q
# 37 passed, 2 skipped
./scripts/run-sealed-linux-certify.sh                  # usable=1 draft=34
```

Gateway check (local index): `skills_run_start` accepts `canary-echo` (`usable`);
rejects `git-safeguard` (`draft` → `skill_not_runnable`). `_assert_skill_runnable` unchanged.

## Residual blockers (HOLD for stage)

- Stage `lskills` schema apply / seed lag (filesystem now 35; packaged seed still 34)
- Live Platform PACI / shared Gateway against stage DB
- Remaining 34 skills lack executable sealed suites
- Independent Codex verification
- This is **not** stage/prod readiness

## Rollback

```bash
git checkout development  # or prior SHA
# or revert this branch's commit(s)
```

Sealed evidence and overlay are in-repo only; no stage/DB mutation to undo.

## Human-only gaps

- Integrator PR review → `development`
- Principal promotion gates unchanged
- Platform apply of catalog seed for `canary-echo` when ready
