# Correction Handoff Wave 9 — Codex independent findings

**Status:** Provisional Grok correction report for independent Codex re-verification. **Do not self-certify. Do not merge PR #22. Do not start the multi-day Cursor canary. Do not deploy. Do not apply live Platform migrations.**

**Date:** 2026-07-29
**Executor:** Cursor Local Agent (Grok 4.5 High) — original issue/21 owner
**Issue:** https://github.com/linktrend/LiNKskills/issues/21
**PR:** https://github.com/linktrend/LiNKskills/pull/22
**Branch:** `issue/21-linkskillsdevelopmentplan01`
**Base head for this wave:** `409a24dbcf7ef30173022c2557ccd985ad0739ab`
**Wave-9 code tip (exact clean pushed head before handoff pin):** `8742bf79f4c6013abf9bcd07a27286ce905b17cb`
**Plan hash:** `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`

## Wave 9 corrections (Codex findings)

1. **Service-state atomicity** — DB-owned writes defer `SkillsGatewayService` cache/list publishes via a mutation batch. Store is authoritative during the atomic transaction; caches publish only after successful commit. Crash injection after handler mutation / before idempotency complete rolls back SQLite and aborts the batch so service-visible state matches the DB. Retry yields a single logical mutation/event.

2. **External-result fencing** — `complete_side_effect_intent` validates the **current idempotency reservation** fence (and active `reserved` status) atomically with intent ownership (`request_hash`), not only the token stored on the intent row. Displaced workers cannot record/overwrite results after stale reclaim.

3. **Stable downstream idempotency** — Downstream keys derive from actor/org/operation/idempotency key/canonical request hash (`lskills-downstream:<hash>`), never the renewable fence token. Keys propagate through `skills_tool_invoke` → `invoke_tool` → adapter env `LINKSKILLS_DOWNSTREAM_IDEMPOTENCY_KEY`. Reclaim preserves durable side-effect results and reconciles without overwrite. Adapters that cannot prove exactly-once keep `external_side_effect_at_least_once` (no exactly-once claim).

## Preserved

- Shared canonical hashing / launch-target profile work from wave 8 (verified)
- macOS confinement honesty from wave 7
- AuthClaims pin and prior authorization/tenant/receipt controls
- PR remains draft; no merge / hosted CI poll / canary / deploy / live migrations

## Proof actually run (local; no hosted CI wait)

```bash
export PYTHONPATH="packages/core:packages/gateway:packages/tool_runtime:packages/eval_runner:packages/contracts:packages/publisher:packages/librarian_domain:packages/mcp_server:packages/client:packages/skill_runtime:."
export LINKSKILLS_EVAL_RUNNER_ISSUER_KEY=linkskills-local-eval-runner-issuer-key-not-for-production
export LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven
python3 -m pytest -q
# 173 passed, 4 skipped
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

Re-verify against this branch tip and the three findings above. Treat this as a correction packet, not certification.
