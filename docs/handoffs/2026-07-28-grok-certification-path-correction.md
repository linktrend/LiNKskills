# Correction Handoff — Invalid Certification Path Replacement (issue #21)

**Status:** Provisional Grok correction report for independent Codex re-verification. **Do not merge PR #22 from this handoff alone.** Do **not** begin the multi-day Cursor canary until certification + Platform gates pass.

**Date:** 2026-07-28
**Executor:** Cursor Local Agent (Grok 4.5 High) — original issue/21 implementation owner
**Issue:** https://github.com/linktrend/LiNKskills/issues/21
**PR (do not merge):** https://github.com/linktrend/LiNKskills/pull/22
**Branch:** `issue/21-linkskillsdevelopmentplan01`
**Repo:** `/Users/linktrend/Projects/LiNKskills`
**Prior provisional handoff:** `docs/handoffs/2026-07-27-grok-linkskills-internal-launch-implementation.md` (**superseded on certification/auth claims**)
**Closed session:** `docs/agent-sessions/completed/20260727-cursor-grok-issue21-linkskillsdevelopmentplan01.md`

## Why this correction exists

The 2026-07-27 canary certification was **invalid**: suite-authored `observed_output` was treated as executed evidence, and `skills_tool_invoke` could return `live_echo` without a real adapter invocation. That path cannot authorize certification.

## Corrections implemented

1. **Real Eval Runner executor** — `packages/eval_runner/linkskills_eval_runner/executor.py` runs `packaged_tool` / `command` cases in an isolated workspace and captures exit status, stdout/stderr, artifacts, and tool calls.
2. **Suite fixtures are golden only** — suite `observed_output` / `fixture_output` never count as observed execution evidence (`INVALID_EMBEDDED_OUTPUT` / non-certifiable).
3. **Immutable execution receipts** — `receipt.py` seals case + suite_hash + skill_release_hash + execution_profile_hash + tool call hashes + environment/toolchain + stdout/stderr hashes. Certifier requires `evidence_source == "executor"` and valid receipts.
4. **Adversarial tests** — `tests/eval_runner/test_adversarial_certification.py` proves embedded answers / fabricated outputs / fabricated artifact metadata cannot certify.
5. **Genuine canary** — `evidence/phase3/fixtures/canary-echo/eval-suite.yaml` v0.2.0 invokes packaged `tools/text-echo`. Invalid prior certified claim replaced by new receipt-bound evidence.
6. **`skills_tool_invoke`** — dry_run resolves; `dry_run=false` requires exact version+hash, authorized write, real `invoke_tool`, mode `live_adapter` (never `live_echo`).
7. **Platform claims** — `PlatformClaimsVerifier` + vendored `packages/contracts/fixtures/platform-claims/`; `fake.*` confined to `auth_testing`.
8. **Migration/RLS package tests** — `tests/migrations/` structural only; **no live apply**.

## Execution receipts (canary, regenerated 2026-07-28)

| Field | Value |
|---|---|
| suite_hash | `a564173690b0745271d34991c69c8234039305501a4fccedaadf0954ac71a50a` |
| profile_hash | `67f17eb8a5c2301b709385c5897fca0367e290d4d6327508c1acd52527668a32` |
| receipt echo-hello | `121d8ef64c8c578bd08a4a22ad11999e47b2162cb9bbb2207cf3892f89bcc8a1` |
| receipt echo-json | `fbb425a52fd28b3a4c0614dea5e367603b1d333b0d28ceb52e9b61953d38009a` |
| certify_reason | certified: executor receipts bind case, release, tool, profile, environment/toolchain, and collected evidence |
| evidence JSON SHA-256 | `554289972ab6b0dcf6e1decd7c7ee1e304bfae26f414e449ebb27a4a2698eb85` |

Human summary: `evidence/phase3/canary-echo-cli.txt`
Machine evidence: `evidence/phase3/canary-echo-cli.json`

**Invalid prior claim (do not trust):** previous `profile_hash` `70b6cc98…053d` / suite-authored observed_output path. Treat as withdrawn.

## Tests actually run

```bash
export PYTHONPATH="packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:."
.venv/bin/python -m pytest tests/eval_runner tests/tool_runtime tests/gateway tests/mcp_server tests/client tests/migrations tests/core tests/contracts tests/publisher tests/librarian_domain tests/skill_runtime -q
# Result: 76+ passed (after core suite-authored refusal test)
.venv/bin/python -m linkskills_eval_runner run evidence/phase3/fixtures/canary-echo/eval-suite.yaml -o evidence/phase3/canary-echo-cli.json
# certified=true with receipt_hashes above
```

## Codex re-verification checklist

1. Confirm suite YAML has **no** suite-authored `observed_output`/`fixture_output` used as evidence.
2. Re-run canary CLI; verify receipt hashes bind tool `source_hash` + env + stdout/stderr.
3. Confirm adversarial tests fail closed without real execute.
4. Confirm `skills_tool_invoke` dry_run=false never emits `live_echo`.
5. Confirm Gateway rejects `fake.*` tokens; accepts Platform fixtures.
6. Confirm migration tests do not apply SQL live.
7. Do **not** start multi-day Cursor canary until this certification path and Platform gates are accepted.

## Intentionally not done

- PR #22 merge
- Live Platform migration apply
- Multi-day Cursor canary stages 3–8
- Live Platform issuer wiring beyond consuming the claim schema/fixtures

## Ask of Principal / Codex

Return this correction handoff to the **LiNKskills Codex verifier** for independent re-verification against plan hash `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`. Keep PR #22 open and unmerged until that pass.

---

## Amendment 2026-07-28 — wave 2 supersession

Wave 1 profile/receipt claims are **withdrawn**. See `docs/handoffs/2026-07-28-grok-certification-correction-wave2.md` for frozen AuthClaims pin, immutable skill-release binding, and deterministic profile hashes.

## Amendment 2026-07-28 — wave 3 supersession

Additional fail-closed corrections for buffer/flush, librarian/core receipt-bound certification, MCP identity minting, run-start gates, fragments, and README CI commands. See `docs/handoffs/2026-07-28-grok-certification-correction-wave3.md`. Still provisional — do not merge PR #22; do not start the multi-day Cursor canary; return to Codex verification.

## Amendment 2026-07-28 — wave 4 supersession

Unsigned production AuthClaims decoding is withdrawn. Production requires Platform-approved cryptographic authenticator injection; local-test unsigned path is explicit only. See `docs/handoffs/2026-07-28-grok-certification-correction-wave4.md`.
