# LiNKskills release-hygiene — docs/archive lane handoff

**Status:** `DOCS_LANE_APPLIED` — archive moves + honesty updates only; no commit/push; no stage/prod claim
**Lane:** A (documentation/archive)
**Date:** 2026-08-02
**Branch:** `dev/cloudcursor/RELEASE-HYGIENE-CLEANUP` (start SHA `46797b2`)
**Machine-readable report:** `/tmp/linkskills-hygiene-lane-a.json`

## What was done

1. **`git mv`** ten superseded root documents into `docs/archive/legacy-root/` (history preserved; nothing deleted).
2. Updated archive index, root README status, Operations Manual Current status (W20 **BLOCKED** + PACI local/fake pins), Intent success/archive pointers, Technical PRD deferred item #11 + drift row.
3. OPEN-ISSUES #9 status line → Completed 2026-08-02; **appended** a Recently completed entry (append-only).
4. Left ADR-cited `docs/CURSOR-GROK-*.md` prompts in place.

## Archived (`docs/archive/legacy-root/`)

- `SOP.md`, `SOP_HUMAN.md`, `SOP_MACHINE.md`
- `OPERATOR_BRIEFING.md`, `OPERATOR_BRIEFING_MVO_CLASS_A.md`
- `260319 LiNKskills PRD.md`
- `LiNKskills PRD v4.0 Implementation Dossier (Phase 0-3).md`
- `COMMAND_REFERENCE.md`
- `SKILLS_CATALOGUE.md`
- `GIT_STRATEGY.md` (no live SoT citations found; AGENTS.md + workflows remain authority)

## Left in place (deliberate)

- SoT: Intent / Technical PRD / Operations Manual / OPEN-ISSUES / approved plan (hash `31a6cc70…`)
- ADRs 0001–0008
- `docs/CURSOR-GROK-*.md` (cited by ADRs + inventories)
- `global_blacklist.md`, migrations, evidence, contracts, skills packages, handoffs, `archive/logic-engine-2026-07-14/`

## Honesty retained

- Stage/prod **not** claimed
- W20 **BLOCKED**
- PACI: Platform pin `421a35e`, AuthClaims `1.1.0`, contracts `0.2.2` / `0.3.0` — **local/fake only**

## Rollback

Reverse each `git mv` from `docs/archive/legacy-root/<file>` back to repo root; revert doc text edits via `git checkout --` on the updated paths (or discard the lane commit if one is created later by the leader).

## Not done by this lane

- Commit / push
- Full pytest (leader)
- Archiving CURSOR-GROK prompts
- Any cloud/Supabase/Platform/runtime mutation
