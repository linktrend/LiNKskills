# Handoff — issue 376 release-gate path

**Date:** 2026-09-17
**Branch:** `issue/376-define-and-automate-the-release-profile-promotio`
**Role:** implementer

## What landed

- `profiles.release.commands` is a short non-mutating compile + `secret_scan` list.
- `scripts/gitops/run_delivery_profile.py` accepts the `release` boundary.
- `scripts/gitops/release_gate.py` writes and verifies identity-bound evidence.
- Delivery controller / promotion receipt gate consume that evidence when present
  and still refuse a full-suite rerun.
- Trusted workflow: `.github/workflows/linktrend-release-gate.yml`.
- Contract: `docs/contracts/RELEASE-GATE.md`.
- Tests: `tests/gitops/test_release_gate.py`.

## Not done here

- No implementer PR, merge, promotion, protection change, or Bugbot request.
- Phase Packager/Coordinator remains the PR opener.
