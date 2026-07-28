# Correction Handoff Wave 8 — Codex independent findings

**Status:** Provisional Grok correction report for independent Codex re-verification. **Do not self-certify. Do not merge PR #22. Do not start the multi-day Cursor canary. Do not deploy. Do not apply live Platform migrations.**

**Date:** 2026-07-29  
**Executor:** Cursor Local Agent (Grok 4.5 High) — original issue/21 owner  
**Issue:** https://github.com/linktrend/LiNKskills/issues/21  
**PR:** https://github.com/linktrend/LiNKskills/pull/22  
**Branch:** `issue/21-linkskillsdevelopmentplan01`  
**Base head for this wave:** `f091d67bc15b7ae27203b16b3214321ce20092d0`  
**Wave-8 code tip (exact clean pushed head):** `871c27277cd497083ccc7958e412e10094bea56d`  
**Plan hash:** `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`

## Wave 8 corrections (Codex findings)

1. **Mutation-safe idempotency** — Opaque `fence_token` / `fence_generation` on reserve; complete/failure requires the current fence (late displaced workers rejected). DB-owned writes use `run_atomic_idempotent` (reserve + domain mutation + complete in one SQLite transaction with deferred nested commits). External side effects (`skills_tool_invoke`) use durable intent/result rows plus a propagated `downstream_idempotency_key` and explicitly warn `external_side_effect_at_least_once` (no exactly-once claim). Tests cover crash-after-mutation rollback, stale reclaim, late original completion, concurrent same-key (single domain mutation), same-hash replay, and different-hash conflict.

2. **Shared canonical hashing** — New `packages/core/linkskills_core/hashing.py` is authoritative for publisher bundle content hash, eval-suite file hash, skill-release tree hash, skill-bundle identity, and execution-profile identity/stamping. Publisher and Eval Runner `skill_release_hash` share the same directory digest. Validator recalculates and compares `eval_suite_hash`, `skill_bundle_hash`, and `profile_hash` for launch targets. All 10 canary launch-target `references/execution-profile.json` files regenerated via `stamp_execution_profile`; clean repeated stamps and release hashes agree.

## Preserved

- macOS confinement / Seatbelt pure-allowlist posture from wave 7 (passed prior verification)
- AuthClaims `platform.auth-claims/1.1.0` pin
- Prior authorization, tenant-binding, receipt-signing, pytest-discovery, ServerAdapter-disabled controls
- PR remains draft; no merge / hosted CI poll / canary / deploy / live migrations

## Proof actually run (local; no hosted CI wait)

```bash
export PYTHONPATH="packages/core:packages/gateway:packages/tool_runtime:packages/eval_runner:packages/contracts:packages/publisher:packages/librarian_domain:packages/mcp_server:packages/client:packages/skill_runtime:."
export LINKSKILLS_EVAL_RUNNER_ISSUER_KEY=linkskills-local-eval-runner-issuer-key-not-for-production
export LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven
python3 -m pytest -q
# 167 passed, 4 skipped
python3 -m pytest tests/migrations/test_rls_actor_org_ephemeral.py -q
# 5 passed
python3 scripts/validate_skills.py --scan-all
# ✓ Validation passed for registry scan (53 targets)
python3 scripts/build-catalog-index.py --check
python3 scripts/check-service-ownership.py
# deterministic clean-run hash comparisons for 10 launch targets
git diff --check
```

## Explicit non-actions

- Did not poll/rerun hosted CI or Bugbot, change PR readiness, merge, apply migrations, start canaries, deploy, or perform live actions.
- Did not self-certify.

## Ask of LiNKskills Codex

Re-verify against this branch tip and the two findings above. Treat this as a correction packet, not certification.
