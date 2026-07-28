# Correction Handoff Wave 5 — Codex independent findings

**Status:** Provisional Grok correction report for independent Codex re-verification. **Do not self-certify. Do not merge PR #22. Do not start the multi-day Cursor canary. Do not deploy. Do not apply live Platform migrations.**

**Date:** 2026-07-28  
**Executor:** Cursor Local Agent (Grok 4.5 High) — original issue/21 owner  
**Issue:** https://github.com/linktrend/LiNKskills/issues/21  
**PR:** https://github.com/linktrend/LiNKskills/pull/22  
**Branch:** `issue/21-linkskillsdevelopmentplan01`  
**Base head for this wave:** `30de5607bfe073ef72f0c11c0bb0813ed57a9e2b`  
**Pushed wave-5 head:** `8104756e166bb453ac5b896de66bb51c626d5513`  
**Plan hash:** `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`

## Wave 5 corrections (Codex findings 1–12)

1. **Confined fail-closed executor** — `packages/tool_runtime/linkskills_tool_runtime/confined_exec.py` used by LocalProcessAdapter + eval `execute.command`. Allowlisted env; realpath boundary + symlink-escape rejection; no shell/`bash -lc`; OS network deny when available else refuse (default) or ADR-gated unproven local-test escape; bounded time/CPU/output. Adversarial tests in `tests/tool_runtime/test_wave5_confinement.py`. Bounded ADR: `docs/adr/0009-confined-executor-network-isolation.md` (no new paid service).
2. **ServerAdapter** — explicitly disabled (`ENABLED=False`); invoke returns fail-closed error until implemented.
3. **Exact `permittedOperations`** — every Gateway/MCP read/mutation checks `ActorClaims.may_perform(operation)`; empty ops fail closed.
4. **Collision-safe durable idempotency** — all `WRITE_OPERATIONS` use store `get/put_idempotent` (SQLite UNIQUE or in-memory); race returns prior envelope.
5. **Strict schema allowlisting + redaction** — `linkskills_core.payload_guard` before feedback/trace/run-mutation persistence.
6. **Feedback/trace binding** — require accessible run for authenticated actor/org; skill_id must match run.
7. **Trusted Eval Runner provenance** — receipts seal with content hash + HMAC issuer (`LINKSKILLS_EVAL_RUNNER_ISSUER_KEY`); certification rejects self-hash-only receipts.
8. **Actor/org RLS** — foundation migration + upgrade `20260728_000006_lskills_rls_actor_org_scope.sql` with GUC helpers; ephemeral PG tests gated by `LINKSKILLS_TEST_PG_DSN` / `LINKSKILLS_TEST_PG_DOCKER=1`.
9. **Persistent Gateway/publisher/librarian** — SQLite gateway store, publisher registry transactional publish, librarian review queue store.
10. **Meta-skill/validator migration** — `scripts/validate_skills.py`; skill-architect/template/tool-architect remediated to point at package/script validators and governance scope-out.
11. **pytest.ini** — `testpaths=tests`, `norecursedirs` includes `archive`; collection guard test.
12. **AuthClaims 1.1.0 pin** — vendored schema + consumer pin; `orgId` null only for `service`; hashes `c2e8bc68…ddfa1` / `fb518834…ca567`.

## Proof actually run (local; no hosted CI wait)

```bash
export PYTHONPATH="packages/core:packages/gateway:packages/tool_runtime:packages/eval_runner:packages/contracts:packages/publisher:packages/librarian_domain:packages/mcp_server:packages/client:packages/skill_runtime:."
export LINKSKILLS_EVAL_RUNNER_ISSUER_KEY=linkskills-local-eval-runner-issuer-key-not-for-production
export LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven
python3 -m pytest -q
# 137 passed, 5 skipped (ephemeral RLS unless DSN/DOCKER explicitly enabled)
python3 scripts/validate_skills.py --scan-all
python3 scripts/build-catalog-index.py --check
python3 scripts/check-service-ownership.py
git diff --check
```

## Explicit non-actions

- Did not poll hosted CI, change PR readiness, merge, apply migrations, start canaries, deploy, alter shared Codex/OpenClaw configuration, or perform live actions.
- Did not self-certify.

## Ask of LiNKskills Codex

Re-verify against this branch tip and the twelve findings above. Treat this as a correction packet, not certification.
