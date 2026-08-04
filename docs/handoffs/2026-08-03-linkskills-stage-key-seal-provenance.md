# Handoff — Stage-key sealed certification + catalog provenance

**Date:** 2026-08-03
**Branch:** `dev/cloudcursor/skills-stage-certification`
**Tip SHA:** `e27ee8e5ccce67d553c8f4649ddd10cf6f7cddff` (evidence/catalog commit; branch may add docs-only commits)
**Evidence/catalog tip (this commit family):** see branch HEAD after push
**Governed source commit:** `0a232932d97a35661c165492649b8814705b04cc`
**source_tree_sha256:** `e6ce798f62da1a2c9781269ac40bed4d08a5fc6c5d09a673c29c667373671894`
**Verdict:** local/stage-key sealed certification **PASS**; stage DB apply remains **HOLD** (Platform-only)

## Gaps closed

1. **Catalog provenance** — `git_sha` is the certified ancestor (not a self-referential tip).
   `source_tree_sha256` binds tracked certification inputs (skills/tools/runtime packages/scripts).
   Excludes generated `catalog/` / `evidence/` / `docs/` / runtime. `build-catalog-index.py --check`
   rejects all-zero, stale, and unrelated commits; docs-only follow-ups do not invalidate.

2. **Real release-mode seal** — GSM secret `LINKTREND_SKILLS_STAGE_EVAL_RUNNER_ISSUER_KEY` v1
   fetched process-only via impersonating
   `skills-runtime@linktrend-linkplatform-stage.iam.gserviceaccount.com`.
   Pinned image `python@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de`.
   Key never printed, never stored, never placed in argv (name-only Docker `--env`).

## Trust binding (stage issuer)

| Constant | Value |
|---|---|
| text-echo source/tool hash | `29b179692378ba32ee244afa7f8b8017e918a158f37127e117cfe24a820f3d83` |
| skill_release_hash | `skill-release:006a23b0af3abbcb9a0600c3f44bf337b89dc6cdd5be6d328097a2498a5f05bb` |
| profile_hash | `9db2d1db2663d9e3fb2a60b0ab4aaaf291aed010d155caba65798b5ecb0ec188` |
| suite_hash | `8f56554dc1b731e94e735ba9dc9d9942e4c2a495ecf11986b071ac17f22a4662` |
| sealed_evidence_sha256 | `a0bb2d56703cb95a6766a8902176f613dffed6af39d798546b338c5b3d77c262` |
| receipt echo-hello | `4da15fe03cb8ac71d34e1b86169bfbb35f47c8c7aa411b93ab2519e075de56e8` |
| receipt echo-json | `7a4b885d545d0e9352be5151869fe8b4c963332225de3a5eab4b8bfdc810fa99` |
| sealed image digest | `sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de` |

## Migration package (Platform-only apply)

- Up: `supabase/migrations/20260803_000010_lskills_canary_echo_usable_seed.sql`
- Down: `…_usable_seed_down.sql` (exact package UUID/hash pins only)
- Manifest: `docs/migrations/MANIFEST-20260803-lskills-canary-echo-usable-seed.md`
- **Do not apply from Skills agents.**

## Residual HOLD

- Stage DB apply still Platform-owned (PREFLIGHT B1–B5)
- No live Lisa / VPS / shared Gateway mutation
- Remaining 34 skills still draft
