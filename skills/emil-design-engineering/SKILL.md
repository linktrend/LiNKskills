---
name: emil-design-engineering
description: "Routes specialist motion, animation, prototyping, Expo, Apple-interface, Sonner, UI-library, and Swift work through the complete exact Emil Kowalski skill collection."
usage_trigger: "Use for building or reviewing animation and interaction, finding motion opportunities, prototyping variants, Expo or React Native motion, Apple-style interactions, Sonner, curated UI-library selection, or modern Swift work."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-31
author: LiNKskills Library
tags: [design-engineering, motion, animation, expo, apple, swift]
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
scope_out: ["Do not use a web animation route for Expo or a native route for ordinary web work", "Do not turn motion review into general code review", "Do not add animation when the selected source recommends restraint", "Do not bypass consumer dependency, device, review, or release gates"]
format_profile: simple
last_updated: 2026-08-31
---

# Emil Design Engineering

This family is the specialist authority beneath the broader design stack. All
twelve upstream skills are retained, including `animate-expo`, `apple-design`,
and `write-swift`, so LiNKdeveloper can use the same qualified family for web
and application development.

## Select the specialist

1. Validate the request with
   [`references/schemas.json#/definitions/input`](references/schemas.json).
2. Read [`references/routing.json`](references/routing.json) or run
   `python3 scripts/helper_tool.py --route "<task>"`.
3. Load exactly one selected entrypoint under `vendor-skills/emil-design/` and any file
   it directly references.
4. Respect the source's explicit separation between building, reviewing,
   auditing, finding opportunities, and prototyping.
5. Use Impeccable for broad design reconciliation and final interface polish;
   do not duplicate those responsibilities here.

Consumer routing:

- IDE Development and LiNKdeveloper Web may use the web motion, prototype,
  Sonner, library-selection, and design-engineering routes.
- LiNKdeveloper Apps may additionally use Expo, Apple, and Swift routes.
- LiNKsites normally uses web routes; native routes remain available only when
  its task genuinely targets a native application surface.

## Tool and authority protocol

Use a native CLI to inspect packages and platform versions, followed by a CLI wrapper
for deterministic builds or tests. A direct API requires an existing
consumer grant; MCP is only for an approved persistent adapter. If more than
ten tools or multiple domains become relevant, call `get_tool_details` and
load only the selected schemas.

Conform output to
[`references/schemas.json#/definitions/output`](references/schemas.json).
Dependency installation, signing, device access, publishing, and activation
remain consumer-owned operations.
