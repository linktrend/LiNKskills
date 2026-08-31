---
name: search-strategy
description: "One-way facade that supersedes new broad research workflows onto canonical research. Does not run a competing retrieval methodology or the excluded tools/research router."
usage_trigger: "Use only as a legacy alias; new broad research briefs must select research. This skill forwards intent, HITL, and tier gates without implementing a second methodology."
version: 1.0.0
release_tag: v1.0.0
created: 2026-02-25
author: LiNKskills Library
tags: [research, retrieval, strategy, facade]
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
dependencies: [research]
permissions: [fs_read, fs_write]
scope_out: ["Do not call paid research APIs before drafting Research Intent", "Do not run Deep Research without operator PROCEED approval", "Do not select tools/research or a named retrieval provider", "Do not depend on research depending back on this skill"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-08-31
---

# search-strategy

This skill is a **one-way facade**. It does not own a second research
methodology. Callers asking for a new broad research workflow are routed to
canonical `research`. The prior exact release remains independently addressable
and is not rewritten. `citation-enforcer` stays independently composable.

## Facade decision tree

0. **Resume Check**: If a matching task exists, load `.workdir/tasks/{{task_id}}/state.jsonl`.
1. **Supersession**: For a new broad workflow, select `research` and record
   `outcome=supersession`, `direction=one-way`.
2. **Research Intent Gate (Mandatory)**: Draft a `Research Intent` before any
   retrieval. If absent: stop and create intent first.
3. **Provider-neutral routing**: Escalate cost tiers (`web` → `neural` →
   `brief`) by confidence and HITL rules only. Do not name a vendor API.
   Classify the run as specialist or generalist; generalist or more than ten
   tools uses `get_tool_details`.
4. **Legacy router exclusion**: Never invoke `/tools/research`,
   `tools/research/bin/research`, or a consumer research gateway from this
   skill. Transport remains consumer-owned.
5. **Deep Research HITL**: Multi-step `brief` work writes intent and returns
   `PENDING_APPROVAL` until the operator supplies `PROCEED`.

## Rules

### Scope-In
- Forward useful intent, confidence, and HITL controls into `research`.
- Preserve this skill id for legacy selectors.

### Scope-Out
- Do not implement a competing claim graph or workstream planner.
- Do not introduce a reverse dependency from `research` to this skill.
- Do not call a named retrieval provider or the excluded research router.

### Tooling Protocol (CLI-First)
1. **Level 1 - Native CLI**: local context and file checks.
2. **Level 2 - CLI Wrapper Scripts**: `scripts/helper_tool.py` for facade
   routing only.
3. **Level 3 - Direct API**: exception only; still provider-neutral.
4. **Level 4 - MCP**: persistent consumer-owned services only.

## Workflow

1. Parse the request and emit the facade/supersession outcome.
2. Hand the Research Intent, freshness, privacy, and depth fields to `research`.
3. For deep brief mode without `PROCEED`, checkpoint `PENDING_APPROVAL`.
4. Do not finalize a competing `research_report`; the canonical skill owns
   synthesis and citation composition.

## Contracts
| Direction | Artifact Name | Schema Reference | Purpose |
| :--- | :--- | :--- | :--- |
| **Input** | `research_request` | `./references/schemas.json#/definitions/input` | Question, budget, depth, and optional facade flags. |
| **Output** | `facade_result` | `./references/schemas.json#/definitions/output` | One-way routing outcome; empty effects. |
| **State** | `execution_state` | `./references/schemas.json#/definitions/state` | Resumable HITL gates. |

## Progressive Disclosure References
- Advanced heuristics: `./advanced/advanced.md`
- Tier protocol details: `./references/api-specs.md`
- Known failures: `./references/old-patterns.md`
- Version history: `./references/changelog.md`
