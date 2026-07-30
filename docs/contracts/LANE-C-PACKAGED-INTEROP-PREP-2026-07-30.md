# PROVISIONAL PREP ONLY — Lane C packaged interoperability (Wave 3)

**Status:** `AWAITING_CODEX_CERTIFIED_PLATFORM_REPIN`
**Authority:** none — scout prep for Wave-3/4 handoff; not a consumer pin; not a freeze record.
**Date:** 2026-07-30 (Asia/Taipei)

## Gate (do not skip)

| Field | Value |
|---|---|
| Failed Platform tip (do **not** consume / do **not** repin) | `83501b11b78b0c5f46a5c5ef23f48de9f1317468` (prior); `ca0274178cbba0dd07e665a4d66b4ceb92c0ac09` (current failed IV) |
| Skills frozen envelope (unchanged) | `platform.auth-token-envelope/0.1.0` |
| Skills PACI contracts package (unchanged) | `@linktrend/platform-contracts@0.3.0` |
| Skills frozen Platform HEAD pin (unchanged) | `0455846487d0b8c583859060ba8b4be70e7f0b48` |
| Consumer pin | `docs/contracts/frozen/platform-auth-token-envelope-v0.1.0.CONSUMER-PIN.md` |
| Code constants | `packages/gateway/linkskills_gateway/paci_types.py` |

Do **not** invent a future SHA. Do **not** claim interop ran. Do **not** bump package versions from this note.

## Observed local Platform checkout (report only)

At Wave-4 evidence time, `/Users/linktrend/Projects/LiNKplatform` HEAD was
`ca0274178cbba0dd07e665a4d66b4ceb92c0ac09` (branch `issue/LP-01-linkplatformdevelopmentplan01`).
That local HEAD failed independent verification and is **not** Skills authority;
do not repin to it.

## Packaged interoperability checklist (deferred until Codex-certified tip)

When Platform Codex certifies a corrected descendant, a later Skills continuation should:

1. Record the **exact** certified Platform HEAD (full SHA) — only from certification evidence.
2. Confirm published identity still matches (or explicitly supersedes with new freeze): envelope `0.1.0` / `@linktrend/platform-contracts` version + tarball integrity.
3. Byte-compare schema + fixtures from the **packaged** Platform artifact against Skills vendored copies and `paci_types.py` hashes (`7173b9f9…463eed` schema bytes; `9335b185…890a12` contentHash; AuthClaims hashes unchanged unless freeze says otherwise).
4. Run Skills frozen-fixture + adversarial suites against those packaged bytes (`tests/gateway/test_paci_frozen_fixtures.py`, `tests/gateway/test_paci_adversarial.py`).
5. Update consumer pin + `PLATFORM_HEAD_PACI` only after those proofs pass — never from an uncertified tip.

## Explicit non-claims

- No packaged interop run in this scout.
- No tooling script added; no hash or version mutation.
- No Platform edits; no Skills package bumps; no commit/push from this prep.
