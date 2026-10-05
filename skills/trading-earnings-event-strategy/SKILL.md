---
name: trading-earnings-event-strategy
description: "Analyze dated earnings reactions and post-event drift from supplied, timestamped evidence without interpreting grades as odds."
usage_trigger: "Analyze dated earnings reactions and post-event drift from supplied, timestamped evidence without interpreting grades as odds."
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
# Earnings reaction and PEAD research

**Status:** isolated unqualified research draft. Jane may give a conditional advisory recommendation only when requested and supported by supplied evidence. No action is authorized.

## Task contract

Input: `references/schemas.json#/definitions/input`. Output: `references/schemas.json#/definitions/output`. Preserve actual units, dates, sources, and unknowns. Use host-native read/write capability only; schemas are inline. A direct API, native CLI, CLI wrapper, or MCP route may be used only when actually exposed and authorized. Do not invoke a named tool that the active host does not expose.

## Integrated practical method

1. Pin issuer, listing, event date, scheduled and actual release times with timezone, source/vintage, price cutoff and venue calendar. Unknown release timing blocks gap attribution or remains separate scenario; never substitute AMC.
2. Separate reported EPS/revenue/guidance surprises from price gaps, pre-event trend, volume, sector/index return and subsequent drift. Preserve positive and negative gap direction.
3. Compute metrics only with supplied observations and explicit denominators/windows. Show source rows, units and whether the price bars were adjusted; missing calendar rows are not evidence of zero events.
4. If PEAD is requested, compare forward event-window returns with a named market/sector control, avoid overlap, include delisted/history coverage and costs, and keep weekly red-candle stages descriptive.
5. Treat source 5-factor scores, grades, catalyst labels and stage names as unvalidated summaries, never probabilities or “institutional accumulation.”
6. Identify counterevidence, data/API degradation, selection bias and sample size. Provide conditional advisory view/watch/no-view; no position sizing, manual order, alert, provider fallback, or persistent state.

## Source and authority limits

Exact MIT entrypoints are preserved as quarantined data-only `SKILL.source.md` copies with root licenses and file-level provenance. They are not active skills. Source scripts and unread supports are excluded. LiNKtrading adapters belong to Eric; Sara owns legal/accounting determinations.

Fictional example: `examples/worked-example.json`. Proposed adversarial inputs: `references/eval-suite.json` (not run). Structural schema validation is not behavioral qualification.
