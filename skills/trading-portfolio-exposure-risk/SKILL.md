---
name: trading-portfolio-exposure-risk
description: "Portfolio exposure, correlation, allocation, risk metrics and risk constraints. Isolated draft; advisory analysis only."
usage_trigger: "User asks to quantify portfolio exposures, concentration, dependence, drawdown/stress risk or an advisory hypothetical target/rebalance from supplied portfolio evidence."
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

# Portfolio exposure and risk

## Use when

Use when Jane is asked to quantify exposures, concentration, dependence, drawdown/stress risk, or to recommend a hypothetical target/rebalance from supplied portfolio evidence. Recommendations may include increase, trim, exit or target/risk proposals when data and mandate support them. No order, position mutation, policy change or live activation.

## Inputs

- Dated holdings/cash/liabilities/margin, signed units, identifiers, currencies, prices, valuation time and equity/NAV denominator.
- Derivatives: contract, multiplier, expiry, settlement, and supported Greeks/scenarios; do not treat notional as delta exposure without the conversion.
- Issuer/sector/theme/look-through mappings with source and confidence; unknown mappings remain in an “unclassified” bucket.
- Returns series with frequency, timestamps, corporate-action/roll convention, currency conversion and benchmark/factor series.
- Owner-approved targets/limits and version if judging a breach. Otherwise report measurements and hypothetical scenarios, not compliance.
- Scenario shocks, horizon, liquidity/cost assumptions, correlation/factor estimation window and sample size.

## Outputs

- Reconciled exposure table by asset, currency, issuer, sector/theme, liquidity class and risk factor with denominator and unknown coverage.
- Concentration/dependence table and risk metrics with data window, sample size, annualization and missingness.
- Scenario loss/range table separating price shocks, FX, rate, volatility, liquidity and margin assumptions.
- Advisory allocation alternatives with proposed target weights/levels only when inputs support them; current exposure, delta, risk/cost, uncertainty and rationale.
- Exact policy comparison only when approved mandate and version supplied; otherwise explicit `not assessed`.


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

1. Freeze the position and equity snapshot. Reconcile signed quantities, market values, cash flows, liabilities and cash to the supplied NAV; quantify unmatched and stale items before metrics. Preserve currencies and convert only with dated FX evidence.
2. Define exposure numerator and denominator. For cash equities use signed market value/NAV. For a future or option, show gross notional and supported delta-equivalent separately; do not synthesize Greeks or assume contract multipliers.
3. Compute concentration by direct position and any supplied look-through mapping. Show top names and residual/unclassified allocation; do not count a missing issuer mapping as diversified.
4. Estimate correlation only from aligned return rows on a stated frequency/window with pairwise sample counts. State that correlation is historical dependence, not causation or a stable forecast. Provide sensitivity to window and outliers when sample permits.
5. Calculate drawdown from a dated total-return equity path including opening wealth, dividends/costs and external flows treated consistently. State peak basis and flow treatment. Do not calculate from percentages alone if opening NAV/flows are absent.
6. Build scenario P&L with explicit shock units/signs and valuation rules. For linear exposure, `scenario_P&L = signed_units * price_change * multiplier` in quote currency before FX/cost; only use nonlinear option repricing if terms/Greeks/model inputs are supplied and limitations stated.
7. Compare actuals with owner-approved limits/version only if both are supplied and effective for the measurement date. Otherwise report observed exposure and “policy status not assessed.”
8. Present at least a current-hold baseline and user-relevant alternatives. Show hypothetical before/after exposure, expected scenario losses, liquidity/cost and tradeoff. Do not output an executable order ticket or unconditional threshold.
9. Deliver advisory recommendation plus rejected alternatives, data confidence, reversals and missing evidence. Reference native state without writing it.

## Rules

- Currency, denominator, signed side, multiplier and valuation as-of are mandatory metric metadata.
- Missing instruments, short positions, liabilities, stale prices or incomplete cash flows can materially understate risk. Show coverage and bound uncertainty.
- Correlation and factor betas require matched dated observations and sufficient sample; no fabricated confidence interval.
- Risk limits are owner policy, not source defaults. Never invent breach states, automatic trims or circuit-breaker thresholds.
- Sara owns tax interpretation; Eric owns data adapters and risk-control implementation. Jane may give strategy advice but cannot execute it.

## Focused evaluation cases (expected, not executed)

- NAV $100, position $60 and cash $40: weight is 60% only if both use the same valuation timestamp/currency and reconcile to NAV.
- Long 2 contracts with multiplier 100 and price shock -3: linear scenario P&L is -600 quote currency before FX/cost; do not call notional delta.
- Equity 100→90→100: return ends flat but max drawdown is 10% from initial wealth; opening wealth is included.
- Holdings total only 82% of NAV and 18% lacks issuer mapping: state 18% unclassified; no full-portfolio concentration conclusion.

## Source and release status

This is independently authored; selected source, Apache-2.0 license and NOTICE are captured under `source-material/` with SHA-256 records. GPL-licensed source entrypoints were reviewed as private audit evidence only and were not copied. Draft is not admitted/qualified; risk model, data and current policy remain task-specific inputs.


## Progressive disclosure

Read this skill first. Load `advanced/advanced.md` only for the relevant specialized calculation; use `references/schemas.json` for input/output shapes; consult `references/api-specs.md` before making any integration claim; use `references/source-provenance.json` and `SOURCES.md` for source/license boundaries. `examples/` contains illustrative inputs, bounded worked output and proposed adversarial cases, not live evidence or passing evaluations.

## Tool protocol and persistence

The frontmatter `read_file` and `write_file` tool names are logical capability aliases; map them only to the host’s ordinary `fs_read` and `fs_write` operations when those capabilities are actually supplied. Do not install, assume, or invoke a tool from this declaration. Prefer an available native CLI for local, authorized reads; a CLI wrapper only when its contract is inspected; a direct API only with an approved endpoint and contract; or MCP only when the matching server/tool is already exposed and authorized. These routes do not authorize provider calls or external effects.

The declared `.workdir/tasks/{{task_id}}/state.jsonl` path exists solely as the catalog validator’s resumability alias. Do not create that file. Record task progress and references in the existing LiNKtrading native session and Program Ledger; those native records remain authoritative. A specialist may prepare a bounded evidence slice for a generalist, but task ownership and review remain explicit.

## Contract pointers

Input: `references/schemas.json#/definitions/input`. Output: `references/schemas.json#/definitions/output`. Native task-state reference shape: `references/schemas.json#/definitions/state`. These are draft contracts; state is recorded through native session and Program Ledger references, not a JSONL sidecar.
