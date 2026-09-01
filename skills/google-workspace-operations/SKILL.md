---
name: google-workspace-operations
description: "Routes an authorized Google Workspace task to one exact preserved gws operation skill without granting credentials, permissions, or execution authority."
usage_trigger: "Use when a consumer needs an exact Google Workspace CLI operation for Drive, Docs, Sheets, Slides, Gmail, Calendar, Tasks, Chat, Classroom, Forms, Keep, Meet, Admin, Groups, People, or related Workspace APIs."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-31
author: LiNKskills Library
tags: [google-workspace, gws, routing, productivity]
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5
  context_required: 128000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, shell_exec, get_tool_details]
dependencies: []
permissions: [fs_read, shell_exec]
scope_out: ["Do not authenticate or grant scopes", "Do not execute a write without consumer authority", "Do not activate a consumer profile", "Do not treat internal canary admission as stable qualification"]
format_profile: simple
last_updated: 2026-08-31
---

# Google Workspace Operations

Use this adapter to select one exact preserved Google Workspace source skill.
It is a routing and disclosure layer; it does not own Google credentials,
OAuth scopes, Program permissions, approval, or execution.

## Route one operation

1. Identify the exact Workspace service and operation requested.
   Validate the request against
   [`references/schemas.json#/definitions/input`](references/schemas.json).
2. Prefer `python3 scripts/helper_tool.py --route-id "<gws-skill-id>"` when the
   caller already knows the route. Otherwise use `--route "<task>"` and fail
   closed on `AMBIGUOUS`, `NOT_APPLICABLE`, or `NOT_ELIGIBLE`.
3. Read only the returned `source_entrypoint` and the shared prerequisites it
   explicitly references.
4. Confirm the consumer has the required account, OAuth scopes, data access,
   and approval before any command is executed.
5. Return the proposed command or perform it only through the consumer's own
   governed execution process.

Return the route decision defined by
[`references/schemas.json#/definitions/output`](references/schemas.json).

The 95 preserved source members are approved or blocked individually in
[`references/admission.json`](references/admission.json). Internal-canary
admission permits controlled consumer evaluation; it does not make a release
ordinarily selectable or stable-qualified.

## Safety boundary

Read operations may still expose private company or customer data. Write,
share, send, delete, permission, and administrator operations require explicit
consumer tool authority. Never infer authority merely because a route exists.

Use the native CLI for ordinary authorized Workspace operations and a small
deterministic CLI wrapper only when it reduces repeated command construction.
Use a direct API only when the consumer has authorized the exact API and the
CLI cannot perform the operation. Use MCP only for an approved persistent
adapter. If more than ten tools are exposed, load only the selected capability
details.
