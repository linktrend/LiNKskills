# Correction Handoff Wave 6 — Codex independent findings

**Status:** Provisional Grok correction report for independent Codex re-verification. **Do not self-certify. Do not merge PR #22. Do not start the multi-day Cursor canary. Do not deploy. Do not apply live Platform migrations.**

**Date:** 2026-07-28  
**Executor:** Cursor Local Agent (Grok 4.5 High) — original issue/21 owner  
**Issue:** https://github.com/linktrend/LiNKskills/issues/21  
**PR:** https://github.com/linktrend/LiNKskills/pull/22  
**Branch:** `issue/21-linkskillsdevelopmentplan01`  
**Base head for this wave:** `f780161cee8415bd35d7d8250f52c35e2655bbab`  
**Wave-6 tip:** *(exact SHA after this handoff push — see git log tip)*  
**Plan hash:** `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`

## Wave 6 corrections (Codex findings)

1. **Filesystem confidentiality** — `confined_exec.py` no longer uses global macOS `(allow file-read*)` alone or Linux `--ro-bind / /`. Linux: `bwrap --tmpfs /` + explicit `--ro-bind` of canonical runtime/workspace realpaths. macOS: deny `/Users`/`/home`/`/Volumes`/`/private/var/root`, re-allow workspace + EXTRA_RO realpaths (ADR 0009 documents dyld constraint). Adversarial test refuses home-file reads when isolation=`denied`.
2. **Isolation bound into signed receipt + certification** — `network_isolation` is in receipt `payload_for_hash` / seal; `sealed_executor_receipt` and `certify._receipt_valid` require `network_isolation == "denied"`. `allow_unproven` stamps `"unproven"` and cannot certify.
3. **Immutable published `(skill_id, version)`** — publisher `ON CONFLICT DO UPDATE` removed; exact-content replay idempotent; different content under same version raises.
4. **Atomic idempotency + request hash** — `reserve_idempotency` / `complete_idempotency` before mutation; key bound to canonical request hash; same key + different payload → `409 idempotency_conflict`.
5. **Recursive privacy** — nested conversation/Brain/prompt/credential/`raw_input`/`raw_output` rejected or redacted; unknown content-bearing leaves redacted (`payload_guard` + expanded `retention`).
6. **Ephemeral RLS** — fresh/upgrade/wrong-actor/wrong-org (+ GUC rollback) run when Docker is available (ephemeral host port); `LINKSKILLS_TEST_PG_DOCKER=0` is the explicit skip. Proven in this wave: **5 passed**.
7. **`validator.py` schema routing** — validates canonical v0.1 Skill Pack / eval / tool / execution-profile via `linkskills_contracts.validate_instance`; contract fixtures exercised on `--scan-all` (not regex-only wrap).
8. **Preserved** — AuthClaims 1.1.0 pin; authorization / tenant-binding / receipt-signing / pytest-discovery / ServerAdapter disabled controls from prior waves.

## Proof actually run (local; no hosted CI wait)

```bash
export PYTHONPATH="packages/core:packages/gateway:packages/tool_runtime:packages/eval_runner:packages/contracts:packages/publisher:packages/librarian_domain:packages/mcp_server:packages/client:packages/skill_runtime:."
export LINKSKILLS_EVAL_RUNNER_ISSUER_KEY=linkskills-local-eval-runner-issuer-key-not-for-production
export LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven
python3 -m pytest -q
# 154 passed (includes 5 ephemeral RLS under Docker)
python3 scripts/validate_skills.py --scan-all
python3 scripts/build-catalog-index.py --check
python3 scripts/check-service-ownership.py
git diff --check
```

## Explicit non-actions

- Did not poll hosted CI, change PR readiness, merge, apply migrations, start canaries, deploy, alter shared Codex/OpenClaw configuration, or perform live actions.
- Did not self-certify.

## Ask of LiNKskills Codex

Re-verify against this branch tip and the eight findings above. Treat this as a correction packet, not certification.
