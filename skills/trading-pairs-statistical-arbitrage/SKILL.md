---
name: trading-pairs-statistical-arbitrage
description: "Assess whether a specified pair/universe has a robust, tradable statistical relationship and produce a scoped research dossier."
usage_trigger: "Use for pair screening, cointegration, spread diagnostics, or statistical-arbitrage research."
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
scope_out: ["Do not place orders, contact a broker, alter a portfolio, or activate live capital.", "Do not invent market data, source access, paid entitlements, historical validation, or method passes.", "Do not treat structural validation or fictional fixtures as strategy validation.", "Do not replace the existing LiNKtrading engine or create runtime JSON state/sidecars."]
format_profile: simple
last_updated: 2026-10-05
---

# Pairs and statistical-arbitrage research

**Status:** Isolated draft v0.1.0. Not admitted, published, selected, activated, or method-qualified. Upstream bytes are preserved as data-only evidence in the external archive described by `references/source-packaging.md` and mapped by `references/source-provenance.json`; they are not active skills.

## Preconditions and native host

Use only when the requested task matches this skill and the required dated inputs are present or can be read from an actually exposed, authorized host capability. Logical `read_file`, `write_file`, and schema-validation labels do not imply those named tools exist: use the host's native persistent-session read/write capability and supplied inline schemas. Do not claim `get_tool_details`, provider, API, CLI or MCP access unless exposed. Tool-routing order is native CLI only if the host exposes and authorizes one; CLI wrapper only if the host exposes it; direct API only if actually authorized; MCP only if an exposed persistent service supports the task. These capability labels do not grant tools or entitlements. Preserve continuity in the one persistent native session; no runtime JSON/JSONL state, sidecar ledger, telemetry rows, provider calls, or external writes are created by this draft.

## Inputs and output contract

Canonical input is `references/schemas.json#/definitions/input`; canonical task-shaped output is `#/definitions/output`. Treat the fictional worked example as a format illustration only. Record supplied facts with source IDs, publication/release time, retrieval/as-of time, unit, period, basis, and transformation. If a required input is absent, return `insufficient_input` or `partial`, identify the exact missing field, and do only independent work that remains valid. Unknown stays null/unknown; never backfill from memory.

## Practical method

1. Define pair universe, listing/industry, as-of, bar frequency, horizon, shortability assumptions and selection search count before looking at outcomes.
2. Validate identifier/corporate-action adjustments, calendars, missingness and price/return fields. Reject misaligned or stale pairs; do not forward-fill large gaps or mix total-return prices with raw prices.
3. Check each series’ integration order; use correlation/return co-movement only to reduce candidates. Do not infer cointegration from correlation or ordinary ADF on raw-price spread.
4. Predeclare model: Engle–Granger regression orientation, intercept/trend, lag selection, sample window and cointegration-specific inference; test both directions and adjust for number of pairs. Use Johansen only for appropriate multivariate design.
5. Freeze estimation window; derive β/α and a unit-explicit residual or log-ratio. Compute stationarity, rolling hedge stability, structural-break, half-life only if residual model supports it, and train/test diagnostics.
6. Calculate current spread z-score using only historical training/rolling parameters; state standardization window and avoid look-ahead. A threshold crossing is a hypothesis, not a signal proof.
7. Evaluate dollar-notional, cointegration unit hedge and market-factor beta separately; include short locate/borrow, dividend financing, fees, spread, impact, gap and legging stress. Missing shortability/cost evidence yields no trade thesis.
8. Compare walk-forward results to each leg and simple controls, disclose all pair searches and failures, and report candidate/no-view with assumptions/invalidation. Conditional advisory sizing is allowed when budget and constraints are supplied; no orders or execution.

## Source-specific branches

- **tradermonty/claude-trading-skills — `skills/pair-trade-screener/SKILL.md` @ `fed1bb34c5b09a28a00ab05262fc78a94a3bea0f`** — Pair screen and spread workflow; correlation only filters. Repair residual inference, hedge units, costs, look-ahead and multiplicity before any signal.
- **agiprolabs/claude-trading-skills — `skills/cointegration-analysis/SKILL.md` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`** — Use Engle–Granger critical values/p-values, lag/deterministic specification, both orientations; preserve Johansen only for appropriate multivariate cases.
- **dr-pabs/Agent-claude-trading-skills — `skills/pair-trade-screener/SKILL.md` @ `4ff3f81c176e46449e388d15676643d4b714a3da`** — Pair screen and spread workflow; correlation only filters. Repair residual inference, hedge units, costs, look-ahead and multiplicity before any signal.
- **mphinance/alpha-skills — `skills/pair-trade-screener/SKILL.md` @ `dc38d201a6b80cfc8e65251eb4a5ead419ac3048`** — Pair screen and spread workflow; correlation only filters. Repair residual inference, hedge units, costs, look-ahead and multiplicity before any signal.

## Failure handling and boundaries

- Missing/stale/conflicting data: stop dependent calculations, preserve observed values, mark partial/no-view and name the next evidence needed.
- Conflicting strategy variants: select by the user’s stated objective; do not average thresholds or silently switch strategy.
- Jane may give conditional research/strategy/position-sizing/exit recommendations when requested and supplied constraints support them. Recommendations are advice only and never authorize external action.
- No manual trading, order placement, broker interaction, portfolio mutation or live activation. Any later activation remains on LiNKtrading and requires Lisa plus Carlos independent authenticated approvals over two channels against the exact version.
- Eric owns software/Nautilus adapters; Sara owns legal/accounting determinations.

## Source provenance and licensing

`references/source-provenance.json` indexes exact source hashes, commits, paths, notices, copies and excluded/unread supports. Quarantine notice states permitted copying basis and modifications. Upstream source scripts were not executed or copied. Source statements do not certify method performance or current API availability.

## Proposed evaluation

`references/eval-suite.json` contains proposed output criteria and adversarial cases only. No behavior evaluation ran. The helper checks supplied JSON shape only and must never manufacture a behavioral PASS.

## References

- `references/schemas.json` — concrete input/output structures.
- `examples/worked-example.json` — fictional task-shaped input/output.
- `references/source-provenance.json` and ``references/source-provenance.json` and `references/source-packaging.md` — data-only source index and quarantine rules; no raw upstream README is routed as a method.` — source index/quarantine.
- `references/eval-suite.json` — proposed actual-output criteria, not executed.
- `references/old-patterns.md`, `references/changelog.md`, `advanced/advanced.md`, `scripts/helper_tool.py` — draft maintenance/structure.
