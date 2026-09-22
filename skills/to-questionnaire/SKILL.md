---
name: to-questionnaire
description: "Turn a decision the session cannot finish into a questionnaire another person fills asynchronously."
usage_trigger: "Use when Intake analysis cannot finish because a named person off-session holds facts or decisions."
version: 1.0.0
release_tag: v1.0.0
created: 2026-09-22
author: LiNKskills Library
tags: [intake, questionnaire]
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

# To Questionnaire

Grill the **send**, not the subject. The recipient holds knowledge this session lacks.

1. **Who.** Role, expertise, relationship. Done when you know what they know that we do not.
2. **What back.** The decisions or facts we cannot resolve alone. Concrete list.
3. **Write** `to-questionnaire-<slug>.md` covering every item from step 2.

Template: purpose; from/to; how answers will be used; one paragraph of context; how to answer (deadline, "I don't know" is useful); themed `##` sections; one idea per question; answer stub; optional _why this matters_; **Anything else?**

Bring completed answers back into `grill-office-hours` or `technical-prd`. Do not pretend the questionnaire is the analysis.

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
