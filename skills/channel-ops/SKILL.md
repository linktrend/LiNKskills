---
name: channel-ops
description: "Platform-specific channel operations skill for YouTube, TikTok, and X, covering scheduling, comment workflows, and support-to-sales conversion motions."
usage_trigger: "Use when campaign content needs platform execution SOPs, engagement handling, and conversion-oriented channel operations."
version: 1.0.0
release_tag: v1.0.0
created: 2026-02-25
author: LiNKskills Library
tags: [channel, distribution, operations]
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5
  context_required: 128000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, list_dir, get_tool_details]
dependencies: [social-ltr, sync-scheduler, marketing-strategist]
permissions: [fs_read, fs_write, api_access]
scope_out: ["Do not publish without platform-specific SOP alignment", "Do not ignore support-to-sales handoff opportunities"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-02-25
---

# channel-ops

## Decision Tree (Fail-Fast & Persistence)
0. Resume from `.workdir/tasks/*/state.jsonl` when task continuation exists.
1. Validate target platform set (YouTube/TikTok/X) and schedule window.
2. Validate intelligence floor from `engine`.
3. Validate tooling protocol: native cli, cli wrapper, direct api, mcp.
4. Classify operation mode as specialist or generalist.
5. If generalist or >10 tools, call `get_tool_details` and cache schemas.
6. Require platform SOP checks before scheduling or engagement actions.
7. Require support-to-sales funnel tagging for qualified interactions.

## Rules

### Scope-In
- Execute platform-specific SOPs for YouTube, TikTok, and X.
- Schedule posts and monitor comments with response pathways.
- Convert support interactions into sales-qualified handoffs.

### Scope-Out
- Do not run cross-platform actions without platform adaptation.
- Do not treat all comments as equal; route by intent.
- Do not finalize without output contract validation.

### Tooling Protocol (CLI-First)
1. Level 1 - Native CLI: stage schedule and response context.
2. Level 2 - CLI Wrapper Scripts: use `social-ltr`/`sync-scheduler` for deterministic actions.
3. Level 3 - Direct API: exception-only for unsupported high-frequency operations.
4. Level 4 - MCP: persistent background sessions only.

### Internal Persistence (Zero-Copy / Flat-File)
- Save checkpoints to `.workdir/tasks/{{task_id}}/state.jsonl`.
- Store per-platform runbooks and comment routing outputs as flat files.
- Use seek-based reads for platform-specific slices.

### Smart JIT Tool Loading (Mitigated)
- Activate JIT only for `Generalist` or >10 tools.
- Call `get_tool_details` and cache capability summaries.

## Workflow

### Phase 1: Ingestion & Checkpointing
1. Parse campaign goals, target platforms, and posting calendar.
2. Load platform SOP constraints and moderation policies.
3. Determine specialist/generalist mode and JIT setup.
4. Validate Input Contract.
5. Append `INITIALIZED` checkpoint.

### Phase 2: Logic & Reasoning
6. Build schedule plan by platform with timing and message variants.
7. Define comment triage and response matrix.
8. Define support-to-sales qualification logic and handoff criteria.
9. Prepare execution payloads for social wrappers.

### Phase 3: Drafting & Asynchronous Gate
10. Draft channel operations runbook and action queue.
11. If compliance or risk threshold is exceeded, set `PENDING_APPROVAL`.

### Phase 4: Finalization
12. Finalize schedule, engagement handling, and handoff rules.
13. Validate Output Contract.
14. Append `COMPLETED` checkpoint.

### Phase 5: Self-Correction & Auditing
15. Append summary to `execution_ledger.jsonl`.
16. Save traces to `.workdir/tasks/{{task_id}}/trace.log`.
17. Update `references/old-patterns.md` with channel failure learnings.

## Tools
| Tool Name | Workflow Scope | Critical Execution Rule |
| :--- | :--- | :--- |
| `social-ltr` | Phases 2-4 | Use for post and comment actions across supported platforms. |
| `sync-scheduler` | Phases 1-2 | Align schedule windows before publishing actions. |
| `get_tool_details` | Phase 1+ | Required for generalist/JIT profile. |

## Contracts
| Direction | Artifact Name | Schema Reference | Purpose |
| :--- | :--- | :--- | :--- |
| **Input** | `channel_plan_input` | `./references/schemas.json#/definitions/input` | Validate platform scope and campaign schedule context. |
| **Output** | `channel_ops_plan` | `./references/schemas.json#/definitions/output` | Validate scheduling, comment ops, and conversion routing outputs. |
| **State** | `execution_state` | `./references/schemas.json#/definitions/state` | Persist resumable channel operations flow. |

## Progressive Disclosure References
- Advanced SOP logic: `./advanced/advanced.md`
- Platform interface notes: `./references/api-specs.md`
- Known anti-patterns: `./references/old-patterns.md`
- Version history: `./references/changelog.md`
