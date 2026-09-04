---
name: taste-design-exploration
description: "Routes divergent website and application visual exploration through the exact Taste collection to produce meaningfully different directions without replacing downstream quality control."
usage_trigger: "Use when a website or application needs multiple distinct visual directions, an anti-generic redesign, image-to-code exploration, a brand kit, or an explicitly named Taste mode; use Impeccable after a direction is selected."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-31
author: LiNKskills Library
tags: [design, taste, exploration, redesign, visual-variance]
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
scope_out: ["Do not use as the final quality or accessibility authority", "Do not load multiple Taste modes when one explicit mode is requested", "Do not invent brand facts or override a supplied design system", "Do not claim consumer activation or deployment authority"]
format_profile: simple
last_updated: 2026-08-31
---

# Taste Design Exploration

Taste owns divergence: widening the creative search space with genuinely
different visual answers. It is not the final design-quality gate.

## Workflow

1. Validate the task and consumer using
   [`references/schemas.json#/definitions/input`](references/schemas.json).
2. Read [`references/routing.json`](references/routing.json). Select one exact
   Taste member for an explicit mode. For an open exploration, select the
   current `taste-taste-skill` route and ask it for contrasting directions.
3. Load only the selected file under `vendor-skills/taste-design/`. Do not merge every
   mode into a contradictory mega-prompt.
4. Preserve the brief, factual product content, established tokens, and stack.
   Exploration can propose alternatives; it cannot silently replace accepted
   constraints.
5. Hand the selected direction to Impeccable for critique, reconciliation,
   accessibility, responsiveness, and polish before production acceptance.

Taste has higher intentional visual variance than Impeccable. That is its
reason to exist. Impeccable remains the stronger broad design-quality and
production-discipline authority.

## Tool and authority protocol

Use a native CLI for repository inspection and a CLI wrapper for deterministic
rendering or checks. A direct API may be used only through an already-authorized
consumer adapter. MCP is reserved for approved persistent services. When the
task is generalist or exposes more than ten tools, call `get_tool_details` and
retain only the selected capability schemas.

Return the route decision and exploration output under
[`references/schemas.json#/definitions/output`](references/schemas.json). This
skill grants no publishing, activation, image-provider, or deployment authority.
