# Correction Handoff Wave 3 — PR #22 Unresolved Review Threads

**Status:** Provisional Grok correction report for independent Codex re-verification. **Do not self-certify. Do not merge PR #22. Do not start the multi-day Cursor canary.**

**Date:** 2026-07-28
**Executor:** Cursor Local Agent (Grok 4.5 High) — original issue/21 owner
**Issue:** https://github.com/linktrend/LiNKskills/issues/21
**PR:** https://github.com/linktrend/LiNKskills/pull/22
**Branch:** `issue/21-linkskillsdevelopmentplan01`
**Plan hash:** `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`
**Prior corrections:**
- Wave 1: `docs/handoffs/2026-07-28-grok-certification-path-correction.md`
- Wave 2: `docs/handoffs/2026-07-28-grok-certification-correction-wave2.md`

## Wave 3 corrections (all 10 unresolved actionable threads)

| # | Thread | Fix |
|---|---|---|
| 1 | Offline buffer wrong shape | `compat.record_invocation` buffers mapped `skills_feedback_submit` payload (`skill_id`/`kind`/`outcome`/`notes`/`run_id`), never legacy `skill`/`status`/`summary` alone |
| 2 | Flush counts HTTP errors success | `SkillsGatewayClient._request` raises on HTTP 4xx/5xx; flush keeps events and increments `failed`, never `written` |
| 3 | Librarian certifies thin evidence | `interpret_eval_evidence` uses `evaluate_certification_evidence`; non-empty `case_results` alone never certifies |
| 4 | Feedback ignores run ownership | `op_skills_feedback_submit` calls `_get_run` when `run_id` present (actor/org binding) |
| 5 | MCP fragments omit tool_runtime | Cursor/Codex/OpenClaw fragments include `packages/tool_runtime` (+ `packages/core`) on PYTHONPATH |
| 6 | README test command misses pytest | README Core commands now match CI pytest internal-launch suite set |
| 7 | MCP body claims mint identity | Removed caller `actor_claims` → `mint_platform_token` path; only Authorization or injected `default_actor` |
| 8 | Canary env var unused | `LINKSKILLS_CANARY=1` requires Platform-verifiable `LINKSKILLS_CANARY_AUTHORIZATION` / `GATEWAY_TOKEN`; refuses start without it |
| 9 | Runs start on draft skills | `op_skills_run_start` rejects non-`usable`, release/profile hash mismatch, incompatible runtime profiles |
| 10 | Core accepts bare output strings | Core certification is receipt-bound: sealed executor receipts only; bare outputs/tool_traces/artifacts refused |

## Adversarial tests added

- Caller-minted MCP `actor_claims` rejected (`auth_claims_mint_forbidden` / `auth_missing`)
- Wrong-owner feedback on another actor’s run → `auth_forbidden`
- HTTP 403 buffer flush → `written=0`, event retained with attempts++
- Draft / release-mismatch / incompatible-profile run starts rejected
- Fabricated receipt hash + bare output/tool_traces refused by core + librarian

## Proof actually run (this wave)

```bash
export PYTHONPATH="packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:."
.venv/bin/python -m unittest discover -s tests/skill_runtime -v
# 6 passed
.venv/bin/python -m pytest \
  tests/contracts tests/core tests/publisher \
  tests/eval_runner tests/tool_runtime \
  tests/gateway tests/mcp_server tests/client \
  tests/librarian_domain tests/migrations -q
# 95 passed
python3 validator.py --repo-root . --scan-all
python3 scripts/build-catalog-index.py --check
python3 scripts/check-service-ownership.py
```

## Intentionally not done

- PR #22 merge
- Multi-day Cursor canary start
- Live Platform migration apply / live issuer
- Self-certification of this handoff

## Return path

Return this wave-3 correction handoff to the **LiNKskills Codex verifier** for independent re-verification. Keep PR #22 open and unmerged until that pass.

## Amendment 2026-07-28 — wave 4

Superseded on authenticity: unsigned production AuthClaims decoding is withdrawn. See `docs/handoffs/2026-07-28-grok-certification-correction-wave4.md`.
