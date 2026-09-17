# Handoff — Stage certification trust-gap remediation (Codex HOLD)

**Date:** 2026-08-03
**Branch:** `dev/cloudcursor/skills-stage-certification`
**Base tip (pre-fix):** `8d288f576a1ec7a9b6fc91a46469dfdbb18045ae`
**Verdict:** **PASS** for local sealed trust-gap remediation; **HOLD** for stage/shared apply

## Launch-blocking gaps corrected

1. **Overlay integrity** — `lib/skill_runtime/certification_overlay.py` verifies sealed receipts (repo-contained path, existence, HMAC via `evaluate_certification_evidence` / `sealed_executor_receipt`, bind skill_id + release/profile/suite/tool hashes + PASS). Nonexistent-path promotion test removed; negative suite added.
2. **ADR0006 toolchain hashes** — `scripts/certify-catalog.py` binds observed `text-echo` `source_hash`/`tool_hash` into certification toolchain + execution profile.
3. **Fail-closed certifier exit** — nonzero when sealed requested skill fails or full-catalog sealed yields `usable_count==0`; report still written.
4. **Additive canary seed package 000010** — LiNKskills-owned SQL + down + manifest; Platform applies. Eval_run then usable (trigger preserved). Ephemeral apply/rollback proven locally.

## Counts

| Metric | Value |
|---|---|
| Catalog skills | 35 |
| `usable` | 1 (`canary-echo`) |
| `draft` | 34 |
| text-echo source/tool hash | `6eaa287b75c8848d700e00aa94518e1b711430b5b01a47abd516ddcbce7f71d0` |
| profile_hash (bound) | `b0d3a75267170832387b52360b97ba5cc5b0f56e68e4d7fd5230a5b146f5e3b5` |

## Migration package

- Up: `supabase/migrations/20260803_000010_lskills_canary_echo_usable_seed.sql`
- Down: `…_usable_seed_down.sql` (canary rows only)
- Manifest: `docs/migrations/MANIFEST-20260803-lskills-canary-echo-usable-seed.md`
- **Do not apply from Skills agents.** LiNKplatform only.

## Residual HOLD

- Stage DB apply still Platform-owned (PREFLIGHT B1–B5)
- No live Lisa / VPS / shared Gateway mutation in this session
- Remaining 34 skills still draft (suite_not_executable)
