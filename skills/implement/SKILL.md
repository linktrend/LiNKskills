---
name: implement
description: "Implement one issue from its brief test-first at agreed seams, using deep-module vocabulary, then checkpoint. Phase review is not per issue."
usage_trigger: "Use on an Execution issue: branch or worktree, implement from the brief, commit, push, checkpoint. Do not open a PR. Do not run phase review per issue."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [execution, tdd, implement]
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5
  context_required: 128000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, list_dir, shell_exec, get_tool_details]
dependencies: []
permissions: [fs_read, fs_write, shell_exec]
scope_out: ["Do not claim live or usable certification", "Do not print secrets", "Do not weaken consumer delivery gates"]
format_profile: simple
last_updated: 2026-09-22
---

# Implement

Work the issue brief. Git branch/commit/push/checkpoint are git. Do not open a pull request. Do not run `phase-review` here.

## Seams and TDD

1. Read `CONTEXT.md` and ADRs. Confirm **seams** with the brief (or the user if the brief omitted them). No test at an unconfirmed seam.
2. Consult deep-module vocabulary in `gap-design` / `references/codebase-design.md`: test through the public interface.
3. **Red → green**, one vertical slice: one failing test, only enough code to pass, repeat. Do not write all tests first.
4. Good tests specify behaviour (`user can checkout with valid cart`). Expected values come from an independent source of truth, not from recomputing the implementation.
5. Anti-patterns: implementation-coupled mocks; tautological assertions; horizontal slicing.
6. Refactor is not this loop. Smell cleanup belongs to `phase-review`.

Typecheck often. Run the touched tests often. Run only the checks the **phase brief** names, plus a build of what this issue changed. The full suite lives in Verification.

If the deliverable is Pretext HTML, use `design-html` instead of this skill.

On a screen issue, follow `impeccable-design-system` craft and, if the brief allows motion, `emil-design-engineering`. Match `design-sample`. Do not restyle.

When blocked, stop with the brief's stop rule. Repair uses `diagnose-investigate` then this skill.

## Tooling protocol (CLI-first)

1. **Native CLI** for git, files, screenshots, tests, and local inspection.
2. **CLI wrapper** scripts under this skill's `scripts/` for deterministic checks.
3. **Direct API** only when the consumer already authorized that exact service and a CLI cannot do the work.
4. **MCP** only for an approved persistent adapter.

When the task is generalist or exposes more than ten tools, call `get_tool_details` and cache only the selected schemas.

## Contracts

Validate input against `references/schemas.json#/definitions/input`.
Emit output against `references/schemas.json#/definitions/output`.
Append `{timestamp, skill, status, summary}` to `execution_ledger.jsonl`.
Never print secrets, tokens, or private credentials.

This skill is draft catalog procedure. It does not grant permission-to-act, does not mark itself live or usable, and cannot weaken the consumer's proof, review, integration, promotion, or named-server deploy gates.
