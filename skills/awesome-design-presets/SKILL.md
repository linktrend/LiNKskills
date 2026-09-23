---
name: awesome-design-presets
description: "Apply one named look — soft, minimal, or brutal — when the plan allows a distinct visual language. Not a router over hidden preset files."
usage_trigger: "Use after default direction when the product is allowed a distinct named look (soft, minimal, or brutal). Do not load all three."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-31
author: LiNKskills Library
tags: [design, presets, named-look, visual-style]
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
scope_out: ["Do not load multiple named looks for one product", "Do not override brand notes or a locked sample", "Do not treat leftover vendor preset folders as the working skill"]
format_profile: simple
last_updated: 2026-09-22
---

# Awesome Design Presets

This card is the **named look**. Default direction is `taste-design-exploration`. Choose **one**.

Full look procedures are in this package: `references/looks/soft.md`, `minimal.md`, `brutal.md`. Follow the chosen file. Do not open a hidden 67-member router.

## Soft (high-end / calm)

Calm expensive UI: softer contrast, whitespace, premium type, spring motion. Ban Inter/Roboto/Arial, thick generic icons, harsh `shadow-md`, edge-glued nav, linear easing. Pick one vibe (ethereal glass, editorial luxury, or soft structuralism) and one layout archetype from `soft.md`, then collapse it honestly on mobile (`min-h-[100dvh]`, no hover-only).

## Minimal (editorial product)

Restrained palette, sharp structure, tight hierarchy (Notion/Linear class). Few weights, real grid, no decorative chrome.

## Brutal (industrial)

Swiss type, raw structure, sharp contrast. Hard shadows only in this world. If you did not choose brutal, do not use `box-shadow: 4px 4px 0`.

Write the chosen look into `DESIGN.md` and every screen brief. Then `design-sample` locks pictures. Builders match; they do not mix looks.

If a historical Awesome preset name appears in a brief, translate it to soft, minimal, or brutal using the sample — do not silently load `vendor-skills/awesome-design/*` as the working procedure.

## Tooling protocol (CLI-first)

**Native CLI**, **CLI wrapper**, **direct API** only if authorized, **MCP** only for an approved adapter. Generalist or >10 tools: `get_tool_details`.

Contracts: `references/schemas.json#/definitions/input` and `#/definitions/output`.
