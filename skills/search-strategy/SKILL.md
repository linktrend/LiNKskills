---
name: search-strategy
description: "Defines research intent, tiered escalation, and HITL controls for cost-aware evidence retrieval workflows."
usage_trigger: "Use when planning or executing research tasks that require confidence-based search tier escalation and operator-controlled deep research."
version: 1.0.0
release_tag: v1.0.0
created: 2026-02-25
author: LiNKskills Library
tags: [research, retrieval, strategy]
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
permissions: [fs_read, fs_write, api_access]
scope_out: ["Do not call paid research APIs before drafting Research Intent", "Do not run Deep Research without operator PROCEED approval"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-02-25
---

# search-strategy

## Decision Tree (Fail-Fast & Persistence)
0. **Resume Check**: If matching task exists, load latest state from `.workdir/tasks/{{task_id}}/state.jsonl`.
1. **Research Intent Gate (Mandatory)**: Draft a `Research Intent` artifact before any API call.
   - If absent: stop and create intent first.
2. **Intelligence Floor Check**: Verify runtime meets frontmatter engine constraints.
3. **Tooling Protocol Check**: Enforce native cli, cli wrapper, direct api, and mcp policy.
4. **Profile Check**: Classify run as specialist or generalist.
   - Generalist or >10 tools: use `get_tool_details` and cache schemas.
5. **Tier-1 Start Rule**: Run Tier 1 (`web`) first unless user explicitly requires another tier.
6. **Escalation Rule**: If Tier 1 confidence is low, escalate to Tier 2 (`neural`) for technical similarity retrieval.
7. **Deep Research HITL Rule (Mandatory)**:
   - If plan requires deep multi-step `brief` reasoning, write intent event via `LTRAuditLogger` and pause.
   - Wait for operator response `PROCEED` before continuing.

## Rules

### Scope-In
- Produce research intent and confidence strategy before calls.
- Route search through tiered cost-aware logic.
- Enforce operator checkpoint for deep research sessions.

### Scope-Out
- Do not skip research intent creation.
- Do not escalate to expensive tiers without confidence rationale.
- Do not proceed with deep brief reasoning without explicit `PROCEED`.

### Tooling Protocol (CLI-First)
1. **Level 1 - Native CLI**: Use native cli for local context and file checks.
2. **Level 2 - CLI Wrapper Scripts**: Use `/tools/research/bin/research` as default logic path.
3. **Level 3 - Direct API (Exception Only)**: Only when wrapper cannot satisfy required endpoint behavior.
4. **Level 4 - MCP**: Use only for persistent, session-based background services.

### Internal Persistence (Zero-Copy / Flat-File)
- Save checkpoints to `.workdir/tasks/{{task_id}}/state.jsonl`.
- Save research intent, confidence scores, and source index as task-local flat files.
- Later phases must seek specific keys/slices instead of loading full artifacts.

### Smart JIT Tool Loading (Mitigated)
- Activate JIT only if profile is `Generalist` or tool count exceeds 10.
- For JIT, call `get_tool_details`, cache schemas, and include one-sentence capability summaries.

## Workflow

### Phase 1: Ingestion & Checkpointing
1. Parse research question, budget, depth target, and required evidence quality.
2. Draft `Research Intent` with objective, constraints, confidence threshold, and tier budget.
3. Classify specialist/generalist and load JIT tool details if required.
4. Validate input contract.
5. Checkpoint `INITIALIZED`.

### Phase 2: Search Logic & Escalation
6. Execute Tier 1 `web` search by default.
7. Score confidence from retrieved results.
8. If confidence below threshold, escalate to Tier 2 `neural` and merge evidence.
9. If `brief` deep-research mode is required, write intent log via `LTRAuditLogger` and checkpoint `PENDING_APPROVAL`.

### Phase 3: Drafting & HITL Gate
10. Build draft evidence report from gathered results.
11. For deep brief mode, wait for operator `PROCEED` token before resuming.

### Phase 4: Finalization
12. After approval, complete deep research steps and finalize report.
13. Validate output contract and checkpoint `COMPLETED`.

### Phase 5: Self-Correction & Auditing
14. Append run summary to `execution_ledger.jsonl`.
15. Save trace to `.workdir/tasks/{{task_id}}/trace.log`.
16. Update `references/old-patterns.md` with escalation/HITL mistakes.

## Tools
| Tool Name | Workflow Scope | Critical Execution Rule |
| :--- | :--- | :--- |
| `/tools/research/bin/research` | Phases 2-4 | Start at `web`; escalate to `neural` on low confidence; gate deep `brief` via HITL. |
| `write_file` | All | Required for state checkpoints and research intent artifacts. |
| `get_tool_details` | Phase 1+ | Mandatory for generalist/JIT profile; cache in task-local state. |

## Contracts
| Direction | Artifact Name | Schema Reference | Purpose |
| :--- | :--- | :--- | :--- |
| **Input** | `research_request` | `./references/schemas.json#/definitions/input` | Validate question, budget, and depth constraints. |
| **Output** | `research_report` | `./references/schemas.json#/definitions/output` | Validate evidence quality, confidence trace, and approvals. |
| **State** | `execution_state` | `./references/schemas.json#/definitions/state` | Persist resumable progress and HITL gates. |

## Progressive Disclosure References
- Advanced heuristics: `./advanced/advanced.md`
- Tier protocol details: `./references/api-specs.md`
- Known failures: `./references/old-patterns.md`
- Version history: `./references/changelog.md`
