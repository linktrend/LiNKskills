---
name: trading-contrarian-mean-reversion
description: "Assess a specified price or spread series for reversible behavior and distinguish statistical diagnostics from tradeability."
usage_trigger: "Assess a specified price or spread series for reversible behavior and distinguish statistical diagnostics from tradeability."
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
# Contrarian and mean-reversion research

**Status:** isolated unqualified research draft. Jane may give a conditional advisory recommendation only when requested and supported by supplied evidence. No action is authorized.

## Task contract

Input: `references/schemas.json#/definitions/input`. Output: `references/schemas.json#/definitions/output`. Preserve actual units, dates, sources, and unknowns. Use host-native read/write capability only; schemas are inline. A direct API, native CLI, CLI wrapper, or MCP route may be used only when actually exposed and authorized. Do not invoke a named tool that the active host does not expose.

## Integrated practical method

1. Pin asset/spread definition, venue, units, sampling interval, transformation, source snapshot and full date range. Reject missing/duplicate timestamps and corporate-action inconsistencies.
2. Plot/check level and return series, autocorrelation, outliers, missing intervals, structural breaks and regime changes; do not presume price stationarity.
3. Apply prespecified stationarity/reversion diagnostics with test name, null, lags, window, statistic, p-value/interval and limitations. ADF failure to reject a unit root or Hurst below 0.5 alone does not prove tradable mean reversion.
4. Estimate AR(1)/OU speed, long-run mean and half-life only if parameter sign/stability and sample adequacy support interpretation; show units in bars and convert to calendar time only with calendar mapping.
5. Compare any proposed z-score entry/exit rule only using past-only rolling estimates and declared thresholds. Identify threshold selection, repeated tests, regime dependence and signal timing.
6. Include spread/commission/slippage/borrow/funding constraints supplied by the user and an out-of-sample walk-forward design; never derive performance from in-sample fit.
7. Keep exhaustion-hammer and contrarian confirmation as separate optional descriptive evidence, not proof of reversion. Return candidate/reject/insufficient evidence and conditional advisory view only; no sizing/orders.

## Source and authority limits

Exact MIT entrypoints are preserved as quarantined data-only `SKILL.source.md` copies with root licenses and file-level provenance. They are not active skills. Source scripts and unread supports are excluded. LiNKtrading adapters belong to Eric; Sara owns legal/accounting determinations.

Fictional example: `examples/worked-example.json`. Proposed adversarial inputs: `references/eval-suite.json` (not run). Structural schema validation is not behavioral qualification.
