---
name: impeccable-design-system
description: "Routes interface design, redesign, critique, audit, and polish work through the exact Impeccable source while preserving the user's brief and consumer delivery gates."
usage_trigger: "Use for end-to-end website or application interface design quality, including shaping, critique, audit, typography, layout, responsive adaptation, hardening, and final polish; use Taste first when the task is primarily divergent visual exploration."
version: 1.0.0
release_tag: v1.0.0
created: 2026-08-31
author: LiNKskills Library
tags: [design, ui, ux, critique, polish, impeccable]
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
scope_out: ["Do not use for divergent style generation when Taste is the primary task", "Do not replace an explicit brief with Impeccable's defaults", "Do not bypass consumer review, release, deployment, or permission gates", "Do not enable hooks or mutate project configuration without task authority"]
format_profile: simple
last_updated: 2026-08-31
---

# Impeccable Design System

Use Impeccable as the canonical end-to-end design-quality authority. It owns
interface shaping, critique, audit, correction, hardening, and polish. It does
not own wide visual divergence (Taste), named aesthetic presets (Awesome), or
specialist motion/native implementation (Emil Kowalski).

## Route one operation

1. Read the input contract at
   [`references/schemas.json#/definitions/input`](references/schemas.json).
2. If the request explicitly names an Impeccable command, select that route.
   Otherwise use `python3 scripts/helper_tool.py --route "<task>"` as a routing
   aid and fail closed on `AMBIGUOUS` or `NOT_APPLICABLE`.
3. Read [`vendor-skills/impeccable/impeccable/SKILL.md`](../../vendor-skills/impeccable/impeccable/SKILL.md),
   then only the command reference it directs you to. Preserve its setup and
   bounded-verification requirements.
4. Inspect the actual repository's incumbent design truth and the user's brief.
   The brief wins over any general aesthetic preference.
5. Return or implement only the requested design scope. Consumer-owned review,
   Git, deployment, and permission rules remain authoritative.

## Boundary with the other design families

- Use **Taste Design Exploration** to generate genuinely different visual
  directions before a direction has been selected.
- Use **Awesome Design Presets** when a named or selected visual style should be
  applied as a design reference.
- Use **Emil Design Engineering** for motion, animation review, Expo, Swift,
  Apple interaction, Sonner, or specialist prototyping.
- Use this skill after exploration to critique, reconcile, harden, and polish
  the chosen direction.

Do not load competing design families merely because they are available. A
single task may move from exploration to polish sequentially, but each phase
has one authority and an explicit handoff.

## Tool and authority protocol

Use a native CLI for local inspection, then a deterministic CLI wrapper when
the selected source provides one. Use a direct API only when the consumer has
already authorized the exact service and a CLI cannot perform the operation.
Use MCP only for an approved persistent adapter. If the task becomes generalist
or exposes more than ten tools, call `get_tool_details` and load only the chosen
capability schemas.

The output contract is
[`references/schemas.json#/definitions/output`](references/schemas.json). This
skill does not itself activate a release, grant tool authority, or declare a
design accepted.
