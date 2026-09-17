# Correction Handoff Wave 12 — Codex independent findings

**Status:** Provisional Grok correction report for independent Codex re-verification. **Do not self-certify. Do not merge PR #22. Do not start the multi-day Cursor canary. Do not deploy. Do not apply live Platform migrations.**

**Date:** 2026-07-29
**Executor:** Cursor Local Agent (Grok 4.5 High) — original issue/21 owner
**Issue:** https://github.com/linktrend/LiNKskills/issues/21
**PR:** https://github.com/linktrend/LiNKskills/pull/22
**Branch:** `issue/21-linkskillsdevelopmentplan01`
**Base head for this wave:** `57d245b74b08d34bdf58f3f9b693b681260ca903`
**Wave-12 code tip (exact clean pushed head before handoff pin):** `5d35e102b7853a0c8ed38f2baedc1471575cf280`
**Plan hash:** `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`

## Wave 12 corrections (Codex findings)

1. **Fail-closed write idempotency keys** — Every `WRITE_OPERATIONS` member requires a validated non-empty idempotency key via `normalize_idempotency_key` **before** selecting DB-owned vs external-side-effect handling, invoking any handler, creating an external intent, or mutating persistent/cached state. Rejects missing, null, empty, whitespace-only, leading/trailing whitespace, non-string, malformed (`[^A-Za-z0-9._:-]`), and oversized (`>128`) keys with `idempotency_key_required` / `idempotency_key_invalid` (HTTP 400).

2. **Ungated write fallback removed** — Write operations no longer fall through to a bare handler when a key is absent/invalid. Unsupported write classifications fail closed. Read-only operations remain key-optional.

3. **Surface proofs** — `tests/gateway/test_wave12_idempotency_key_required.py` parameterizes every `WRITE_OPERATIONS` member × invalid-key case through direct service dispatch, HTTP Gateway, and MCP. Each rejection leaves DB runs/events/idempotency/side-effect intents and service caches unchanged; tool adapters are not invoked.

4. **Retained downstream propagation** — Confined executor allowlists `LINKSKILLS_DOWNSTREAM_IDEMPOTENCY_KEY` so mandatory write keys continue wave-9/10 stable downstream propagation under live confined invoke.

## Preserved

- Waves 8–11: hashing, fencing, stable downstream keys, honest ack, MutationContext, commit-through-publish serialization, isolation, RLS

## Proof actually run (local; no hosted CI wait)

```bash
export PYTHONPATH="packages/core:packages/gateway:packages/tool_runtime:packages/eval_runner:packages/contracts:packages/publisher:packages/librarian_domain:packages/mcp_server:packages/client:packages/skill_runtime:."
export LINKSKILLS_EVAL_RUNNER_ISSUER_KEY=linkskills-local-eval-runner-issuer-key-not-for-production
export LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven
python3 -m pytest -q
# 186 passed, 4 skipped
python3 -m pytest tests/migrations/test_rls_actor_org_ephemeral.py tests/gateway/test_wave8_fencing_and_hashing.py -q
# 12 passed
python3 scripts/validate_skills.py --scan-all
python3 scripts/build-catalog-index.py --check
python3 scripts/check-service-ownership.py
git diff --check
```

## Explicit non-actions

- Did not poll/rerun hosted CI or Bugbot, change PR readiness, merge, apply migrations, start canaries, deploy, or perform live actions.
- Did not self-certify.

## Ask of LiNKskills Codex

Re-verify against this branch tip and the fail-closed write idempotency key finding above. Treat this as a correction packet, not certification.
