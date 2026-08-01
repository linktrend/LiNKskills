# LiNKskills repin to certified Platform candidate — handoff

**Status:** `REPIN_COMPLETE` — local/fake conformance only; stage/prod **not** claimed
**Packet:** `SKILLS-REPIN-CERTIFIED-PLATFORM`
**Executor:** Cursor Grok 4.5 High lane leader + lanes A/B/C
**Date / time:** 2026-08-01 Asia/Taipei
**Branch:** `dev/cloudcursor/SKILLS-REPIN-CERTIFIED-PLATFORM`
**Durable coordination head (LiNKbrain):** `0d6b97634953a76075079e50b875b572762c0c54`

## Exact heads

| Field | SHA |
|---|---|
| Required start HEAD | `7fd54c019f8c5b46f93bb2fec9402741e2cda087` |
| Certified Platform input | `421a35e97bc302be0f5e1f196d0a5e8d132f6fd8` |
| Prior Skills PACI pin (superseded) | `0455846487d0b8c583859060ba8b4be70e7f0b48` |

## Pins retained (compatible)

| Item | Value |
|---|---|
| Envelope | `platform.auth-token-envelope/0.1.0` |
| Contracts package (PACI) | `@linktrend/platform-contracts@0.3.0` |
| Envelope schema SHA-256 | `7173b9f9bca59ce8a0e3e3dc2b78b680dd07fdd2451215e3ecd97ff3dd463eed` |
| Envelope contentHash | `9335b1855c3b3a5ec01b40c18ea85a98826192cbfba3110e07399d896e890a12` |
| AuthClaims | `platform.auth-claims/1.1.0` · schema `c2e8bc68…ddfa1` · contentHash `fb518834…ca567` |
| Access-token max TTL | 900s |

Obsolete live advertising of `platform.auth-token-envelope/0.1.3-draft` corrected in current docs; draft mentioned only as superseded.

## Lanes

| Lane | Scope | Result |
|---|---|---|
| A | PACI consumer pins/adapters + migration hash package (no live apply) | Passed |
| B | Certification/eval/runtime/Librarian (no demonstrated defects) | Passed (no code churn) |
| C | Project-scoped Cursor canary contract/evidence (no live canary) | Passed |

## Local proof

| Suite | Result |
|---|---|
| Supported Python | `.venv` / CPython **3.14.3** (`/opt/homebrew/bin/python3.14`) |
| Focused PACI + migrations + cursor contract | **142 passed** |
| Lane B runtime/cert/librarian/gateway waves | **166 passed, 3 skipped, 189 subtests** |
| Ephemeral Postgres migrations | **23 passed** |
| Full pytest | **373 passed, 4 skipped, 189 subtests** (~67s) |
| validator / catalog / ownership / skill_runtime | PASS / 34 skills / success / **6 OK** |
| `git diff --check` | clean |
| Secret scan (changed surfaces) | no private keys / live secrets |
| CI / Bugbot | **deferred** (not polled) |

## Non-claims

- Not live PACI issuer/JWKS/introspection; certified candidate ≠ live authority
- No merge, promote, deploy, live migration apply, live Cursor canary, global Cursor mutation
- No macOS claim of Linux sealed isolation
- No paid Linux host / external service created

## Rollback

Revert the single correction commit on this branch. No live action.
