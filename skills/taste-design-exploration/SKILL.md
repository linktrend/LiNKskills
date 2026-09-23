---
name: taste-design-exploration
description: "Lock default visual direction: company brand notes first, then Taste default, then Apple-like or shape/color/type decisions. Named looks are awesome-design-presets."
usage_trigger: "Use in Assembly after library lookup to lock visual direction before design-sample. Use brandkit path only when the product is a visual identity."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-31
author: LiNKskills Library
tags: [design, taste, direction, visual-language]
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
scope_out: ["Do not restyle after the sample is locked", "Do not invent brand facts", "Do not load a named look unless the plan allows a distinct language", "Do not claim activation"]
format_profile: simple
last_updated: 2026-09-22
---

# Taste Design Exploration

This card locks **direction**. It is not craft, motion, sample pictures, or visual QA.

## Order

1. Read company **brand notes** (Brain Brand aisle). They win.
2. Read the product brief and `DESIGN.md` if present.
3. Apply Taste default (v2) from `references/taste-default.md`: infer VARIANCE / MOTION / DENSITY; anti-slop (no Inter-by-default, no identical card grids, no template hero-metrics). Frozen v1 only if v2 breaks a required workflow.
4. If the plan allows a **distinct visual language**, stop and use `awesome-design-presets` (soft / minimal / brutal). Do not mix three looks.
5. If the product should feel Apple-like (fluid materials, SF-like type on web), apply `references/apple-design.md`.
6. Record shape / color / type decisions using `references/impeccable-shape.md`, `impeccable-colorize.md`, `impeccable-typeset.md` as checklists — they do not override brand or the sample that follows.

Write the lock: palette, type, density, motion yes/no, components, what is forbidden. Then `design-sample` produces the pictures builders must match.

Identity-only products: Taste `brandkit` boards during Intent (see `design-sample`).

Do not implement production UI here.

## Tooling protocol (CLI-first)

**Native CLI**, **CLI wrapper**, **direct API** only if authorized, **MCP** only for an approved adapter. Generalist or >10 tools: `get_tool_details`.

Contracts: `references/schemas.json#/definitions/input` and `#/definitions/output`.
