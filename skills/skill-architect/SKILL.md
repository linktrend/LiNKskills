---
name: skill-architect
description: "Designs, migrates, and refines production-grade skills following the LiNKskills Golden Template."
usage_trigger: "Use when the user wants to create a new skill, reverse-engineer a third-party skill/prompt into LiNKskills standards, or improve an existing LiNKskills skill."
version: 1.3.0
release_tag: v1.3.0
created: 2026-02-20
author: LiNKskills Library
tags: [meta, generator, migration, refiner]
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5
  context_required: 128000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, make_dir, list_dir, shell_exec, get_tool_details]
dependencies: []
permissions: [fs_read, fs_write, shell_exec]
scope_out: ["Do not create minimalist skills without persistence layers", "Do not execute business actions of target skills; only design, migrate, or refine skill artifacts"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-02-20
---

# Skill Architect

## Decision Tree (Fail-Fast & Persistence)
0.  **Audit Check**: Is this a resume of a previous design/migration/refinement task?
    - YES: Load latest record from `.workdir/tasks/{{task_id}}/state.jsonl`. STOP and EXPLAIN current state.
1.  **Mode Selection**: Determine mode from input:
    - `SCAFFOLD`: Build a new skill from scratch.
    - `REVERSE_ENGINEER`: Convert third-party skill/prompt code into LiNKskills format.
    - `REFINER`: Improve an existing LiNKskills skill (failures, feature requests, tool upgrades, quality improvements).
2.  **Intelligence Floor Check**: Does current runtime satisfy `frontmatter.engine` requirements?
    - NO: Fail-fast and request a higher-capability model/runtime.
3.  **Tooling Protocol Check**: Does execution plan satisfy CLI-first policy and API/MCP limits in `frontmatter.tooling`?
    - NO: Re-plan using tooling protocol before continuing.
4.  **Requirement Check**:
    - `SCAFFOLD`: Require `name`, `description`, `tools`, `usage_trigger`, and `engine`.
    - `REVERSE_ENGINEER`: Require source artifact (files/text), target skill name, expected outputs, and `engine`.
    - `REFINER`: Require target skill name and at least one improvement driver:
      - execution failures/HITL friction
      - `references/old-patterns.md` lessons
      - user-requested new feature
      - tool/interface changes
      - engine-floor adjustments when complexity/context needs changed
    - IF REQUIRED INPUT MISSING: Request missing parameters and STOP.
5.  **Collision/Existence Check**:
    - `SCAFFOLD`: If `/skills/{{skill_name}}` exists, STOP and request overwrite/version decision.
    - `REVERSE_ENGINEER` or `REFINER`: If `/skills/{{skill_name}}` does not exist, STOP and request valid target.
6.  **Prerequisite Check**: Are required tools and dependencies available for selected mode?
    - NO: route request to `/skills/tool-architect` to create missing global tool in `/tools`, then resume.
7.  **Old Pattern Check**: Does the plan use deprecated "stateless" or "plugin-only" formats from `./references/old-patterns.md`?
    - YES: Enforce Golden Template structure.
    - NO: Initiate **Phase 0**.

## Rules

### Scope-In
- Generate, migrate, or refine skills using the Golden Template structure.
- Ensure persistent execution (`task_id`, `.workdir/tasks/{{task_id}}/state.jsonl`, trace logs, optional flat-file artifacts).
- Keep contracts valid and pointers aligned to `references/schemas.json` definitions paths.
- Maintain versioning discipline (`version`, `release_tag`, and `references/changelog.md` updates).

### Scope-Out
- **CRITICAL**: Do not create "minimalist" skills without persistence layers.
- Do not execute business operations of target skills; architect only modifies skill artifacts.
- Do not preserve third-party anti-patterns that violate LiNKskills standards.

### Escalation Protocol
- If `make_dir` fails due to permissions, then report error and request user intervention.
- If validation fails, document failure and update `old-patterns.md` and `changelog.md`.
- If missing required parameters, then stop and request clarification before proceeding.

### Heuristic: Migration/Conversion
If a third-party skill/prompt/codebase is provided, perform a **Structural Audit** before writing files:
1. **Step A - Tool Extraction**: Identify core tool requirements (e.g., `web_search`, `mcp-email`, local scripts, API dependencies).
2. **Step B - Workflow Deconstruction**: Decompose source instructions into the LiNKskills 5-phase workflow.
3. **Step C - Decision Tree Injection**: Add fail-fast checks, `task_id` generation, persistence, and resumability rules.
4. **Step D - Failure Seeding**: Initialize `references/old-patterns.md` with likely failure modes for that skill type plus migration-specific anti-patterns.

### Global Tooling & Persistence Protocol
1. **Level 1 - Native CLI**: Prioritize system binaries first (`git`, `rg`, `grep`, etc.).
2. **Level 2 - CLI Wrapper Scripts**: Default logic should run through scripts in each skill's `scripts/`.
3. **Level 3 - Direct API (Exception Only)**: Allow only for high-frequency LLM reasoning, complex DB queries with high serialization costs, or real-time streaming.
4. **Level 4 - MCP**: Allow only for persistent, session-based background services.
5. **Internal Persistence**: Write phase checkpoints to `state.jsonl`; use task-local flat files for heavy artifacts; later phases must seek targeted slices/keys.
6. **Smart JIT Loading**:
   - Activate only when skill is `Generalist` or has `>10` tools.
   - Require one-sentence capability summaries for listed tools to avoid planning blind spots.
   - Require `get_tool_details` call and task-local schema caching when JIT is active.

## Workflow

### Phase 0: Improvement & Migration Audit
1. Select execution mode: `SCAFFOLD`, `REVERSE_ENGINEER`, or `REFINER`.
2. For `REVERSE_ENGINEER`, run the Structural Audit heuristic (Steps A-D).
3. For `REFINER`:
   - Read root `execution_ledger.jsonl` and target `references/old-patterns.md`.
   - Ingest user-provided improvement requests (new features, tool upgrades, or workflow refinement).
   - Build a versioned refinement plan with proposed diffs to `SKILL.md`, contracts, and references.
4. **CHECKPOINT**: Append audit output to `state.jsonl` with `status: "AUDITED"`.

### Phase 1: Ingestion & State Init
5. Extract mode-specific inputs and validate against `./references/schemas.json#/definitions/spec`.
6. Categorize target skill profile:
   - `Specialist`: single domain and `<=10` tools.
   - `Generalist`: multi-domain or `>10` tools.
7. If profile is `Generalist`, plan mandatory `get_tool_details` usage and schema caching instructions.
8. Validate target skill naming (kebab-case) and path strategy.
9. **CHECKPOINT**: Generate `task_id` (`YYYYMMDD-HHMM-SKILLARCH-<SHORTUNIX>`) and append `status: "INITIALIZED"` to `state.jsonl`.

### Phase 2: Schema & Manifest Design
10. Generate/modify YAML frontmatter with `version`, `release_tag`, `engine`, `tooling`, persistence, tools, dependencies, and permissions.
11. Build or refactor the Decision Tree for the selected mode and domain, including Specialist/Generalist branch logic.
12. Generate or tighten Input/Output/State contracts in `references/schemas.json`.
13. For `REFINER`, explicitly map observed failures or requested features to contract and workflow updates.
14. **CHECKPOINT**: Append `status: "DESIGNED"` to `state.jsonl` and save manifest/schema drafts.

### Phase 3: Build / Migration / Refinement Execution
15. `SCAFFOLD`: Create full structure (`advanced/`, `examples/`, `references/`, `scripts/`, `.workdir/tasks/`) and write all template files.
16. `REVERSE_ENGINEER`: Transform source into LiNKskills-compliant files and generate missing folders/contracts/trace scaffolding.
17. `REFINER`: Patch existing `SKILL.md`, contracts, and references in place; include user-requested features and tool refinements.
18. Enforce tooling and persistence protocol text in generated skill artifacts (CLI-first, JIT conditions, `state.jsonl`, `get_tool_details`).
19. Always update `references/changelog.md` with reason, scope, and version delta.
20. **CHECKPOINT**: Append one of `SCAFFOLDED`, `MIGRATED`, or `REFINED` to `state.jsonl`.

### Phase 4: Verification
21. Run `python3 ../../validator.py --path ../{{skill_name}} --repo-root ../..`.
22. Run `python3 ../../global_evaluator.py --root ../..` for `REFINER` mode or when cross-skill risk insight is needed.
23. If validation fails, record errors in `state.jsonl` and old-patterns with `status: "VALIDATION_FAILED"`.
24. Report findings and compatibility notes to the user.
25. **CHECKPOINT**: Append `VALIDATED` or `VALIDATION_FAILED` to `state.jsonl`.

### Phase 5: Self-Correction & Auditing
26. **LEDGER**: Append `{ "timestamp", "skill": "skill-architect", "task_id", "status", "summary" }` to root `execution_ledger.jsonl`.
27. **TRACE**: Save model/tool trace to `.workdir/tasks/{{task_id}}/trace.log`.
28. **LEARN**: Update `./references/old-patterns.md` when failures, user corrections, migration anti-patterns, or new reusable lessons are identified.
29. Append `COMPLETED` to `state.jsonl`.

## Tools
| Tool Name | Workflow Scope | Critical Execution Rule |
| :--- | :--- | :--- |
| `make_dir` | Phase 3 | Create required directories before writing files. |
| `write_file` | Phase 0-5 | Use for checkpointing, scaffolding, migration outputs, and changelog updates. |
| `read_file` | Phase 0-2 | Read template/source/target artifacts for audits and design diffs. |
| `list_dir` | Phase 0-1 | Check for existence/collision of source and target skill folders. |
| `shell_exec` | Phase 4 | Use only for validator/evaluator checks; no business-action execution. |
| `get_tool_details` | Phase 1+ | Mandatory when profile is Generalist or tool count > 10; cache schemas for JIT. |

## Contracts
| Direction | Artifact Name | Schema Reference | Purpose |
| :--- | :--- | :--- | :--- |
| **Input** | `skill_spec` | `./references/schemas.json#/definitions/spec` | Validate mode-specific requirements. |
| **Output** | `architect_report` | `./references/schemas.json#/definitions/report` | Integrity check of generated/migrated/refined output. |
| **State** | `execution_state` | `./references/schemas.json#/definitions/state` | Persistent checkpointing of design progress. |

## Progressive Disclosure References
- **Examples**: Refer to [`./examples/success-scaffold.md`](#) for a complete trace of generating a skill.
- **Examples**: Refer to [`./examples/reverse-engineering.md`](#) for migration from third-party inputs.
- **Examples**: Refer to [`./examples/refiner-mode.md`](#) for iterative improvement of an existing skill.
- **Advanced**: Refer to [`./advanced/advanced.md`](#) for complex edge cases and customization patterns.
- **Reference**: Refer to [`./references/manifest-spec.md`](#) for YAML frontmatter field definitions.
- **Versioning**: Refer to [`./references/changelog.md`](#) for tracked skill evolution.

## Old Patterns
> **IMPORTANT**: The agent MUST consult [`./references/old-patterns.md`](#) during the Decision Tree phase. This file is dynamically updated by the agent in Phase 5 to prevent "Convention Drift" and ensure 100% adherence to evolving project norms.
