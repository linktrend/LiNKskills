---
name: revenue-adapter-base
description: "Foundational revenue protocol that ingests heterogeneous monetization signals (YouTube, AdSense, Stripe) and normalizes them into Venture Studio Transaction records."
usage_trigger: "Use when finance operations need standardized transaction-format outputs from mixed revenue sources."
version: 1.0.0
release_tag: v1.0.0
created: 2026-02-25
author: LiNKskills Library
tags: [revenue, finance, normalization]
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
dependencies: [ltr, stripe]
permissions: [fs_read, fs_write, api_access]
scope_out: ["Do not emit raw source-specific payloads as final output", "Do not finalize without Venture Studio Transaction normalization"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-02-25
---

# revenue-adapter-base

## Decision Tree (Fail-Fast & Persistence)
0. Check resumable state in `.workdir/tasks/*/state.jsonl`.
1. Validate presence of at least one supported source (YouTube views, AdSense, Stripe).
2. Validate intelligence floor from `engine`.
3. Validate tooling protocol: native cli, cli wrapper, direct api, mcp.
4. Classify execution mode as specialist or generalist.
5. If generalist or >10 tools, call `get_tool_details` and cache schemas.
6. Require output normalization into Venture Studio Transaction format.
7. Fail-fast on missing required transaction fields.

## Rules

### Scope-In
- Ingest and map revenue signals from heterogeneous sources.
- Normalize all records into a single Venture Studio Transaction schema.
- Provide source traceability for finance reconciliation.

### Scope-Out
- Do not return source-native records as final artifacts.
- Do not drop currency/timestamp/source identifiers.
- Do not finalize without output contract validation.

### Tooling Protocol (CLI-First)
1. Level 1 - Native CLI: inspect and stage local source extracts.
2. Level 2 - CLI Wrapper Scripts: run deterministic normalization transforms.
3. Level 3 - Direct API: exception-only for high-volume revenue feeds.
4. Level 4 - MCP: only for persistent ingestion sessions.

### Internal Persistence (Zero-Copy / Flat-File)
- Append checkpoints to `.workdir/tasks/{{task_id}}/state.jsonl`.
- Store normalized transaction batches as task-local files.
- Use seek-based reads for source-specific reconciliation slices.

### Smart JIT Tool Loading (Mitigated)
- Activate JIT only for `Generalist` or >10 tools.
- Call `get_tool_details` and cache capability summaries.

## Workflow

### Phase 1: Ingestion & Checkpointing
1. Parse source payloads from YouTube, AdSense, and Stripe.
2. Validate field availability and time-window consistency.
3. Determine specialist/generalist mode and initialize JIT cache if needed.
4. Validate Input Contract.
5. Append `INITIALIZED` checkpoint.

### Phase 2: Logic & Reasoning
6. Map source fields to canonical Venture Studio Transaction fields.
7. Standardize amounts, currencies, and timestamps.
8. Attach source metadata and reconciliation pointers.
9. Validate normalized batch integrity.

### Phase 3: Drafting & Asynchronous Gate
10. Draft normalized transaction output and reconciliation summary.
11. If data integrity risk is high, set `PENDING_APPROVAL`.

### Phase 4: Finalization
12. Finalize Venture Studio Transaction batch.
13. Validate Output Contract.
14. Append `COMPLETED` checkpoint.

### Phase 5: Self-Correction & Auditing
15. Append summary to `execution_ledger.jsonl`.
16. Save trace payloads to `.workdir/tasks/{{task_id}}/trace.log`.
17. Update `references/old-patterns.md` with normalization failure patterns.

## Tools
| Tool Name | Workflow Scope | Critical Execution Rule |
| :--- | :--- | :--- |
| `read_file` | Phases 1-2 | Read source payloads before canonical mapping. |
| `write_file` | All | Persist normalized transactions and checkpoints. |
| `get_tool_details` | Phase 1+ | Required for generalist/JIT profile. |

## Contracts
| Direction | Artifact Name | Schema Reference | Purpose |
| :--- | :--- | :--- | :--- |
| **Input** | `revenue_input` | `./references/schemas.json#/definitions/input` | Validate supported source payloads and required metadata. |
| **Output** | `venture_studio_transactions` | `./references/schemas.json#/definitions/output` | Validate canonical Venture Studio Transaction records. |
| **State** | `execution_state` | `./references/schemas.json#/definitions/state` | Persist resumable normalization workflow. |

## Progressive Disclosure References
- Advanced mapping rules: `./advanced/advanced.md`
- Data interface notes: `./references/api-specs.md`
- Known anti-patterns: `./references/old-patterns.md`
- Version history: `./references/changelog.md`
