---
name: writing-for-agents
description: "Write documents cheaper executors can follow: Intent, reuse decisions, issue briefs, proof manifests, ship criteria, and library entries."
usage_trigger: "Use when writing Intent, reuse decisions, execution briefs, proof manifests, ship criteria, or library entries for later agents."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [writing, briefs, agents]
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

# Writing For Agents

The agent takes the same **process** every run. Packaging differs; writing does not.

## Levers

- **Context pointer:** wording, not the target, decides when material is reached. Front-load the leading word. One trigger per branch.
- **Two loads:** always-on context vs human index. Disclose what only some branches need.
- **Hierarchy:** in-file steps first; in-file reference; disclosed reference behind a pointer in this same skill package.
- **Co-location:** definition, rules, caveats under one heading.
- **Completion criterion:** checkable and exhaustive. Sharpen a fuzzy bound before splitting files.
- **Leading words:** compact pretrained concepts (`tight`, `red`, `tracer bullet`). Prompt the positive behaviour.
- **Prune:** one source of truth; do not cache what `package.json` already says; delete no-ops.

## Completeness (Taste output)

Do not truncate. No placeholder sections. No "rest omitted". If a brief lists files, list them all.

## Artifacts this skill writes in the program

**Intent:** outcome, users, non-goals, constraints, success checks. Cheap executors must not re-plan.

**Reuse decision:** what is the base (library, starter, OSS), what will be refactored, what is forbidden to rewrite.

**Issue brief:** outcome; files that may change; files that must not; interfaces already decided; local checks that prove the issue; stop-when-blocked.

**Proof manifest:** index of Verification artifacts with paths and what each proves.

**Ship criteria:** named server, deploy method, health check, settings that can only be made live.

**Library entry:** how a later agent reuses the extracted work.

Do not use Diátaxis product-doc shape for these artifacts.

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
