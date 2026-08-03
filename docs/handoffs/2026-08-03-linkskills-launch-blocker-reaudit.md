# Handoff — Launch-blocker re-audit remediation (A/B/C)

**Date:** 2026-08-03
**Branch:** `dev/cloudcursor/skills-stage-certification`
**Tip SHA:** 
**Base tip (pre-fix):** `70a26410a071abfa74642d302a3f730bfb4a4d3d`
**Verdict:** local remediation complete; stage/shared apply remains HOLD

## Launch blockers fixed

### A — Clean-source reproducibility
- Governed allowlist hasher excludes tmp/cache/build/VCS noise.
- Darwin seatbelt profiles write under ephemeral `$TMPDIR/linkskills-confine-state/`.
- Regression: ignored tmp/cache does not change hashes; tracked drift does.
- text-echo source/tool hash: `29b179692378ba32ee244afa7f8b8017e918a158f37127e117cfe24a820f3d83`

### B — Migration fail-closed
- 000010 asserts existing immutable rows match all pinned IDs/hashes or RAISE + rollback.
- Down deletes only exact package UUID/hash pins.
- Ephemeral tests prove mismatch atomic fail + scoped down.

### C — Secret argv exposure
- `run-sealed-linux-certify.sh` uses name-only `--env LINKSKILLS_EVAL_RUNNER_ISSUER_KEY`.
- Argv-inspection regression with fake docker; key never logged/stored.

## Trust binding (post re-seal, release mode, ephemeral process-only key)

| Constant | Value |
|---|---|
| text-echo source/tool hash | `29b179692378ba32ee244afa7f8b8017e918a158f37127e117cfe24a820f3d83` |
| skill_release_hash | `skill-release:006a23b0af3abbcb9a0600c3f44bf337b89dc6cdd5be6d328097a2498a5f05bb` |
| profile_hash | `9db2d1db2663d9e3fb2a60b0ab4aaaf291aed010d155caba65798b5ecb0ec188` |
| suite_hash | `8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662` |
| sealed_evidence_sha256 | `bbaae7384cffd785b0585238174b103f213062428cf45160c9435fba660f80e0` |
| receipt echo-hello | `ec3227e77e1d19844c3d3a2d5de65520251263f228ab70a3f0bbe8a64cc8ed49` |
| receipt echo-json | `e02b150ab3915005b44d72c33687677849f27946e6191a57600960a006009005` |
| sealed image digest | `sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de` |

## Residual HOLD
- Stage DB apply still Platform-owned
- No live Lisa / VPS / shared Gateway / GSM mutation in this session
- Production issuer key remains GSM process-only
