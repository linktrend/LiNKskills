# Correction Handoff Wave 11 — Codex independent findings

**Status:** Provisional Grok correction report for independent Codex re-verification. **Do not self-certify. Do not merge PR #22. Do not start the multi-day Cursor canary. Do not deploy. Do not apply live Platform migrations.**

**Date:** 2026-07-29  
**Executor:** Cursor Local Agent (Grok 4.5 High) — original issue/21 owner  
**Issue:** https://github.com/linktrend/LiNKskills/issues/21  
**PR:** https://github.com/linktrend/LiNKskills/pull/22  
**Branch:** `issue/21-linkskillsdevelopmentplan01`  
**Base head for this wave:** `972e883378a09386e6269f7cc8f6e9d5009c65df`  
**Wave-11 code tip (exact clean pushed head before handoff pin):** `6f24562270735ac96a40eb160cefcc308d562cae`  
**Plan hash:** `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`

## Wave 11 corrections (Codex findings)

1. **DB commit / cache publication ordering** — DB-owned writes hold `SkillsGatewayService._mutation_gate` from reservation/transaction start through authoritative cache refresh. Mutations inside the boundary read store/transactional state via explicit `MutationContext` (never stale `self._runs`). The gate releases only after commit and publish agree; rollback discards the request-owned context so DB and cache remain at the pre-request state. Deterministic pause-after-commit test proves a peer cannot nonblocking-acquire the gate (and therefore cannot overwrite stale cache) before publish.

2. **Explicit MutationContext ownership** — Removed `contextvars.ContextVar` batch ownership. Request-owned `MutationContext` carries `service_id`, `request_id`, `generation`, `active`, and `published`, is passed through DB-owned handlers, and `assert_writable` fails closed for foreign services, expired, or already-published contexts. Nested Service1 → Service2 mutations use distinct contexts and must not join the parent batch. Captured contexts used after parent publish cannot mutate.

3. **Adversarial concurrency proofs** — `tests/gateway/test_wave11_mutation_serialization.py` covers commit-before-publish peer blocking, store-not-stale-cache updates, nested services, expired async-child fail-closed, and different-key commit/crash/retry with DB/cache equality and one logical event per success.

## Preserved

- Wave 8 shared hashing / launch-target profiles
- Wave 9 fencing, stable downstream keys, durable-result reconciliation, crash injection, isolation, RLS
- Wave 10 honest downstream acknowledgment (`downstream_idempotency_propagated`; honored/exactly-once only on explicit adapter `True`)

## Proof actually run (local; no hosted CI wait)

```bash
export PYTHONPATH="packages/core:packages/gateway:packages/tool_runtime:packages/eval_runner:packages/contracts:packages/publisher:packages/librarian_domain:packages/mcp_server:packages/client:packages/skill_runtime:."
export LINKSKILLS_EVAL_RUNNER_ISSUER_KEY=linkskills-local-eval-runner-issuer-key-not-for-production
export LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven
python3 -m pytest -q
# 180 passed, 4 skipped
python3 -m pytest tests/migrations/test_rls_actor_org_ephemeral.py -q
# 5 passed
python3 -m pytest tests/gateway/test_wave8_fencing_and_hashing.py -q
# 7 passed
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
