---
name: trading-microstructure-execution-analysis
description: "Orderflow, price formation, MEV and execution-quality analysis. Isolated draft; advisory analysis only."
usage_trigger: "User asks to explain supplied historical market data, trade execution quality, order-flow evidence, market impact or transaction-level MEV exposure."
version: 0.1.0
release_tag: v0.1.0
created: 2026-10-05
author: LiNKskills Library (isolated draft)
tags: [trading, research, advisory, draft]
engine:
  min_reasoning_tier: high
  context_required: 32000
  preferred_model: gpt-6.1-sol
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
tools: [read_file, write_file]
dependencies: []
permissions: [fs_read, fs_write]
scope_out: ["No provider, broker, exchange, wallet, credential, API, order, signature, deployment, live activation, or policy mutation.", "No claims of current external contracts or installed runtime versions unless separately evidenced.", "No tax/legal/accounting-final determination; Sara owns those topics."]
format_profile: heavy
persistence:
  required: true
  state_path: .workdir/tasks/{{task_id}}/state.jsonl
  state_authority: existing LiNKtrading native session and Program Ledger references only
  path_semantics: validator compatibility alias only; actual task state stays in native session and Program Ledger records
last_updated: 2026-10-05
---

# Microstructure and execution analysis

## Use when

Use for a historical, supplied-data question about spread/depth, price formation, order flow, market impact, execution quality or a specific MEV hypothesis. Jane may recommend changes to a strategy, urgency, sizing or proposed limits from evidence. This skill does not obtain quotes, route orders, connect a venue, sign transactions or control an execution adapter.

## Inputs

- Instrument/contract, venue, session calendar/timezone, reporting currency, time range, clock precision and benchmark definition.
- Raw quotes, trades, depth snapshots and/or event stream with source, sequence, event versus receive time, side, units, price precision, lot/tick and multiplier.
- For execution review: order intent/arrival time and benchmark, fills/partial fills/cancels, remaining quantity, fees/rebates, financing and known route/latency data.
- For crypto: token decimals, pool/route identifiers, chain block/transaction ordering, gas/tip/priority costs and transaction/fill receipts if the question is MEV.
- Sampling gaps, duplicated routes, clock skew, corrections, fee schedule and known provider transformations. Missing facts stay unknown.

## Outputs

- Data-quality and event-timeline table, including clock/sequence conflicts and missingness.
- Spread, depth and size-specific impact profile by side and horizon; distinguish displayed, realized and effective spread.
- Execution-cost bridge from arrival benchmark to fills/unfilled remainder with fees/rebates and sign convention.
- MEV classification (observed pattern, plausible hypothesis, not evidenced) with transaction-level evidence limits.
- Advisory recommendations and alternatives with uncertainty; no order instructions or automatic thresholds.


## Decision path

1. Confirm the request matches the named task and that the source snapshot/period/decision question are available.
2. Resolve the exact task-specific contract terms, event time, units, signs, currency, denominator and owner boundaries before calculating.
3. If critical evidence is missing, produce a bounded partial answer with exact gaps; do not invent defaults or make the unsupported conclusion.
4. Route technical adapter/runtime/API claims to Eric and legal, accounting or tax conclusions to Sara. Jane retains advisory strategy authority.
5. Return the requested analysis with reproducible methods, uncertainty, counterevidence, limitations and any advisory proposal separated from action.

## Evidence standard

Every material finding identifies its source reference and as-of time. Every numerical result states units, sign convention, denominator, precision and transformation. Distinguish observed, calculated, estimated, hypothesis and unknown. State sample/window coverage and assumptions. Do not claim causation, certainty, profitability, readiness, or current integration from a source example alone.

## Blocker standard

Stop only the affected conclusion when a task-critical input is absent or contradictory. Name the missing field, why it changes the result, and its owner. Continue independent bounded analysis where possible. An unresolved metric remains unknown; it is not zero, pass, healthy, or policy-compliant.

## Workflow

### Phase 1: Intake

Freeze question, date/time range, source version, relevant identifiers, output currency, and requested recommendation scope. Map supplied evidence to the input contract.

### Phase 2: Analysis

Reconcile data first. Apply only the applicable task branch. Keep source facts, calculations, scenarios and hypotheses separate. Run adversarial sensitivity reasoning in the report; do not execute upstream code or external integrations.

### Phase 3: Output

Produce the schema-shaped task deliverable, exact unresolved gaps, evidence references, uncertainty, strongest alternative explanation and any advisory-only recommendation.

### Phase 4: Review

Check arithmetic, units/signs/denominators, source lineage, owner boundaries, and that no proposal was phrased as an order or approval. Record native session/Program Ledger references only; create no state sidecar.

## Method

1. Normalize price, quantity and notional with exact contract multiplier/decimals; declare signed side, quote currency, time zone, session boundaries and clock source. Keep event time distinct from receipt time.
2. Sort by authoritative sequence when available. Detect duplicate/out-of-order events, crossed/stale books, missing sides, corrections, non-trading periods and source clock offsets. Do not infer a valid book from malformed snapshots.
3. Compute quoted spread as ask minus bid and relative spread against an explicitly named midpoint. Compute side-specific depth only from the requested price band and timestamp. Report sample count, percentile and missing interval; never let an average hide empty or crossed periods.
4. Compare a proposed notional to supplied book levels or verified historical fills. Estimate sweep price by consuming levels in order. Separate book/curve impact from fees, rebates, gas, funding, route cost and latency uncertainty; do not extrapolate a linear impact model beyond observed size.
5. For fills, use a declared arrival benchmark. Signed implementation shortfall per filled unit is `(fill_price - arrival_price) * side_sign`, with `side_sign=+1` for buys and `-1` for sells; multiply by quantity and contract multiplier to produce quote-currency cost. Add fees and rebates using their currency conversion at a stated time. Show unfilled amount separately and do not treat it as zero-cost execution.
6. Compare filled and unfilled quantity to the benchmark at a declared evaluation horizon only if supplied market data supports it. Attribute adverse selection/impact as decompositions, not causal proof; distinguish markout association from trader intent.
7. For MEV, require transaction/block order, pre/post pool state, exact route and swap amounts, public/private ordering evidence, fees/tips and a credible counterfactual. A price move or sandwich-shaped sequence is a hypothesis unless complete transaction evidence identifies the mechanism.
8. Stress alternative clocks, benchmark, sampling cadence, fees, size and order urgency. Recommend a strategy adjustment only when the ranking survives plausible data and model variations; otherwise specify which evidence would resolve it.
9. Return a reproducible advisory report and cite native session/Program Ledger facts; no state writes, adapter edits, provider calls or execution.

## Rules

- Quote, trade, book and fill records with unmatched clocks are not directly comparable until aligned or explicitly bounded.
- Do not equate displayed depth with guaranteed liquidity or a simulated fill with realized execution.
- Report costs in currency and basis points with denominator and sign. Expose unfilled quantity, rebates and negative-cost conventions.
- Do not use reinforcement learning, execution scripts, MEV bots, provider APIs or alternate broker/venue installation. Technical integration belongs to Eric.
- Jane’s increase/trim/exit/target/risk recommendations remain advisory; live/capital changes require Lisa and Carlos independent two-channel approval for the exact version.

## Focused evaluation cases (expected, not executed)

- Buy 10 units at 101 with arrival mid 100, multiplier 1, fees 2 quote units: signed shortfall is +10 and all-in cost +12; a sell uses the opposite sign.
- 8 units ordered, 5 filled, 3 unfilled: report fill cost on 5 and unresolved opportunity/markout on 3; do not report 8 as fully executed.
- Receive timestamps are reversed but exchange sequence is monotonic: use sequence order and flag receive-clock skew, not reorder by local time.
- A block shows back-to-back swaps and a price reversal, but no prestate/route/tip evidence: classify as possible MEV pattern, not confirmed sandwich.

## Source and release status

Exact source evidence and licenses are recorded in `source-material/` and `provenance.json`. The selected AGIPro root is MIT; preserve its license/copyright for any substantial copied text. ML4T Apache-2.0 includes a NOTICE that must be carried if its material is copied. This draft is independently authored and imports no RL policy or MEV execution workflow. Not admitted or qualified; no upstream script or data provider was run.


## Progressive disclosure

Read this skill first. Load `advanced/advanced.md` only for the relevant specialized calculation; use `references/schemas.json` for input/output shapes; consult `references/api-specs.md` before making any integration claim; use `references/source-provenance.json` and `SOURCES.md` for source/license boundaries. `examples/` contains illustrative inputs, bounded worked output and proposed adversarial cases, not live evidence or passing evaluations.

## Tool protocol and persistence

The frontmatter `read_file` and `write_file` tool names are logical capability aliases; map them only to the host’s ordinary `fs_read` and `fs_write` operations when those capabilities are actually supplied. Do not install, assume, or invoke a tool from this declaration. Prefer an available native CLI for local, authorized reads; a CLI wrapper only when its contract is inspected; a direct API only with an approved endpoint and contract; or MCP only when the matching server/tool is already exposed and authorized. These routes do not authorize provider calls or external effects.

The declared `.workdir/tasks/{{task_id}}/state.jsonl` path exists solely as the catalog validator’s resumability alias. Do not create that file. Record task progress and references in the existing LiNKtrading native session and Program Ledger; those native records remain authoritative. A specialist may prepare a bounded evidence slice for a generalist, but task ownership and review remain explicit.

## Contract pointers

Input: `references/schemas.json#/definitions/input`. Output: `references/schemas.json#/definitions/output`. Native task-state reference shape: `references/schemas.json#/definitions/state`. These are draft contracts; state is recorded through native session and Program Ledger references, not a JSONL sidecar.
