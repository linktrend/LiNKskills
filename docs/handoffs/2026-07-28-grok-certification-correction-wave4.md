# Correction Handoff Wave 4 — Cryptographic Auth Authenticity

**Status:** Provisional Grok correction report for independent Codex re-verification. **Do not self-certify. Do not merge PR #22. Do not start the multi-day Cursor canary. Do not deploy.**

**Date:** 2026-07-28  
**Executor:** Cursor Local Agent (Grok 4.5 High) — original issue/21 owner  
**Issue:** https://github.com/linktrend/LiNKskills/issues/21  
**PR:** https://github.com/linktrend/LiNKskills/pull/22  
**Branch:** `issue/21-linkskillsdevelopmentplan01`  
**Plan hash:** `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`  
**Prior corrections:** waves 1–3 under `docs/handoffs/2026-07-28-grok-certification-*.md`

## Problem

Production `PlatformClaimsVerifier` previously accepted unsigned `platform.<base64url(JSON)>` tokens. Gateway/MCP instantiated that verifier by default, so any caller who could reach the surface could mint arbitrary AuthClaims.

## Wave 4 corrections

1. **Isolated unsigned decoder** as `LocalUnsignedClaimsVerifier` (explicit local-test-only).
2. **Unsigned tokens allowed only** when `LINKSKILLS_AUTH_MODE=local-test` or an explicit local-test verifier is injected.
3. **Production `PlatformClaimsVerifier`** requires an injected Platform-approved `PlatformTokenAuthenticator` that cryptographically authenticates tokens; it rejects unsigned `platform.<b64 JSON>` and raw JSON bearers.
4. **Fail closed:** Gateway/MCP startup/`resolve_claims_verifier()` raises `AuthConfigurationError` when production authenticator/config (`LINKSKILLS_PLATFORM_AUTHENTICATOR`) is unavailable — never falls back to unsigned.
5. **`mint_platform_token` moved** to `auth_testing` only; removed from package-root exports.
6. **`LINKSKILLS_CANARY` cannot use unsigned/local-test auth**; requires production cryptographic verification of a signed bearer.
7. **Adversarial tests** cover: self-minted unsigned canonical bearer, raw JSON bearer, fake token, wrong issuer, wrong audience, expired, revoked, wrong operation, tampered signature, missing production authenticator.
8. **Frozen claim schema unchanged** (`platform.auth-claims/1.0.0` hashes unchanged). This wave is authenticity, not field renaming.
9. **No Platform signing keys invented** in this repo; production expects Platform to supply the authenticator module via env. Tests use an explicitly labeled local-test HMAC helper only.

## Source-of-truth docs updated

- `docs/contracts/frozen/platform-auth-claims-v1.0.0.CONSUMER-PIN.md`
- `docs/OPEN-ISSUES.md` §4
- `docs/LINKSKILLS-TECHNICAL-PRD.md` (auth section)
- `docs/integrations/openclaw/HANDOFF.md`
- `configs/fragments/cursor-skills-canary.mcp.json.example`

## Proof actually run

```bash
export PYTHONPATH="packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:."
.venv/bin/python -m unittest discover -s tests/skill_runtime -v
# 6 passed
.venv/bin/python -m pytest \
  tests/contracts tests/core tests/publisher \
  tests/eval_runner tests/tool_runtime \
  tests/gateway tests/mcp_server tests/client \
  tests/librarian_domain tests/migrations -q
# 111 passed
python3 validator.py --repo-root . --scan-all
python3 scripts/build-catalog-index.py --check
python3 scripts/check-service-ownership.py
```

## Intentionally not done

- PR #22 merge
- Multi-day Cursor canary
- Deploy / live Platform issuer wiring
- Inventing or committing Platform production signing keys
- Modifying LiNKplatform
- Self-certification

## Return path

Return this wave-4 correction handoff to the **LiNKskills Codex verifier** for independent re-verification. Keep PR #22 open and unmerged until that pass.
