---
name: workflow-architect
description: "Reviews existing processes using evidence and owner-reviewed proposals; designs, creates, activates, and validates n8n workflows only for separately authorized implementation requests."
usage_trigger: "Use to map or improve an existing process without executing it, or to implement an explicitly authorized n8n workflow."
version: 1.0.1
release_tag: v1.0.1
created: 2026-02-24
author: LiNKskills Library
tags: [workflow, n8n, automation]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-4.1
  context_required: 128000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, list_dir, get_tool_details]
dependencies: [n8n]
permissions: [fs_read, fs_write, api_access]
scope_out: ["Do not deploy unreviewed production automations without explicit user consent", "Do not store plaintext secrets in workflow JSON"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-06
---

# workflow-architect

## Decision Tree (Fail-Fast & Persistence)
0. **Resume Check**: Is this request linked to an existing `task_id` in `execution_ledger.jsonl`?
   - YES: Resume from latest checkpoint in `.workdir/tasks/<task_id>/state.jsonl`.
   - NO: Generate a new task id `YYYYMMDD-HHMM-WORKFLOWARCHITECT-<SHORTUNIX>`.
1. **Intelligence Floor Check**: Verify runtime satisfies frontmatter `engine` constraints.
   - FAIL: Stop and report required reasoning/context floor.
2. **Tooling Protocol Check**: Validate plan follows native cli, cli wrapper, direct api, and mcp policy.
   - FAIL: Refactor plan before execution.
3. **Profile Check**: Classify workload as Specialist or Generalist.
   - Specialist: single automation domain and <=10 tools.
   - Generalist: multi-domain automation or >10 tools.
4. **JIT Check**: If Generalist, call `get_tool_details`, cache tool schemas in task state, then continue.
5. **Contract Check**: Select `process_review_input` for explicit process review; otherwise validate the existing `input` workflow contract. Process review returns before create/activate/test phases.
6. **Pattern Check**: Review `./references/old-patterns.md` before execution.

## Rules

### Scope-In
- Design workflow JSON for n8n based on explicit trigger/action/outcome requirements.
- Create workflow using `/tools/n8n/bin/n8n create`.
- Activate and test workflow using `/tools/n8n/bin/n8n activate` and `/tools/n8n/bin/n8n trigger`.

### Scope-Out
- Do not hardcode secrets in workflow definitions.
- Do not silently modify unrelated workflows.
- Do not skip state checkpointing.

### Tooling Protocol (CLI-First)
1. **Level 1 - Native CLI**: Use native cli for file navigation and JSON sanity checks.
2. **Level 2 - CLI Wrapper**: Prefer CLI wrapper tools (`/tools/n8n/bin/n8n`) for workflow API logic.
3. **Level 3 - Direct API**: Use direct api only if wrapper lacks required endpoint behavior.
4. **Level 4 - MCP**: Use mcp only for persistent session-based workflow operations.

### Internal Persistence (Zero-Copy / Flat-File)
- Append checkpoints to `.workdir/tasks/{{task_id}}/state.jsonl` after each phase.
- Save generated workflow JSON to `.workdir/tasks/{{task_id}}/workflow.json`.
- Future phases must seek specific keys from state artifacts, not reload full context.

### Smart JIT Tool Loading (Mitigated)
- JIT activates only for Generalist or >10 tools.
- When JIT is active, run `get_tool_details` and cache results under task-local state.
- Each cached entry must include a one-sentence capability summary to reduce planning blind spots.

## Explicit process-review mode

Select this mode only when the request is to document or improve an existing recurring process. Use `process_review_input` and return `process_review_output`; do not require `workflow_request` fields. This mode is a read-only evidence map and owner-review proposal. It returns before legacy workflow creation, activation, or trigger-testing phases, and never creates an n8n workflow or workflow identifier. Keep the original workflow design/create/activate/test route unchanged for explicit workflow implementation requests.

### Process-review method

1. Fix scope, outcome, boundary, as-of date, and privacy class. Separate supplied records from recollection and unreported fields.
2. Map each supplied current step, handoff, decision, approval, and system reference. Copy supplied references exactly; preserve unknown actors and owners as null.
3. Map required controls and approval gates exactly, even when their owner or evidence is missing. Do not remove a gate because a future design appears simpler.
4. Record exception routes only when supplied. Empty input means “not reported,” not “no exceptions.” Identify missing exception owners, dispositions, and escalation points as owner questions.
5. Copy measured volume, cycle-time, rework, or error metrics only with their supplied period, unit, and evidence. Leave missing values null; distinguish observations from hypotheses and do not claim causal savings without a measured comparison.
6. Draft future-state options only as proposals. Identify required approvals, exception handling, assumptions, evidence basis, and an owner reference when supplied; otherwise leave the owner null and ask the process owner.
7. Return a draft map, gaps, and owner questions with empty effects. Do not call workflow tools, create workflow JSON, activate, trigger, publish, or claim implementation. A later separately authorized workflow request follows the legacy workflow path.

## Workflow

### Phase 1: Ingestion & Checkpointing
0. Select explicit `process_review` or the existing workflow implementation path. For `process_review`, validate only its own input contract, execute the process-review method above, validate its separate output contract, and return before any legacy create/activate/test phase.
1. Parse user requirements: trigger, inputs, actions, outputs, error policy.
2. Determine Specialist vs Generalist profile.
3. If Generalist, fetch tool details with `get_tool_details` and cache schemas.
4. Validate request payload with Input Contract.
5. Checkpoint state with `status: INITIALIZED`.

### Phase 2: Design & Transformation
6. Build canonical n8n workflow JSON skeleton.
7. Add nodes, connections, retries, and failure branches.
8. Validate draft against Output Contract semantics.
9. Save draft to task-local `workflow.json` and checkpoint `status: IN_PROGRESS`.

### Phase 3: Create Workflow
10. Post JSON through `/tools/n8n/bin/n8n create --workflow-json ...`.
11. Persist returned workflow id and API response metadata in `state.jsonl`.
12. If creation fails, checkpoint `FAILED`, log root cause, and stop.

### Phase 4: Activate & Test (Resume Point)
13. Activate workflow using `/tools/n8n/bin/n8n activate --workflow-id ...`.
14. Trigger test payload using `/tools/n8n/bin/n8n trigger --workflow-id ... --payload-json ...`.
15. Validate test result against Output Contract and checkpoint `COMPLETED`.

### Phase 5: Self-Correction & Auditing
16. Append execution summary to `execution_ledger.jsonl`.
17. Save raw API outputs and validation notes to `.workdir/tasks/{{task_id}}/trace.log`.
18. Update `./references/old-patterns.md` with any new known-bad design or activation pattern.

## Tools
| Tool Name | Workflow Scope | Critical Execution Rule |
| :--- | :--- | :--- |
| `/tools/n8n/bin/n8n` | Phases 3-4 | Must create before activate; must activate before trigger. |
| `write_file` | All | Required for checkpoints and workflow artifact persistence. |
| `get_tool_details` | Phase 1+ | Mandatory for Generalist/JIT profile and cached locally. |

## Contracts
| Direction | Artifact Name | Schema Reference | Purpose |
| :--- | :--- | :--- | :--- |
| **Input** | `workflow_request` | `./references/schemas.json#/definitions/input` | Requirement integrity validation. |
| **Input** | `process_review_input` | `./references/schemas.json#/definitions/process_review_input` | Existing-process evidence-map request; independent of workflow creation. |
| **Output** | `process_review_result` | `./references/schemas.json#/definitions/process_review_output` | Owner-review map, gaps, future-state draft, empty effects. |
| **Output** | `workflow_result` | `./references/schemas.json#/definitions/output` | Creation/activation/test result validation. |
| **State** | `execution_state` | `./references/schemas.json#/definitions/state` | Resumable task checkpointing. |

## Progressive Disclosure References
- Advanced edge cases: `./advanced/advanced.md`
- API behavior: `./references/api-specs.md`
- Failure history: `./references/old-patterns.md`
- Change history: `./references/changelog.md`
- Process-review fixtures: `./references/process-review-eval-fixtures.json`. Evaluate the actual captured response with `python scripts/eval_process_review.py --input REQUEST.json --output RESPONSE.json`; do not use the case-ID remainder classifier as a behavior check.

For process_review, each missing fact has a structured gap and an explicit owner question ending in `?`. Name the affected step/control/exception reference or metric name in that question; a statement merely noting missing information does not satisfy owner follow-up.
