# Correction Handoff Wave 2 — Frozen Auth Claims + Deterministic Certification

**Status:** Provisional Grok correction report for independent Codex re-verification. **Do not self-certify. Do not merge PR #22. Do not start the multi-day Cursor canary.**

**Date:** 2026-07-28  
**Executor:** Cursor Local Agent (Grok 4.5 High) — original issue/21 owner  
**Issue:** https://github.com/linktrend/LiNKskills/issues/21  
**PR:** https://github.com/linktrend/LiNKskills/pull/22  
**Branch:** `issue/21-linkskillsdevelopmentplan01`  
**Prior correction:** `docs/handoffs/2026-07-28-grok-certification-path-correction.md` (wave 1; partially superseded below)

## Wave 2 corrections

1. Consumed frozen Platform contract `platform.auth-claims/1.0.0` from `@linktrend/platform-contracts@0.2.1`:
   - schema bytes SHA-256 `b0397cdf34e76ab0986c6d223ecb6c3c66d619ea59557f78cd45c0c015ff50fb`
   - contentHash `6bf49618d846662976886f57d5d468f73a08ab1a6574968f68833d82429db251`
   - consumer pin: `docs/contracts/frozen/platform-auth-claims-v1.0.0.CONSUMER-PIN.md`
2. Production verifier requires exact contract version + Platform actor-kind enum; rejects snake_case, unknown fields, `fake.*`, and `actorKind: "agent"`.
3. Expired-fixture proof uses injected clock (`now=` / fixture `context.now`), not a permanently valid credential.
4. Certification fails closed when `skill_release_hash` is unset/placeholder/missing/mismatched vs the immutable evaluated release.
5. `execution_profile_hash` is deterministic (no temp workspace paths, absolute repo paths, timestamps, UUIDs, or machine env in profile identity).
6. Individual receipts may still carry environment/timestamps/UUIDs; repeated clean runs keep identical suite/release/profile hashes.
7. Adversarial tests cover unset release, mismatched release, fabricated receipts, and profile stability.
8. Canary regenerated against immutable skill-release tree `evidence/phase3/fixtures/canary-echo/skill-release/`.

## Withdrawn prior claims (wave 1)

| Claim | Value | Status |
|---|---|---|
| profile_hash | `67f17eb8a5c2301b709385c5897fca0367e290d4d6327508c1acd52527668a32` | **withdrawn** (non-deterministic / release unset) |
| receipt echo-hello | `121d8ef64c8c578bd08a4a22ad11999e47b2162cb9bbb2207cf3892f89bcc8a1` | **withdrawn** |
| receipt echo-json | `fbb425a52fd28b3a4c0614dea5e367603b1d333b0d28ceb52e9b61953d38009a` | **withdrawn** |

## Current canary execution receipts (wave 2)

| Field | Value |
|---|---|
| suite_hash | `a564173690b0745271d34991c69c8234039305501a4fccedaadf0954ac71a50a` |
| skill_release_hash | `skill-release:036f019dc24542ebc4f68bd0502178d5be5587abe049fb9661adeb2923fcb379` |
| profile_hash | `288543a4379181fc6f5b47299c679c5ca7b3df6130dcf8b481b9188c83346a7b` |
| receipt echo-hello | `9b6d827046f8b916c114e05dc184ba403be36a1d567f65537defed8a641cecfe` |
| receipt echo-json | `e8a1cfc998e6807ecc63b31d87702721d4d6d510436291f6e148d80ce5bc025e` |

Evidence: `evidence/phase3/canary-echo-cli.json`, `evidence/phase3/canary-echo-cli.txt`.

## Commands actually run

```bash
export PYTHONPATH="packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:."
.venv/bin/python -m pytest tests/eval_runner tests/tool_runtime tests/gateway tests/mcp_server tests/client tests/migrations tests/core tests/contracts tests/publisher tests/librarian_domain tests/skill_runtime -q
# 86 passed

TMP=$(mktemp /tmp/canary-echo-XXXXXX.json)
.venv/bin/python -m linkskills_eval_runner run \
  evidence/phase3/fixtures/canary-echo/eval-suite.yaml \
  --skill-dir evidence/phase3/fixtures/canary-echo/skill-release \
  -o "$TMP"
# certified=true; suite/release/profile stable across two runs

python3 validator.py --repo-root . --scan-all
python3 scripts/build-catalog-index.py --check
python3 scripts/check-service-ownership.py
```

## OpenClaw owner notice

Corrected Platform AuthClaims pin + Skills MCP fragment/fixtures are ready for OpenClaw repinning and countersign. See:
- `docs/contracts/frozen/platform-auth-claims-v1.0.0.CONSUMER-PIN.md`
- `docs/integrations/openclaw/HANDOFF.md`
- `configs/fragments/openclaw-skills.mcp.json.fragment`

LiNKskills will not edit OpenClaw/Lisa internals.

## Intentionally not done

- PR #22 merge
- Multi-day Cursor canary
- Live Platform migration apply / live issuer
- Self-certification of this handoff

## Amendment 2026-07-28 — wave 3

Wave 2 AuthClaims/profile claims remain. Wave 3 adds buffer/flush fail-closed behavior, receipt-bound librarian/core certification, MCP identity hardening, run-start gates, fragment PYTHONPATH, and README CI command alignment. See `docs/handoffs/2026-07-28-grok-certification-correction-wave3.md`. Still provisional for Codex re-verification — do not merge or start the multi-day Cursor canary.

## Ask

Return to the **LiNKskills Codex verifier** for independent re-verification against plan hash `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88` and Platform freeze record.
