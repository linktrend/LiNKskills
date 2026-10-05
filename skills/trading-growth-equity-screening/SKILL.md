---
name: trading-growth-equity-screening
description: "Screen a specified equity universe under distinct CANSLIM or GARP theses and produce a sourced research shortlist."
usage_trigger: "Use for a requested CANSLIM, growth-momentum, GARP, or undervalued-growth screen."
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

# Growth equity screening

**Status:** Isolated draft v0.1.0. Not admitted, published, selected, activated, or method-qualified. Upstream bytes are preserved as data-only evidence in the external archive described by `references/source-packaging.md` and mapped by `references/source-provenance.json`; they are not active skills.

## Preconditions and native host

Use only when the requested task matches this skill and the required dated inputs are present or can be read from an actually exposed, authorized host capability. Logical `read_file`, `write_file`, and schema-validation labels do not imply those named tools exist: use the host's native persistent-session read/write capability and supplied inline schemas. Do not claim `get_tool_details`, provider, API, CLI or MCP access unless exposed. Tool-routing order is native CLI only if the host exposes and authorizes one; CLI wrapper only if the host exposes it; direct API only if actually authorized; MCP only if an exposed persistent service supports the task. These capability labels do not grant tools or entitlements. Preserve continuity in the one persistent native session; no runtime JSON/JSONL state, sidecar ledger, telemetry rows, provider calls, or external writes are created by this draft.

## Inputs and output contract

Canonical input is `references/schemas.json#/definitions/input`; canonical task-shaped output is `#/definitions/output`. Treat the fictional worked example as a format illustration only. Record supplied facts with source IDs, publication/release time, retrieval/as-of time, unit, period, basis, and transformation. If a required input is absent, return `insufficient_input` or `partial`, identify the exact missing field, and do only independent work that remains valid. Unknown stays null/unknown; never backfill from memory.

## Practical method

1. Confirm variant, universe, exchange/security types, as-of date, horizon, liquidity floor, and whether requested scope is named securities or defined universe.
2. Build a point-in-time universe inventory with inclusion/exclusion counts and source vintage. Separate discovery filters from verified candidate facts.
3. Record each observation with symbol, metric, value, unit, period, publication/release timestamp, retrieval/as-of, source URL/file, and reported/calculated/estimated flag; do not mix periods/bases.
4. For CANSLIM, present C/A/N/S/L/I/M separately with definitions and evidence; preserve unavailable components as unknown. Do not apply source weightings or buy bands as validated evidence.
5. For GARP, normalize current/FY1/NTM earnings and FCF/share; trace revenue, margin, taxes, interest, diluted shares and adjustments independently; reconcile SBC/dilution, ROIC, leverage, sector/cycle and valuation scenarios. Never solve forecast drivers backward from target EPS.
6. Verify material facts against issuer/regulatory sources where supplied; label vendor estimates and model assumptions. Use peer comparisons only on comparable periods, accounting and sector measures.
7. Report candidate rows with criterion-level support, contrary evidence, sensitivity, exclusions and exact coverage scope. If universe/pool or source freshness is incomplete, cap conclusion to named/bounded scope or no-view.
8. Give a conditional research/watch view with thesis, invalidation, next evidence and potential strategy considerations when requested. Advisory recommendations including conditional size/exit are allowed only when user-supplied constraints support them; no order or external effect.

## Source-specific branches

- **tradermonty/claude-trading-skills — `skills/canslim-screener/SKILL.md` @ `fed1bb34c5b09a28a00ab05262fc78a94a3bea0f`** — Retain component-level C/A/N/S/L/I/M measurements and missingness; do not carry over score bands, weights or buy/cash mandates as validated.
- **dr-pabs/Agent-claude-trading-skills — `skills/canslim-screener/SKILL.md` @ `4ff3f81c176e46449e388d15676643d4b714a3da`** — Retain component-level C/A/N/S/L/I/M measurements and missingness; do not carry over score bands, weights or buy/cash mandates as validated.
- **dr-pabs/Agent-claude-trading-skills — `skills/finviz-screener/SKILL.md` @ `4ff3f81c176e46449e388d15676643d4b714a3da`** — Translate to a candidate-filter proposal only; filter codes/URLs are not verified data or issuer evidence.
- **mphinance/alpha-skills — `skills/batch-scanner/SKILL.md` @ `dc38d201a6b80cfc8e65251eb4a5ead419ac3048`** — Excluded because the source requires scheduled multi-strategy execution and an external Google Sheets webhook/write.
- **mphinance/alpha-skills — `skills/canslim-screener/SKILL.md` @ `dc38d201a6b80cfc8e65251eb4a5ead419ac3048`** — Retain component-level C/A/N/S/L/I/M measurements and missingness; do not carry over score bands, weights or buy/cash mandates as validated.
- **mphinance/alpha-skills — `skills/finviz-screener/SKILL.md` @ `dc38d201a6b80cfc8e65251eb4a5ead419ac3048`** — Translate to a candidate-filter proposal only; filter codes/URLs are not verified data or issuer evidence.
- **tradermonty/claude-trading-skills — `skills/finviz-screener/SKILL.md` @ `fed1bb34c5b09a28a00ab05262fc78a94a3bea0f`** — Translate to a candidate-filter proposal only; filter codes/URLs are not verified data or issuer evidence.
- **tradermonty/claude-trading-skills — `skills/us-undervalued-growth-screener/SKILL.md` @ `fed1bb34c5b09a28a00ab05262fc78a94a3bea0f`** — Preserve source-level coverage audits, same-basis forward horizons, independent driver bridges, quality/cycle gates; scripts/provider and publication path unadopted.

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
