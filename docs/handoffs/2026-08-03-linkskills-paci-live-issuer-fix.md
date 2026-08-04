# LiNKskills PACI live issuer policy fix

**Status:** Local unit proof complete; branch pushed; **not** merged; **no** staging/prod deploy
**Packet:** `SKILLS-PACI-LIVE-ISSUER-FIX`
**Executor:** Cursor Grok 4.5 High
**Date:** 2026-08-03
**Branch:** `dev/cloudcursor/SKILLS-PACI-LIVE-ISSUER-FIX`
**Start SHA:** `a977b266880adcfb5b1be81b7923afbf595e364d` (`origin/development`)

## Defect

Live Mac Mini canary: `PaciJwtAuthenticator` correctly verified
`LINKSKILLS_PACI_ISSUER` (e.g. `https://linktrend-mini.tailf7e13a.ts.net:9443`),
then `resolve_claims_verifier()` constructed `PlatformClaimsVerifier` with
default `expected_issuer='linkplatform-issuer'`, denying the token after
cryptographic success.

## Fix

In `resolve_claims_verifier`, when `expected_issuer` is not explicitly supplied:

1. Prefer `authenticator.issuer` (PACI pin).
2. Else prefer `LINKSKILLS_PACI_ISSUER` from environ.
3. Else keep `PlatformClaimsVerifier` default (`linkplatform-issuer`) for
   non-PACI authenticators.

Explicit `expected_issuer` (including `None` to skip the duplicate policy
check) still wins. Fail-closed crypto + AuthClaims policy retained.

## Tests

- `ResolveClaimsVerifierPaciIssuerPolicyTests` in
  `tests/gateway/test_paci_adversarial.py`
  - Live canary issuer accepted via `resolve_claims_verifier` without policy kwarg
  - Wrong issuer still fails cryptographically
  - Non-PACI HMAC retains default issuer

## Non-claims

- No merge to `development` / `staging` / `main`
- No staging/runtime/cloud/database/production changes
- Does not claim live Mac Mini canary re-proof after deploy

## Rollback

Revert the fix commit on this branch (or close the PR without merge). No live
action required.
