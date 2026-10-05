---
name: trading-options-volatility-strategy
description: "Analyze supplied options contracts or market view with exact payoff, Greeks, volatility surface/context and downside scenarios."
usage_trigger: "Use for options strategy design, payoff/Greeks, implied-versus-realized volatility, earnings/0DTE risk, or multi-leg scenario analysis."
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

# Options strategy and volatility research

**Status:** Isolated draft v0.1.0. Not admitted, published, selected, activated, or method-qualified. Upstream bytes are preserved as data-only evidence in the external archive described by `references/source-packaging.md` and mapped by `references/source-provenance.json`; they are not active skills.

## Preconditions and native host

Use only when the requested task matches this skill and the required dated inputs are present or can be read from an actually exposed, authorized host capability. Logical `read_file`, `write_file`, and schema-validation labels do not imply those named tools exist: use the host's native persistent-session read/write capability and supplied inline schemas. Do not claim `get_tool_details`, provider, API, CLI or MCP access unless exposed. Tool-routing order is native CLI only if the host exposes and authorizes one; CLI wrapper only if the host exposes it; direct API only if actually authorized; MCP only if an exposed persistent service supports the task. These capability labels do not grant tools or entitlements. Preserve continuity in the one persistent native session; no runtime JSON/JSONL state, sidecar ledger, telemetry rows, provider calls, or external writes are created by this draft.

## Inputs and output contract

Canonical input is `references/schemas.json#/definitions/input`; canonical task-shaped output is `#/definitions/output`. Treat the fictional worked example as a format illustration only. Record supplied facts with source IDs, publication/release time, retrieval/as-of time, unit, period, basis, and transformation. If a required input is absent, return `insufficient_input` or `partial`, identify the exact missing field, and do only independent work that remains valid. Unknown stays null/unknown; never backfill from memory.

## Practical method

1. Parse the view, task horizon, contract(s), style, settlement, multiplier, deliverables, corporate-action adjustments, signed quantity, position basis/entry price and user risk constraints. Missing any term that changes payoff blocks dependent calculations.
2. Validate dated underlying and option quotes, bid/ask/size, expiry calendar, rates curve, discrete dividends, distributions and catalysts. Do not use historical volatility as implied volatility; if IV absent, mark IV/Greeks/surface unavailable or explicitly model a separate assumption.
3. Check quote coherence, contract identity, no-arbitrage bounds/parity under matching style/dividends and liquidity. Reject crossed/zero/stale markets or mismatched deliverables rather than choosing a convenient midpoint.
4. Compute exact expiration payoff per leg (signed quantity × multiplier) and strategy aggregate. Derive break-evens and maximum gain/loss; explicitly identify theoretically unbounded losses and assignment/exercise/settlement exposure.
5. For pre-expiry valuation, specify model/style and calibrated/supplied surface; show model value distinct from executable market quote. Report Greek convention and units; aggregate only with exact position quantities.
6. If surface supplied, report timestamp, spot, term structure, ATM vols, skew/smile, relative-value metrics and quote quality; compare realized vol only at matched return definition/calendar and tenor.
7. Stress spot gaps, IV level/skew/term, time, rates/dividends, event gap, liquidity and assignment; probability/expected value only when a calibrated distribution, sample and assumptions are explicit. Never use a plotted grid share as probability.
8. Compare conditional structures by capital/max loss, tail/assignment/liquidity and risk factors. Jane may recommend strategies, sizing, exit or adjustments as conditional advisory when inputs support them; no order, broker call or live activation.

## Source-specific branches

- **tradermonty/claude-trading-skills — `skills/options-strategy-advisor/SKILL.md` @ `fed1bb34c5b09a28a00ab05262fc78a94a3bea0f`** — Use leg-by-leg payoff/Greeks/scenarios after contract-term validation; discard fabricated probabilities and stale assumptions.
- **LLMQuant/skills — `skills/llmquant-equity-derivatives/SKILL.md` @ `1918237467c2dff4cc97a18ebc0892dfd46e8129`** — LLMQuant route indices describe desired data/workflow shapes only; named data tools are unavailable, no provider access is presumed.
- **LLMQuant/skills — `skills/llmquant-options/SKILL.md` @ `1918237467c2dff4cc97a18ebc0892dfd46e8129`** — LLMQuant route indices describe desired data/workflow shapes only; named data tools are unavailable, no provider access is presumed.
- **agiprolabs/claude-trading-skills — `skills/options-pricing/SKILL.md` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`** — Crypto-focused stub with planned features; no implied full implementation or adoptable production model.
- **agiprolabs/claude-trading-skills — `skills/volatility-modeling/SKILL.md` @ `981e1d736cdc02bdc1c55c74ec9224e956414706`** — Volatility estimators are candidate calculations; crypto calendar/regime constants are not transferred to equities without fit evidence.
- **anthropics/financial-services — `plugins/partner-built/lseg/skills/option-vol-analysis/SKILL.md` @ `574ed3624aebd0418c7e96cd101262f30210ab26`** — Surface/Greeks/history comparison workflow; named MCP tools unavailable, so requires user-supplied authorized data.
- **dr-pabs/Agent-claude-trading-skills — `skills/options-strategy-advisor/SKILL.md` @ `4ff3f81c176e46449e388d15676643d4b714a3da`** — Use leg-by-leg payoff/Greeks/scenarios after contract-term validation; discard fabricated probabilities and stale assumptions.
- **mphinance/alpha-skills — `skills/0dte-flow/SKILL.md` @ `dc38d201a6b80cfc8e65251eb4a5ead419ac3048`** — Private audit only; excluded from package because entrypoint includes direct order/API commands and credential/account references.
- **mphinance/alpha-skills — `skills/options-strategy-advisor/SKILL.md` @ `dc38d201a6b80cfc8e65251eb4a5ead419ac3048`** — Use leg-by-leg payoff/Greeks/scenarios after contract-term validation; discard fabricated probabilities and stale assumptions.

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
