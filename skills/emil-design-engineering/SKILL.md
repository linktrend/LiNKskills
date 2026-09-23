---
name: emil-design-engineering
description: "Motion set: decide whether to animate, build web or Expo motion, review, improve, and name vocabulary. Not look, not visual acceptance."
usage_trigger: "Use on Execution screen issues when the brief allows motion, or in Verification when motion was in the briefs. Use animate-expo only for native. Toasts are ask-sonner. UI kit pick is pick-ui-library."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-31
author: LiNKskills Library
tags: [design-engineering, motion, animation, expo]
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
scope_out: ["Do not animate 100+/day or keyboard actions", "Do not use Expo recipes on ordinary web", "Do not restyle the locked sample", "Do not review non-motion diffs"]
format_profile: simple
last_updated: 2026-09-22
---

# Emil Design Engineering

This card is **motion**. Look is `taste-design-exploration` / `awesome-design-presets`. Craft is `impeccable-design-system`. Visual check is `ui-ux-guardian`.

Companions in this package: `references/animate.md`, `RECIPES.md`, `STANDARDS.md`, `animate-expo.md`, `review-animations.md`, `improve-animations.md`, `find-animation-opportunities.md`, `animation-vocabulary.md`, `impeccable-animate.md`. Follow them; do not open Emil's GitHub.

## Build sequence (web)

1. **Should it animate?** 100+/day or keyboard: never. Tens/day: near-imperceptible or nothing. Occasional: standard. Rare: delight budget only.
2. **Purpose** in one word: feedback, spatial consistency, state indication, preventing a jarring change, explanation (onboarding), or delight (rare only). Can't name it → don't build it.
3. **Cheapest tool:** CSS transition → `@starting-style` → CSS animation → WAAPI → Motion. Do not install a library for a fade. Components (toast/drawer/menu) go to `pick-ui-library`.
4. **Properties:** `transform` and `opacity` (clip-path sanctioned; height only for accordions). Never `scale(0)` — start `scale(0.9–0.97)` + opacity. Origin at the trigger for popovers; modals stay centered.
5. **Curve and duration** from `STANDARDS.md` / `RECIPES.md`. No invented `cubic-bezier(0.4, 0, 0.2, 1)`. `ease-in` on UI entrance is a block. UI under 300ms unless justified. Extend existing tokens.
6. **Interrupt and exit** must be defined. Reduced motion and hover gating ship with the animation.

Impeccable animate folds into this same sequence (one authored moment, exponential ease-out, not a fade on every section).

## Expo / RN

Only when the brief is native. Use `references/animate-expo.md`: Reanimated, gestures, sheets, haptics, UI thread.

## Review (Verification or after a motion issue)

Default to flagging. Ten standards: justified; frequency-appropriate; responsive easing; sub-300ms UI; origin/physical correctness; interruptible; no layout-thrashing properties; reduced-motion path; tokens not a fork; no `scale(0)`. Full tables in `STANDARDS.md`.

## Improve / find

Read-only audit → self-contained plans (`improve-animations`). Hunt missing motion with a rejected-candidates list (`find-animation-opportunities`). Vocabulary-only naming is `animation-vocabulary` — it does not implement.

Apple-like **look** is not this card; it is direction (`taste-design-exploration`). Swift language is not design.

## Tooling protocol (CLI-first)

**Native CLI**, then **CLI wrapper**, **direct API** only if authorized, **MCP** only for an approved adapter. Generalist or >10 tools: `get_tool_details`.

Contracts: `references/schemas.json#/definitions/input` and `#/definitions/output`.
