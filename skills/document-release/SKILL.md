---
name: document-release
description: "Update docs to match what shipped using a coverage map; generate missing Diátaxis pages only when the map shows a hole."
usage_trigger: "Use at the end of Shipment so documentation matches the shipped tree."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [shipment, docs]
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

# Document Release

## Diff analysis

From the release merge-base: `git diff --stat`, log, name-only. Classify: new features, changed behaviour, removals, infrastructure. List markdown at repo depth 2 excluding vendor dumps.

## Coverage map

For each new/changed public surface (command, flag, module, env, skill):

```
entity | reference | how-to | tutorial | explanation
```

Fill holes. `document-generate` Diátaxis shape is allowed **here** for missing product docs, not for Intent or issue briefs.

Then update CHANGELOG voice if `ship` left a stub, fix cross-links, and commit docs with the consumer git rules. Do not bump VERSION again.

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
