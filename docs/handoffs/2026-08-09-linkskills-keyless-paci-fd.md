# Handoff — LiNKskills keyless PACI inherited descriptor

**Date:** 2026-08-09 Asia/Taipei
**Branch:** `feature/keyless-paci-fd`
**Start SHA:** `b94657a`
**Status:** Implementation validated; ready for review.

## Purpose

Allow the LiNKskills PACI client to receive its EC P-256 private key through
one inherited file descriptor without creating a persistent key file, while
preserving the existing private-key file configuration.

## Changes

- Added `LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FD` as the alternative to
  `LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE`.
- Enforced exactly one key source, an integer descriptor `>= 3`, and an open
  descriptor before client construction.
- Read the inherited descriptor once with a 64 KiB bound and close it through
  `os.fdopen(..., closefd=True)` on success and read/parse failure.
- Preserved PEM, EC, and P-256 validation with generic redacted failures.
- Kept status diagnostics free of key paths, descriptor values, tokens, and key
  bytes; source indicators are booleans.
- Updated MCP proxy and server wording to describe both supported key sources.

## Validation

- `PYTHONPATH=packages/client:packages/mcp_server python3 -m pytest -q tests/client/test_paci_token_client.py` — 25 passed.
- Full package-path suite under Python 3.13 — 536 passed, 5 skipped, 189 subtests passed.
- MCP/config compatibility tests — 24 passed.
- `python3 -m compileall` on touched Python files — passed.
- `git diff --check` — passed.
- `python3 scripts/check-service-ownership.py` — passed.

The system Python 3.9 full suite was not compatible with the repository’s
Python `>=3.11` package metadata; the supported Python 3.13 rerun passed.

## Boundaries

- No cloud, runtime, Secret Manager, Supabase, live service, or Keychain access.
- No OpenClaw parent `pass_fds` implementation.
- No credential values or key material are included in this handoff.

## Remaining work

Review and merge the PR into `development`; the corresponding parent launcher
must separately provide the inherited descriptor.
