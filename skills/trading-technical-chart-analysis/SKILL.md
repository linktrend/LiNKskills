---
name: trading-technical-chart-analysis
description: "Describe user-supplied dated charts or OHLC data: trend structure, levels, moving-average context, volume and patterns with alternate interpretations and invalidation conditions."
usage_trigger: User asks for a technical chart reading, support/resistance description, or indicator interpretation from supplied chart or bars.
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-05
author: LiNKskills Library
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
scope_out: ["No assumed market data/provider access, indicator library, or prices not visible in supplied evidence.", "No numeric probability, target, performance claim, order, or live activation absent user request and evidence.", "No automatic script or source asset execution."]
format_profile: simple
last_updated: 2026-10-05
---

# Technical chart reading

**Status:** isolated unqualified draft, not admitted/published/activated. Jane can provide advisory analysis, including conditional entry/exit or sizing ideas when explicitly asked and when evidence and user constraints support it; this skill never submits orders.

## Host and input contract

Portable `read_file`/`write_file` manifest labels map to host-native persistent-session read/write capability. Use supplied inline schema; assume no named tools, native CLI, CLI wrapper, direct API, MCP or provider access. Eric owns LiNKtrading adapters. Required inputs are in `references/schemas.json#/definitions/input`: symbol/market, source, as-of, timeframe, timezone/session, and either a user chart or complete OHLCV rows with units and adjustment basis. If chart crop, axis, timeframe, volume, or dates are unreadable, list the exact missing observations.

## Method

1. Confirm instrument, venue, timeframe, as-of cutoff, session/calendar, source and adjustment basis. Use completed bars only.
2. Describe observed swing sequence and range; identify candidate support/resistance zones with the observed pivots and their dates. A level is a historical reference, not a guarantee or price target.
3. If moving averages or indicators are requested, state formula, period, price basis, warmup rows, missing-bar handling, and library/version if supplied. Do not import source thresholds as universal signals.
4. Describe volume and candle patterns only where visible and defined; distinguish observed values from interpretation and give a credible opposing explanation.
5. Offer conditional scenarios through level/invalidation pairs. Do not assign precise probabilities or targets from an uncalibrated chart template. Provide numeric price levels only if they are directly observable or mechanically calculated from complete supplied bars.
6. A contrarian-confirmation checklist is a separate explicitly requested variant in `examples/source-variants.json`; the listed strict rules require completed weekly OHLC and matching crowd direction. Do not execute its source script. If chart resolution cannot establish strict inequalities or bar counts, return `insufficient_input`, not a fabricated verdict.
7. Return a concise structured memo, preserve source/date/units, uncertainty and limitations, and validate shape. Structural validity is not trading-method validation.

## Output

Use `references/schemas.json#/definitions/output`: observation ledger, level evidence, scenario conditions, invalidation, countercase, missing data, and limitations. No runtime state JSON, task ledger, or telemetry sidecar; native session is the continuity surface.

## Source branches

The weekly chart workflow contributes an orderly observational checklist. Contrarian-confirmation uses a distinct key reversal, failed extreme, failed breakout and continuation veto sequence. TA-Lib/pandas-ta/custom crypto indicators are optional definitions inventory only: no dependency, formula claim, or fixed threshold is enabled. Do not blend crypto indicator packages with the weekly chart method.

## Source closure

See `references/source-provenance.json`. The chart framework and contrarian checklist were read and copied to quarantined references. Indicator libraries, optional formulas, source scripts, data contracts and chart provider behavior remain unverified and excluded. No scripts were run.
