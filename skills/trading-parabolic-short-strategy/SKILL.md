---
name: trading-parabolic-short-strategy
description: "Review supplied dated equity evidence for parabolic extension, exhaustion and short-side risk; return watch-only analysis."
usage_trigger: "Review supplied dated equity evidence for parabolic extension, exhaustion and short-side risk; return watch-only analysis."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-05
author: LiNKskills Library (draft)
tags: [trading, research, jane, draft]
engine:
  min_reasoning_tier: balanced
  preferred_model: gpt-6.1-sol
  context_required: 64000
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [read_file, write_file]
dependencies: []
permissions: [fs_read, fs_write]
scope_out: ["No order, trade execution, provider activation, capital mutation, or credentials.", "No runtime JSON state or upstream script execution.", "No method qualification or performance claim."]
format_profile: simple
last_updated: 2026-10-05
---
# Parabolic short setup research

**Status:** isolated unqualified research draft. Jane may give a conditional advisory recommendation only when requested and supported by supplied evidence. No action is authorized.

## Task contract

Input: `references/schemas.json#/definitions/input`. Output: `references/schemas.json#/definitions/output`. Preserve actual units, dates, sources, and unknowns. Use host-native read/write capability only; schemas are inline. A direct API, native CLI, CLI wrapper, or MCP route may be used only when actually exposed and authorized. Do not invoke a named tool that the active host does not expose.

## Integrated practical method

1. Confirm symbol, venue, exact as-of, exchange sessions, adjustment status and bar source; separate daily screen context from intraday chronology.
2. Measure only supplied extension, acceleration, volume, range, liquidity and catalyst facts; state thresholds as user-supplied or unvalidated. Do not infer reversal from extension alone.
3. Check earnings/event dates against publication time and bar session; stale or uncertain catalysts remain a scenario/gap.
4. Report candidate/falsifier conditions and gap/squeeze/volatility/liquidity risks. Do not convert patterns into a broker plan, order, entry/stop, account size or trigger.
5. Treat borrow, locate, short-sale restrictions and applicable law as unknown unless a dated authoritative source/user-supplied evidence establishes them. Never request credentials or call brokers.
6. With unresolved borrow/SSR/session data, state watch-only or blocked. Eric owns adapters; Sara reviews legal/accounting determinations. No persisted state, schedule or automated monitoring.

## Source and authority limits

Exact MIT entrypoints are preserved as quarantined data-only `SKILL.source.md` copies with root licenses and file-level provenance. They are not active skills. Source scripts and unread supports are excluded. LiNKtrading adapters belong to Eric; Sara owns legal/accounting determinations.

Fictional example: `examples/worked-example.json`. Proposed adversarial inputs: `references/eval-suite.json` (not run). Structural schema validation is not behavioral qualification.
