---
name: trading-fundamental-equity-research
description: "Build an evidence-led issuer research memo with period-aligned financials, valuation assumptions, countercase, and explicit source gaps."
usage_trigger: "Use for company/issuer fundamentals and value range."
version: 0.1.1
release_tag: v0.1.1
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
scope_out: ["Do not submit orders, call a broker, change portfolio state, or activate a live strategy.", "Do not invent data, paid tool access, historical validation, or source API availability.", "Do not treat a schema-valid example or output as method validation.", "Do not replace LiNKtrading with another execution system."]
format_profile: simple

last_updated: 2026-10-05
---

# Fundamental equity research

**Status:** isolated draft, version 0.1.1. This package is not admitted, published, activated, or method-certified. The sources inform independent synthesis; `references/upstream/` is quarantined data only and must never be loaded as an enabled skill.

## Use when

company/issuer fundamentals and value range. Use the nearest specific skill when the request is an adjacent task (issuer fundamentals, earnings, calendar, news, sector/theme, macro, or breadth). Do not broaden a narrow task into a general trading workflow.

## Host capability mapping

Frontmatter `read_file` and `write_file` are portable logical aliases for the host's native persistent-session read/write capability, not promises that tools with those names exist. Use the supplied inline schemas for schema discovery. Do not invoke `read_file` or `write_file` by name unless those exact tools are exposed. Call `get_tool_details` only if the host actually exposes it and additional detail is needed.


`read_file` and `write_file` in the portable manifest are logical categories only. Use the host’s native persistent-session read/write capability and supplied inline schemas. Do not assume named `read_file`, `write_file`, `get_tool_details`, native CLI, CLI wrapper, direct API, or MCP tools exist; use a native CLI, CLI wrapper, direct API, or MCP route only when that capability is actually exposed and authorized.

## Inputs

The canonical input object is `input` in `references/schemas.json`. Required fields:

- `issuer`
- `ticker_or_id`
- `as_of_date`
- `jurisdiction`
- `research_question`
- `periods`
- `provided_filings`

If required values are missing, do not fill them from assumptions. Set `completion_status` to `insufficient_input` or `partial`, name missing fields, and complete only independent analysis that remains valid. For every filing and ledger fact, preserve publication timestamp, measurement period, units, source vintage, and exact source URL or supplied file path.

## Outputs

The canonical output is `output` in `references/schemas.json`; task-specific fields are listed there. Return the result as a structured report with: conclusion, evidence ledger, method and calculation notes, countercase, limitations, and next evidence required. Jane may make conditional advisory strategy, entry/exit, or sizing recommendations when requested and user-supplied constraints support them. State assumptions and invalidation conditions. A recommendation never authorizes an order or external effect.

## Decision path

1. Confirm the request matches this skill and identify the decision horizon. Use only relevant task inputs.
2. Validate required inputs against `references/schemas.json#/definitions/input`; mark missing/stale items explicitly.
3. Apply the method below. Keep reported observations, calculations, inferences, hypotheses, and recommendations separate.
4. Draft the output object; validate its shape against `#/definitions/output`. Structural validity is not evidence of analytical correctness.
5. Deliver the output and classify each conclusion by evidence and uncertainty. Do not create runtime JSON sidecars or task ledgers for this approved draft effort. The host’s persistent native session carries continuity.

## Integrated method

1. Record legal issuer, ticker/exchange/share class, currency, fiscal calendar, consolidated/standalone basis, as-of date, horizon and exact requested output.
2. Use issuer/regulatory filings first; log each document’s publication timestamp, measurement period, units, exact URL or supplied file path, and source vintage; label each number reported, calculated or estimated. Reconcile restatements, conversions and dilution.
3. Analyze segments, unit economics, revenue/earnings quality, cash conversion, balance sheet, capital allocation, competition, industry, regulation and risks; include bear case and disconfirming evidence.
4. If peers requested, explain operating/valuation comparability; normalize periods/accounting/leases/minority/preferred/dilution/one-offs. If no good peers, say so.
5. If valuation requested, state method fit, date, assumptions and inputs; show scenarios/sensitivities and implied expectations, reconcile EV to diluted equity value, and name what invalidates the range.
6. Deliver requested depth, sourced conclusion, countercase, risks, uncertainty and gaps. Jane may recommend research findings to Carlos; no personalized allocation, order or live action. Eric owns adapters; Sara accounting/legal.

## Source-informed branches

Read `references/source-integrated-method.md` before performing this task. It defines the named source-informed branches, conditional inputs, deliverables and limitations; generic placeholder branches are retired.

## Failure handling

- Missing, stale, unreconciled or inaccessible critical data: stop the dependent calculation and return a bounded partial result with the exact gap.
- Incompatible units, periods, event windows or universes: do not merge. Reconcile definitions or report separate views.
- Source rules conflict or are uncalibrated: show the source-specific rule and treat its result as a hypothesis; do not average contradictory rules into a score.
- User requests an order, live activation, or unapproved side effect: provide the permitted advisory artifact only. Any later execution requires the existing LiNKtrading route and Lisa + Carlos independent authenticated two-channel exact-version approval.
- A conditionally recommended size/exit cannot be supported because risk budget, holdings, liquidity, or instrument constraints are missing: omit numeric sizing and state which inputs would change it.

## Rules

### Scope in

- company/issuer fundamentals and value range.
- Evidence-backed conditional advice and explicit counterfactuals, including sizing/exit concepts when requested and sufficiently constrained.

### Scope out

- Order submission, broker interaction, portfolio mutation, live/capital activation, legal/accounting determinations, or replacement execution engines.
- Unverified data/API access, invented fee/fill assumptions, and claims that source examples prove performance.
- Running quarantined upstream code or scripts.

### Ownership

Jane owns research and advisory recommendations. Eric owns software and Nautilus adapter/engine work. Sara owns legal/accounting. For any future activation, Lisa and Carlos independently authenticate on two channels against the exact version. The skill cannot satisfy or bypass that gate.

## Evidence and review standard

Every conclusion that depends on outside data needs source, observation date, release/publication time, units, vintage, and transformation. Evaluate outputs against the criteria in `references/eval-suite.json` using an actual produced artifact. A schema check or fictional example is not a behavioral pass. No model score, backtest, or calibration is asserted by this draft.

## References

- `references/schemas.json` — concrete task input and output contracts.
- `references/source-provenance.json` — bounded source index and file-level source manifest.
- `references/changelog.md` — draft history.
- `references/old-patterns.md` — errors and repair rules from this source audit.
- `references/eval-suite.json` — proposed output-based evaluation cases; none run.
- `references/source-packaging.md` — external source evidence archive and notice boundary.
- `examples/worked-example.json` — fictional end-to-end input/output; no real security, market data, or performance claim.
