---
name: trading-breakout-momentum-strategy
description: "Research a selected VCP, breakout/momentum, episodic-pivot, large-mover study, or squeeze/pullback variant from dated supplied equity evidence."
usage_trigger: "Breakout, momentum burst, VCP, episodic pivot, 20 percent mover event study, or squeeze/pullback research."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-05
author: LiNKskills Library (draft)
tags: [trading, equity, strategy-research, draft]
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
scope_out: ["No order templates, broker calls, position sizing or execution.", "No provider access or credential use is assumed.", "No persistence sidecar, source scripts or scheduled scan activation.", "No performance edge or profitability claims from scores or selected survivors."]
format_profile: simple
last_updated: 2026-10-05
---
# Breakout and momentum strategy research

**Status:** isolated unqualified draft. Jane may provide a conditional strategy view or compare methods when requested. It never places orders or prescribes unauthorized capital use.

## Inputs and outputs

Use the task-shaped `input` and `output` definitions in `references/schemas.json`. Require a single explicit `variant`, dated point-in-time universe snapshot, venue/session calendar, adjustment and bar policy, source snapshot, parameter provenance, OHLCV with units, and publication time/source for events. Missing data stays explicit. The output is a research-only candidate/watch/reject list with matched rules, evidence rows, invalidation, counterevidence and population limits.

## Integrated method

1. Choose one branch: VCP contraction, momentum burst, episodic catalyst, 20% mover cohort study, or squeeze/pullback. Keep their features and scores separate.
2. Pin universe membership, venue calendar, date cutoff, corporate-action treatment, bar source/vintage, price/volume units, benchmark and event publication timestamp. Reject stale/mismatched rows.
3. Compute only observable branch-specific facts from supplied bars/events: VCP trend/contraction/pivot descriptors; burst close/range expansion and volume ratios; event catalyst plus gap/volume response; or the specified squeeze/pullback indicator state.
4. Compare only against explicit user-supplied parameters. Label source-derived defaults as unvalidated. Produce candidate/watch/reject with invalidation, failed conditions and conflicting evidence. Do not use another branch’s grade as corroboration.
5. For cohort research, include failed setups, down movers, delisted names, historical universes, costs and a control group. Point-in-time outcomes require only future bars after each as-of and non-overlapping cohort definitions. Selected winners or a minimum sample count cannot establish edge.
6. Report coverage, survivorship, lookahead, event timing, liquidity, slippage, borrow and benchmark gaps. Leave performance or causal conclusions unresolved until a separate validated study.
7. Return a descriptive research watchlist only. Never produce orders, account-sized positions, persistence files, or activation instructions.

## Capability and source boundary

Portable read/write labels map to the host’s native persistent-session read/write capability; schemas are inline. Use only actually exposed, authorized host tools. A direct API, native CLI, CLI wrapper, or MCP route is permitted only when actually exposed and authorized; upstream FMP, Alpaca, TraderDaddy or broker mentions create no entitlement. Keep continuity in the native session; do not add JSON/JSONL sidecars. Eric owns the existing LiNKtrading/Nautilus adapter boundary.

Exact MIT source entrypoints are quarantined as data-only `SKILL.source.md` copies under `references/upstream/`; see per-file pinned provenance. No upstream scripts are copied or executed. Private vendor-specific coil/magnet sources are preserved only as audited source references and are not selectable runtime methods. Linked methodology supports remain open until individually read.

## Checks

Validate actual input/output shape against `references/schemas.json`; this checks structure only. Review dates, units, parameters, source rows, branch identity, failed cases and gaps. `examples/worked-example.json` is fictional. Adversarial cases are proposed, not run; no behavioral qualification or profitability is claimed.

## Contract references

- Input: `references/schemas.json#/definitions/input`
- Output: `references/schemas.json#/definitions/output`
- Fictional example: `examples/worked-example.json`
- Proposed evaluation suite: `references/eval-suite.json`
- Source hashes and notices: `references/source-provenance.json`
