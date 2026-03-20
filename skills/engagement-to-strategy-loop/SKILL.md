---
name: engagement-to-strategy-loop
description: "Analyzes channel metrics (views, CTR, sentiment) and produces high-signal strategic feedback for marketing iteration loops."
usage_trigger: "Use when channel performance signals need to be translated into actionable strategic updates for Marketing and Growth."
version: 1.0.0
release_tag: v1.0.0
created: 2026-02-25
author: LiNKskills Library
tags: [analytics, feedback, strategy]
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
dependencies: [channel-ops, marketing-strategist, social-ltr]
permissions: [fs_read, fs_write, api_access]
scope_out: ["Do not report metric changes without evidence context", "Do not omit high-signal feedback routing to marketing"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-02-25
---

# engagement-to-strategy-loop

## Decision Tree (Fail-Fast & Persistence)
0. Resume from `.workdir/tasks/*/state.jsonl` when possible.
1. Validate metric inputs include views, CTR, and sentiment signals.
2. Validate intelligence floor from `engine`.
3. Validate tooling protocol: native cli, cli wrapper, direct api, mcp.
4. Classify analysis mode as specialist or generalist.
5. If generalist or >10 tools, call `get_tool_details` and cache schemas.
6. Require high-signal feedback synthesis for marketing team.
7. Fail-fast if no actionable strategy updates are generated.

## Rules

### Scope-In
- Analyze engagement signals across channel outputs.
- Detect high-signal patterns in views, CTR, and sentiment.
- Route strategic recommendations back to marketing loop.

### Scope-Out
- Do not provide insight without source metrics.
- Do not ignore negative sentiment inflection points.
- Do not finalize without output contract validation.

### Tooling Protocol (CLI-First)
1. Level 1 - Native CLI: load metric exports and comment summaries.
2. Level 2 - CLI Wrapper Scripts: deterministic aggregation and scoring logic.
3. Level 3 - Direct API: exception-only for high-volume stream ingestion.
4. Level 4 - MCP: persistent monitoring sessions only.

### Internal Persistence (Zero-Copy / Flat-File)
- Save checkpoints to `.workdir/tasks/{{task_id}}/state.jsonl`.
- Save signal matrices and recommendation drafts as task-local files.
- Use seek-based reads for specific KPI segments.

### Smart JIT Tool Loading (Mitigated)
- Activate JIT only for `Generalist` or >10 tools.
- Call `get_tool_details` and cache capability summaries.

## Workflow

### Phase 1: Ingestion & Checkpointing
1. Ingest channel KPI payloads and sentiment summaries.
2. Normalize metrics across platforms and time windows.
3. Determine specialist/generalist mode and JIT setup.
4. Validate Input Contract.
5. Append `INITIALIZED` checkpoint.

### Phase 2: Logic & Reasoning
6. Identify KPI deltas and anomaly clusters.
7. Correlate sentiment shifts with content/cadence patterns.
8. Distill high-signal feedback and strategic implications.
9. Prepare marketing recommendation set by priority.

### Phase 3: Drafting & Asynchronous Gate
10. Draft high-signal feedback report for marketing.
11. If signal confidence is low, set `PENDING_APPROVAL`.

### Phase 4: Finalization
12. Finalize strategy-loop update with clear actions.
13. Validate Output Contract.
14. Append `COMPLETED` checkpoint.

### Phase 5: Self-Correction & Auditing
15. Append summary to `execution_ledger.jsonl`.
16. Save traces to `.workdir/tasks/{{task_id}}/trace.log`.
17. Update `references/old-patterns.md` with recurring interpretation errors.

## Tools
| Tool Name | Workflow Scope | Critical Execution Rule |
| :--- | :--- | :--- |
| `social-ltr` | Phases 1-2 | Use to collect comment signal inputs when available. |
| `write_file` | All | Persist feedback reports and checkpoint artifacts. |
| `get_tool_details` | Phase 1+ | Required for generalist/JIT profile. |

## Contracts
| Direction | Artifact Name | Schema Reference | Purpose |
| :--- | :--- | :--- | :--- |
| **Input** | `engagement_metrics` | `./references/schemas.json#/definitions/input` | Validate KPI inputs and sentiment context. |
| **Output** | `strategy_feedback` | `./references/schemas.json#/definitions/output` | Validate high-signal feedback and marketing actions. |
| **State** | `execution_state` | `./references/schemas.json#/definitions/state` | Persist resumable feedback loop workflow. |

## Progressive Disclosure References
- Advanced analytics: `./advanced/advanced.md`
- KPI interfaces: `./references/api-specs.md`
- Known anti-patterns: `./references/old-patterns.md`
- Version history: `./references/changelog.md`
