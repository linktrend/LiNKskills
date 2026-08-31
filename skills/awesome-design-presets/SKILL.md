---
name: awesome-design-presets
description: "Selects one exact visual-style preset from the complete Awesome Design Skills collection without treating presets as procedural design authorities."
usage_trigger: "Use when a website or application needs a named aesthetic preset or a brief-to-style recommendation from the Awesome Design Skills library; use Taste for broad divergence and Impeccable for design-quality control."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-31
author: LiNKskills Library
tags: [design, presets, visual-style, website, vertical-kits]
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
scope_out: ["Do not load all 67 presets for one task", "Do not treat the awesome-impeccable preset as the official Impeccable system", "Do not override a supplied brand or design system", "Do not let a preset bypass accessibility, responsive, implementation, or consumer gates"]
format_profile: simple
last_updated: 2026-08-31
---

# Awesome Design Presets

The complete 67-member collection is retained as a style library. Each member
is a visual reference, not an independently authoritative design process.

## Selection

1. Validate the brief using
   [`references/schemas.json#/definitions/input`](references/schemas.json).
2. If the user names a style, select its exact namespaced route from
   [`references/routing.json`](references/routing.json).
3. Otherwise compare the brief with the preset names and return at most two
   candidates. Do not choose based only on a fashionable effect.
4. Load the selected `SKILL.md` and `DESIGN.md` under the exact
   `vendor-skills/awesome-design/` member directory.
   Treat arbitrary example brands, fonts, palettes, and industries as preset
   defaults—not facts about the user's business.
5. Apply the selected style through the consumer's frontend implementation
   process, then use Impeccable and UI/UX verification to test the result.

The member named `awesome-impeccable` is deliberately namespaced. It is a
cream/orange preset and is unrelated to the official Impeccable design system.

## Tool and authority protocol

Use a native CLI for token and component inspection and a CLI wrapper for
rendering or visual checks. Use a direct API only through an authorized
consumer adapter; reserve MCP for an approved persistent service. If the task
becomes generalist or exposes more than ten tools, call `get_tool_details` and
load only the selected schemas.

Return the selection under
[`references/schemas.json#/definitions/output`](references/schemas.json).
Preset selection does not approve copy, branding, dependencies, publication,
deployment, or consumer activation.
