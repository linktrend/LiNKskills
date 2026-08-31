---
name: citation-enforcer
description: "Enforces evidence-first reasoning by requiring source attribution for every material claim."
usage_trigger: "Use when outputs require high trust and each claim must be linked to Memory, Search, or File evidence."
version: 1.1.0
release_tag: v1.1.0
created: 2026-02-24
author: LiNKskills Library
tags: [reasoning, evidence, citations]
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
dependencies: [memory]
permissions: [fs_read, fs_write]
scope_out: ["Do not emit unsupported claims", "Do not use citation placeholders without source pointers", "Do not treat missing evidence as observed absence", "Do not accept cyclic or self-referential claim links"]
format_profile: simple
last_updated: 2026-08-31
---

# citation-enforcer

> **Profile: `simple`.** This is a single-pass, stateless enforcement gate. It carries no
> task ledger, no `{{task_id}}` state machine, and no resumable multi-phase workflow — it
> maps each claim to evidence in one pass and returns a cited draft or a blocking report.
> Telemetry (the Phase 5 ledger append) is still mandatory.

## Preconditions (Fail-Fast)
1. Intelligence floor check: confirm the active runtime satisfies `frontmatter.engine`.
2. Tooling policy check: plan must follow the CLI-first protocol below.
3. Confirm a target draft/output with material claims is provided; otherwise stop and request it.

## Enforcement Pass (Single Pass)
1. Enumerate every material (factual) claim in the target output.
2. For each claim, resolve a source type: **Memory**, **Search**, or **File**, with a concrete evidence pointer and confidence label.
3. Attach exactly one citation method `rel` from the accepted vocabulary: **supports**, **contradicts**, **qualifies**, or **cites**.
4. Reject any claim with missing, weak, circular, self-linked, or cyclic evidence. A claim cannot cite or supersede itself.
5. Distinguish **missing evidence** (no pointer; block) from **observed absence** (negative evidence: pointer plus `contradicts`).
6. Do not merge multiple claims under one citation unless all are supported.
7. Emit the final claim-evidence matrix and cited draft. If any claim remains unresolved, block finalization and report the gaps.

## Tooling Protocol (CLI-First)
1. **Level 1 - Native CLI**: use native cli for file evidence collection.
2. **Level 2 - CLI Wrapper Scripts**: use cli wrapper scripts under `scripts/` for citation extraction/normalization.
3. **Level 3 - Direct API**: direct api only under exception policy.
4. **Level 4 - MCP**: use mcp only for persistent background services.
- When the skill is Generalist or has >10 tools, call `get_tool_details` and cache capability summaries.

## Ledger (Telemetry — mandatory)
On completion, append `{ "timestamp", "skill", "task_id", "status", "summary" }` to the
root `execution_ledger.jsonl`. Telemetry is required for every skill regardless of profile.
`task_id` here is a lightweight ledger correlation id, not a resumable state handle.

## Contracts
| Direction | Schema Reference | Purpose |
| :--- | :--- | :--- |
| **Input** | `./references/schemas.json#/definitions/input` | Validate claims requiring citation. |
| **Output** | `./references/schemas.json#/definitions/output` | Validate coverage of evidence per claim. |

## Progressive Disclosure References
- Advanced evidence handling: `./advanced/advanced.md`
- Citation schema: `./references/api-specs.md`
- Failure archive: `./references/old-patterns.md`
- Change history: `./references/changelog.md`
