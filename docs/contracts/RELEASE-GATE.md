# Release-gate evidence contract

**Status:** Binding for LiNKskills promotion.
**Related:** `docs/contracts/DELIVERY-MODES.md`, `scripts/gitops/release_gate.py`, `scripts/gitops/delivery_controller.py`.

## Purpose

Staging and main promotion reuse a sealed **full-suite receipt**. They must also
present a short, identity-bound **release** profile result. An empty command
list is not a passing release gate.

## Commands

Repository-owned release commands live in `.ide-development/config/delivery.json`
under `profiles.release.commands`. They must be:

- non-empty argv arrays
- non-mutating (no `git` / `rm` / `install` / apply helpers)
- free of `run_delivery_profile.py full`

The current LiNKskills release profile compiles the promotion scripts and runs
`python3 scripts/gitops/secret_scan.py`.

## Workflow

`.github/workflows/linktrend-release-gate.yml` (`Linktrend Release Gate`) runs
that profile against the exact Phase or `promote/*` commit. It does not rerun
Full. It writes `release-gate-evidence.json`.

## Evidence

Kind: `release-gate-evidence` (`schemaVersion` 1). Required bindings:

- `testProfile=release`
- `fullSuiteInvoked=false`
- `identity` / `identityDigest` (`repository`, `headCommit`, `gitTree`,
  `dependencyDigest`, `profileDigest`, `workflowDigest`)
- non-empty `commands`
- `ok=true`, `complete=true`, `failedCount=0`, `workspaceMutated=false`

Pass this artifact to the delivery controller as `--release-json`. Missing,
empty, stale, or failed evidence is `HOLD`. Status-only payloads remain readable
for older fixtures; production promotions should supply this evidence file.

Independent reviewers should check:

```bash
python3 scripts/gitops/release_gate.py verify \
  --evidence release-gate-evidence.json \
  --identity identity.json \
  --require
```
