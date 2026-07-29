# Correction Handoff Wave 10 — Codex independent findings

**Status:** Provisional Grok correction report for independent Codex re-verification. **Do not self-certify. Do not merge PR #22. Do not start the multi-day Cursor canary. Do not deploy. Do not apply live Platform migrations.**

**Date:** 2026-07-29  
**Executor:** Cursor Local Agent (Grok 4.5 High) — original issue/21 owner  
**Issue:** https://github.com/linktrend/LiNKskills/issues/21  
**PR:** https://github.com/linktrend/LiNKskills/pull/22  
**Branch:** `issue/21-linkskillsdevelopmentplan01`  
**Base head for this wave:** `1392e836160e6634d862935b6fea990c586eee91`  
**Wave-10 code tip (exact clean pushed head before handoff pin):** `9227507964fec7553afaa444c32a01608dc5686d`  
**Plan hash:** `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`

## Wave 10 corrections (Codex findings)

1. **Request-local mutation batches** — Removed shared `SkillsGatewayService._mutation_batch`. Pending publishes are bound via `contextvars.ContextVar` with token restore in `finally`. Only the committing request’s pending cache/list mutations are published; rollback discards only that request’s batch. Deterministic two-thread, different-key test: both wait before atomic lock acquisition; one commits, one crashes after mutation; SQLite and service-visible state stay identical; retry of the crashed key yields one logical mutation.

2. **Honest downstream acknowledgment** — Response field is `downstream_idempotency_propagated` when the key is sent downstream. `downstream_idempotency_honored` / `downstream_idempotency_exactly_once` are set only when the adapter returns an explicit `True`. Echoing the LiNKskills-generated key in metadata is not treated as honor. `external_side_effect_at_least_once` is retained whenever acknowledgment/exactly-once is absent.

## Preserved

- Wave 8 shared hashing / launch-target profiles
- Wave 9 fencing, stable downstream keys, durable-result reconciliation, crash injection, isolation, RLS

## Proof actually run (local; no hosted CI wait)

```bash
export PYTHONPATH="packages/core:packages/gateway:packages/tool_runtime:packages/eval_runner:packages/contracts:packages/publisher:packages/librarian_domain:packages/mcp_server:packages/client:packages/skill_runtime:."
export LINKSKILLS_EVAL_RUNNER_ISSUER_KEY=linkskills-local-eval-runner-issuer-key-not-for-production
export LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven
python3 -m pytest -q
# 175 passed, 4 skipped
python3 -m pytest tests/migrations/test_rls_actor_org_ephemeral.py -q
# 5 passed
python3 scripts/validate_skills.py --scan-all
python3 scripts/build-catalog-index.py --check
python3 scripts/check-service-ownership.py
# deterministic hash agreement for 10 launch targets
git diff --check
```

## Explicit non-actions

- Did not poll/rerun hosted CI or Bugbot, change PR readiness, merge, apply migrations, start canaries, deploy, or perform live actions.
- Did not self-certify.

## Ask of LiNKskills Codex

Re-verify against this branch tip and the two findings above. Treat this as a correction packet, not certification.
