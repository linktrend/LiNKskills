---
name: hybrid-development-methods
description: "Historical catalog id for the old hybrid router. Not how work runs. Use the named Software Development skills instead."
usage_trigger: "Do not use for new work. Kept only so history and old references still resolve. Follow the named catalog skills on Software Development Coding and Design."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-31
author: LiNKtrend Principal; migrated and packaged by LiNKskills
tags: [development, historical, superseded]
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
scope_out: ["Do not route work through hidden vendor members", "Do not treat this id as the working development method", "Do not auto-refresh upstream bytes"]
format_profile: simple
last_updated: 2026-09-22
---

# Hybrid Development Methods (historical)

This id remains so old references do not 404. **It is not how work runs.** Do not select a hidden member. Do not load `vendor-skills/hybrid-development/` as the procedure.

Use these catalog skills instead (each is a followable `SKILL.md`):

Intake: `triage`, `grill-office-hours`, `research`, `to-questionnaire`, `plan-ceo-review`, `writing-for-agents`, `technical-prd`, `autoplan`.

Assembly: `to-tickets`, `research`, `writing-for-agents`, `gap-design`, `plan-eng-review`, `taste-design-exploration`, `awesome-design-presets`, `design-sample`, `pick-ui-library`.

Execution: `implement`, `design-html`, `impeccable-design-system`, `emil-design-engineering`, `mobile-native-web`, `ask-sonner`, `redesign-existing-ui`, `phase-review`, `diagnose-investigate`.

Verification: `plan-eng-review`, `cso`, `qa-only`, `ui-ux-guardian`, `devex-review`, `benchmark`, then `diagnose-investigate` / `implement` for repair.

Shipment: `writing-for-agents`, `ship`, `land-and-deploy`, `canary`, `document-release`.

If you were invoked as `hybrid-development-methods`, stop routing and open the matching named skill above for the current phase.

## Tooling protocol (CLI-first)

**Native CLI**, **CLI wrapper**, **direct API** only if authorized, **MCP** only for an approved adapter. Generalist or >10 tools: `get_tool_details`.

Contracts: `references/schemas.json#/definitions/input` and `#/definitions/output`.
