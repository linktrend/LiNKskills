---
name: ui-ux-guardian
description: "Visual acceptance of a running screen: Impeccable audit/critique/live, motion review when motion shipped, gstack live visual QA, and Playwright regression. Report; do not restyle."
usage_trigger: "Use in Verification whenever the product has a screen. Always for screen products. Motion review when motion was in the briefs."
version: 1.0.0
release_tag: v1.0.0
created: 2026-02-25
author: LiNKskills Library
tags: [design-system, ux, regression, visual-acceptance]
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5
  context_required: 128000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [write_file, read_file, list_dir, get_tool_details]
dependencies: [playwright-cli, fast-playwright]
permissions: [fs_read, fs_write, shell_exec]
scope_out: ["Do not approve visual changes without evidence", "Do not restyle during Verification", "Do not skip accessibility and responsive checks"]
format_profile: simple
last_updated: 2026-09-22
---

# ui-ux-guardian

This card is **visual check** in Verification. Always if there is a screen. Repair is `diagnose-investigate` then `implement` / `impeccable-design-system`. Do not restyle here.

Companions in this package: `references/impeccable-audit.md`, `impeccable-critique.md`, `impeccable-live.md`, `gstack-design-review-procedure.md`, `emil-review-animations.md`. Follow them; do not open upstream repos.

## 1. Match the locked sample

Screenshot the running routes. Compare to `design-sample` and `DESIGN.md`. Fail mismatches (spacing, type, color, hierarchy), not taste opinions.

## 2. Impeccable critique / audit

Heuristic UX critique (findable primary action, errors recoverable, empty states). Technical audit: contrast, a11y names, responsive, keyboard. Live variant picking is optional evidence, not a redesign session.

## 3. Motion (if briefs allowed motion)

Run Emil review standards: justified, frequency, easing, duration, origin, reduced motion. Default to flag.

## 4. gstack live visual QA

Before/after screenshots on named pages. Console errors. Broken layout at the agreed widths. Report only.

## 5. Playwright / Studio regression

If baselines exist, capture and diff. Block approval when visual diff exceeds policy. Save screenshots as task-local files.

## Tooling protocol (CLI-first)

**Native CLI** for artifacts; **CLI wrapper** (`playwright-cli`) for snapshots; **direct API** only if wrappers fail; **MCP** (`fast-playwright`) only for an approved session. Generalist or >10 tools: `get_tool_details`.

Contracts: `references/schemas.json#/definitions/input` and `#/definitions/output`.
