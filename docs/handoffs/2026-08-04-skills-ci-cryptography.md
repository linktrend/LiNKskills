# LiNKskills CI cryptography dependency correction

- Start SHA: `5c9ec69dcb2f16459d7577ee97bfa00b379e3529`
- Branch: `dev/minicodex/WP-0-ci-cryptography`
- Scope: CI test-environment dependency installation only.
- Root cause: the catalog gate installed only `pyyaml` and `pytest` even though PACI gateway, client, and MCP tests import `cryptography`, which is already declared in `requirements-dev.txt`.
- Correction: install the repository's complete development-test dependency file in the CI job.
- Runtime behavior: unchanged.

## Validation

- Fresh Python 3.13 virtual environment installed `requirements-dev.txt`, including `cryptography 50.0.0`.
- Internal-launch suite: 435 passed, 4 skipped, 189 subtests passed.
- Skill-runtime suite: 53 passed, 1 skipped.
- Registry validator: passed for 54 targets (historical-ledger warnings only).
- Service ownership gate: passed for 35 services.
- `git diff --check`: passed.

Hosted CI must independently confirm the correction on the pull request before merge.
