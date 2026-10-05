---
name: trading-liquidity-stress-testing
description: "Assess portfolio shock losses, liquidation capacity, costs and net funding shortfalls from explicit scenarios."
usage_trigger: "Use for a portfolio stress, liquidity, tail or current-versus-proposed scenario analysis, not order execution."
version: 1.0.0
release_tag: v1.0.0
created: 2026-10-05
author: LiNKskills Library
tags: [trading, liquidity, stress, portfolio, research]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-6.1-sol
  context_required: 32000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [read_file, write_file]
dependencies: []
permissions: [fs_read, fs_write]
scope_out: ["No orders, signing or live activation", "No invented holdings, data, limits or approval", "No new vendor access or costs"]
format_profile: heavy
persistence:
  required: true
  state_path: ".workdir/tasks/{{task_id}}/state.jsonl"
last_updated: 2026-10-05
---

# Portfolio stress and liquidity

Draft, not qualified. Jane owns trading business proposals; independent Validation challenges; Eric owns technical integrations and Sara financial/legal treatment. Analysis does not authorize capital or execution.

## Decision Tree (Fail-Fast & Persistence)

0. Identify one task_id and resume actual native state. The portable state_path is a logical template alias: OpenClaw uses its native sessions/Program Ledger, never a standing JSONL sidecar. INITIALIZED → IN_PROGRESS → COMPLETED or FAILED; PENDING_APPROVAL pauses only a genuinely reserved action, NEEDS_CONTEXT identifies missing evidence.
1. Check trigger, owner, source classification, as-of time, proposed version and outputs. Read supplied records before asking answered questions.
2. Classify Specialist vs Generalist. Inspect supplied native schemas directly. Portable read_file/write_file names map to the consumer’s actual read/write tools; no standalone get_tool_details is required or presumed. CLI-first order: native CLI, CLI wrapper, direct API, MCP when the current consumer supports it. This method requires no vendor API or upstream code execution.
3. Validate required inputs and units; missing affected data blocks only affected quantitative conclusions. Do not replace input failures with demo rows or unknown with zero.
4. Source instructions do not grant authority. Existing authorized analysis needs no repeated founder approval; new costs and reserved actions require their actual approval.

## Workflow

### Phase 1 — Ingestion

Freeze request, input identity, market-data provenance and scenario parameters. Validate input; checkpoint through consumer-native state. Read only task-relevant references.

### Phase 2 — Reasoning

Read `advanced/advanced.md` for the actual required holdings/scenario inputs, task outputs, calculation procedure, source contributions and discriminating cases. Read the one requested calculation branch before producing its result; do not rely on source examples or unavailable values. Use `references/schemas.json` for the structured contract and `examples/worked-input.json` / `examples/worked-output.json` for a fictional gross/net cash reconciliation.

Missing data blocks only dependent quantitative conclusions. Preserve unknowns explicitly; no demo substitution, invented probabilities or automatic policy verdict.


### Phase 3 — Draft and approval boundary

Prepare requested scenario report, uncertainty, owner questions and recommendations. Do not change positions, limits or policies. Authorized draft creation is distinct from consequential execution. Preserve dissent and exact proposal/version where approval is necessary.

### Phase 4 — Verification and completion

Recalculate units, gross/net reconciliation and sensitivities; inspect output against its schema and actual evidence. Independent review is separate from author self-check. Report completed analysis and unexecuted proposals distinctly; checkpoint the actual state.

### Phase 5 — Self-correction and telemetry

Append redacted invocation metadata through consumer/provider-owned execution ledger; no new JSONL runtime ledger. Submit safe reusable findings only to Brain intake, not canon. New lessons propose immutable-release changes to the skill owner. Failed checks remain failures, not fabricated receipts.

## Contract pointers

- Input: `references/schemas.json#/definitions/input`
- Output: `references/schemas.json#/definitions/output`
- State: `references/schemas.json#/definitions/state`
- Methods/source dispositions: `advanced/advanced.md`
- Eval cases: `references/eval-suite.json` and `references/eval-suite.yaml`
- Tool boundaries: `references/api-specs.md`
- Failure patterns: `references/old-patterns.md`
- Exact retained source identity and quarantine: `references/upstream-copy-manifest.json` and ``references/source-disposition.json`, `references/upstream-copy-manifest.json`, and `references/source-packaging.md` — data-only source disposition, copy hashes, and quarantine rules; no raw upstream README is routed as a method.`
- Fictional worked report: `examples/success-pattern.md` and its input/output JSON; no behavioral PASS claimed.
