---
name: smart-file-clerk
description: "Senior Document Manager skill for hybrid storage orchestration: Supabase Buckets for active RAG and Google Drive for deep archive, with OCR pipelines for financial/legal documents."
usage_trigger: "Use when documents must be classified, OCR-processed, and routed between active and archive storage tiers."
version: 1.0.0
release_tag: v1.0.0
created: 2026-02-25
author: LiNKskills Library
tags: [documents, storage, ocr]
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
dependencies: [doc-engine, asset-filer, gws, ltr]
permissions: [fs_read, fs_write, api_access]
scope_out: ["Do not store sensitive docs without classification", "Do not skip OCR for eligible financial/legal documents in Supabase"]
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-02-25
---

# smart-file-clerk

## Decision Tree (Fail-Fast & Persistence)
0. Resume from `.workdir/tasks/*/state.jsonl` when available.
1. Validate document set and classification metadata.
2. Validate intelligence floor from `engine`.
3. Validate tooling protocol: native cli, cli wrapper, direct api, mcp.
4. Classify workflow as specialist or generalist.
5. If generalist or >10 tools, call `get_tool_details` and cache schemas.
6. Route active RAG documents to Supabase Buckets and deep archive docs to Google Drive.
7. Require OCR pass for financial/legal docs stored in Supabase.
8. For financial documents, enforce template alignment against `/shared/templates/MASTER_FINANCE_TEMPLATES.md`.
9. Fail-fast if OCR output or storage metadata is missing.

## Rules

### Scope-In
- Classify and route documents across active and archive tiers.
- Execute OCR for financial/legal documents in Supabase.
- For finance files, validate extracted fields against `/shared/templates/MASTER_FINANCE_TEMPLATES.md`.
- Maintain traceable metadata for retrieval workflows.

### Scope-Out
- Do not archive active-RAG docs prematurely.
- Do not skip OCR for eligible docs.
- Do not finalize without output contract validation.

### Tooling Protocol (CLI-First)
1. Level 1 - Native CLI: inspect document sets and metadata.
2. Level 2 - CLI Wrapper Scripts: deterministic routing/OCR orchestration.
3. Level 3 - Direct API: exception-only for high-volume storage operations.
4. Level 4 - MCP: persistent background indexing services only.

### Internal Persistence (Zero-Copy / Flat-File)
- Save checkpoints to `.workdir/tasks/{{task_id}}/state.jsonl`.
- Save classification maps and OCR extracts as task-local files.
- Use seek-based reads for document-level retrieval.

### Smart JIT Tool Loading (Mitigated)
- Activate JIT only for `Generalist` or >10 tools.
- Call `get_tool_details` and cache capability summaries.

## Workflow

### Phase 1: Ingestion & Checkpointing
1. Collect document metadata (type, sensitivity, recency, usage mode).
2. For finance docs, load `/shared/templates/MASTER_FINANCE_TEMPLATES.md` field requirements.
3. Tag docs as active-RAG or deep-archive candidates.
4. Determine specialist/generalist mode and JIT setup.
5. Validate Input Contract.
6. Append `INITIALIZED` checkpoint.

### Phase 2: Logic & Reasoning
7. Route active docs to Supabase Buckets.
8. Route archive docs to Google Drive.
9. Run OCR for eligible financial/legal docs stored in Supabase.
10. Build retrieval metadata with source pointers.

### Phase 3: Drafting & Asynchronous Gate
11. Draft storage and indexing report.
12. If classification ambiguity exists, set `PENDING_APPROVAL`.

### Phase 4: Finalization
13. Finalize storage actions and OCR index outputs.
14. Validate Output Contract.
15. Append `COMPLETED` checkpoint.

### Phase 5: Self-Correction & Auditing
16. Append summary to `execution_ledger.jsonl`.
17. Save trace to `.workdir/tasks/{{task_id}}/trace.log`.
18. Update `references/old-patterns.md` with document-routing failures.

## Tools
| Tool Name | Workflow Scope | Critical Execution Rule |
| :--- | :--- | :--- |
| `asset-filer` | Phases 2-4 | Use for Supabase-bound active assets and metadata registration. |
| `doc-engine` | Phases 2-3 | OCR mandatory for financial/legal docs in Supabase. |
| `get_tool_details` | Phase 1+ | Required for generalist/JIT profile. |

## Contracts
| Direction | Artifact Name | Schema Reference | Purpose |
| :--- | :--- | :--- | :--- |
| **Input** | `document_batch` | `./references/schemas.json#/definitions/input` | Validate document metadata and routing context. |
| **Output** | `storage_index_report` | `./references/schemas.json#/definitions/output` | Validate storage routing and OCR indexing results. |
| **State** | `execution_state` | `./references/schemas.json#/definitions/state` | Persist resumable doc-management workflow state. |

## Progressive Disclosure References
- Advanced routing logic: `./advanced/advanced.md`
- Storage/OCR interfaces: `./references/api-specs.md`
- Known anti-patterns: `./references/old-patterns.md`
- Version history: `./references/changelog.md`
