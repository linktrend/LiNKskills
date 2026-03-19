# AIOS Runtime Binding Contract

Last updated: 2026-03-17

This document defines the minimum mission context that LiNKskills expects from AIOS runtime callers.

## Required context fields

- `tenant_id`
- `mission_id`
- `run_id`
- `task_id`
- `dpr_id`

## Execution model

- Agents are thin clients and should request skill fragments at runtime.
- Fragments must be scoped to the current mission context.
- Execution outcomes and failures must be written back to LiNKbrain audit channels.

## Governance notes

- MVO communications are Slack-only.
- Telegram is disabled during MVO.
- Protected actions (lesson promotion, archive restore) require CEO/CTO recommendation and Chairman final approval at 08:00 Asia/Taipei.
