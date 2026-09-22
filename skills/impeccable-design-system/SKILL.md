---
name: impeccable-design-system
description: "Screen craft while building: layout, type, color, and polish against a locked sample. The brief and brand notes win."
usage_trigger: "Use on Execution screen issues for layout, typography, color, and polish. Use taste-design-exploration to lock direction first. Use ui-ux-guardian for live visual acceptance."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-31
author: LiNKskills Library
tags: [design, ui, ux, craft, polish, impeccable]
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
scope_out: ["Do not invent a new look after design-sample is locked", "Do not replace an explicit brief", "Do not bypass consumer gates", "Do not run motion work that belongs to emil-design-engineering"]
format_profile: simple
last_updated: 2026-09-22
---

# Impeccable Design System

This is the **craft** skill for screens. Direction is already locked. Match `design-sample`. Motion is `emil-design-engineering`. Live acceptance is `ui-ux-guardian`. Redesign of an existing product is `redesign-existing-ui`.

The brief wins. Refinement preserves identity; redesign is a different card.

## Modes

Choose from the surface: **Persuade** (landing), **Operate** (app/task), **Read** (docs), **Experience** (gallery). Persist it only on that surface.

## Craft floor (build with these, then verify once)

Tables in `references/craft-floor.md`, `layout.md`, `typeset.md`, `colorize.md`, `polish.md` are part of this skill.

**Verify together (desktop and mobile, one batched round):** body contrast ≥4.5:1; large text ≥3:1; never gray on color — tint from the hue; shadows have offset and soft blur; tight groups, generous separation, more space above a heading than below; body 65–75ch; display max 6rem; tracking floor -0.04em; real copy at every breakpoint; states hover/disabled/loading/error/empty; theme selection, caret, scrollbars, focus rings; controls name the action.

**Refuse unless the locked sample earned them:** identical icon-card grids; nested cards; hero-metric template; kickers/eyebrows (ban); section numbers without sequence meaning; modal by reflex; gradient text; decorative glass; >1px side stripes; hard offset shadows outside brutal; emoji as icons; system Impact/Arial Black as display; hover-animating images.

## Layout

Fix spacing rhythm and hierarchy before adding chrome. One primary focus per view. Alignment is a system, not per-block.

## Type

Hierarchy from scale and weight, not color tricks. Pair faces from the sample. Do not default to Inter/Roboto/Arial.

## Color

Strategic color on a committed palette. Placeholders inherit the surface hue. Do not gray-on-color.

## Polish

Bounded: build fully, inspect once (desktop + mobile), fix one batch, confirm at most once, stop. Open-ended self-QA is forbidden.

## Tooling protocol (CLI-first)

**Native CLI** for files and screenshots; **CLI wrapper** for deterministic captures; **direct API** only if authorized; **MCP** only for an approved adapter. Generalist or >10 tools: call `get_tool_details`.

Contracts: `references/schemas.json#/definitions/input` and `#/definitions/output`. Ledger append required. Draft only; no live claim.
