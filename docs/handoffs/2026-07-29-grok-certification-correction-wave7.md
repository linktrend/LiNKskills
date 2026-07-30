# Correction Handoff Wave 7 — Codex independent findings

**Status:** Provisional Grok correction report for independent Codex re-verification. **Do not self-certify. Do not merge PR #22. Do not start the multi-day Cursor canary. Do not deploy. Do not apply live Platform migrations.**

**Date:** 2026-07-29
**Executor:** Cursor Local Agent (Grok 4.5 High) — original issue/21 owner
**Issue:** https://github.com/linktrend/LiNKskills/issues/21
**PR:** https://github.com/linktrend/LiNKskills/pull/22
**Branch:** `issue/21-linkskillsdevelopmentplan01`
**Base head for this wave:** `066b3a0dc302cd9df46ddc66176e4f5c698d02a9`
**Wave-7 code tip (exact clean pushed head before handoff pin):** `7284f7b19f21d9e0e5a396da63f7a74c28af2b8f`
**Plan hash:** `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`

## Wave 7 corrections (Codex findings)

1. **Critical macOS confidentiality** — Removed certifiable use of Seatbelt global `(allow file-read*)` + short deny list (reproduced `/var/folders` secret read while claiming `denied`). macOS now claims `denied` only for a **pure path-allowlist** profile that passes a boot probe. Current dyld typically aborts under pure allowlists → isolation stamps `unavailable`/`unproven` and **cannot certify**. Linux `bwrap --tmpfs /` + explicit `--ro-bind` remains the proven path. Adversarial coverage: `/var/folders`, user cache, home files. ADR 0009 amended.
2. **Idempotency concurrency** — In-flight reservation returns `in_progress` (HTTP 409 `idempotency_in_progress`) instead of a second `reserved`. Lease + stale reclaim for crash/retry; same-hash replay and different-hash conflict preserved. In-memory and SQLite stores use locks; SQLite reserve/complete use `BEGIN IMMEDIATE`.
3. **Canonical launch-target artifacts** — All 10 canary/launch-target skills now ship `references/skill-pack.json`, `references/eval-suite.json`, and `references/execution-profile.json` (schema-valid v0.1). Validator **requires** these for IDs in `evidence/phase1/canary-set.json`; legacy YAML alone cannot establish launch readiness. Classification ledger updated: `evidence/phase10/skill-classification-draft.json`.

## Preserved

- AuthClaims `platform.auth-claims/1.1.0` pin
- Prior authorization, tenant-binding, receipt-signing, pytest-discovery, ServerAdapter-disabled controls

## Proof actually run (local; no hosted CI wait)

```bash
export PYTHONPATH="packages/core:packages/gateway:packages/tool_runtime:packages/eval_runner:packages/contracts:packages/publisher:packages/librarian_domain:packages/mcp_server:packages/client:packages/skill_runtime:."
export LINKSKILLS_EVAL_RUNNER_ISSUER_KEY=linkskills-local-eval-runner-issuer-key-not-for-production
export LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven
python3 -m pytest -q
# 160 passed, 4 skipped (macOS unproven-isolation certification paths + one confine skip)
python3 -m pytest tests/migrations/test_rls_actor_org_ephemeral.py -q
# 5 passed (fresh/upgrade/wrong-actor/wrong-org/GUC)
python3 scripts/validate_skills.py --scan-all
python3 scripts/build-catalog-index.py --check
python3 scripts/check-service-ownership.py
git diff --check
```

## Explicit non-actions

- Did not poll/rerun hosted CI or Bugbot, change PR readiness, merge, apply migrations, start canaries, deploy, or perform live actions.
- Did not self-certify.

## Ask of LiNKskills Codex

Re-verify against this branch tip and the three findings above. Treat this as a correction packet, not certification.
