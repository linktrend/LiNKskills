---
name: trading-prediction-market-strategy
description: "Prediction-market probability, fees, settlement and arbitrage; weather and crypto/index modes. Isolated draft; advisory analysis only."
usage_trigger: "User asks whether an identified prediction-market contract is mispriced, what probability its outcome implies, or whether its outcomes provide a valid relative-value opportunity."
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

# Prediction-market strategy analysis

## Use when

Use when Jane is asked whether an identified event contract is mispriced, how its payoff maps to event probability, or whether two supplied contracts provide relative value. Outputs may recommend enter/increase/trim/exit/avoid/no action when evidence supports an advisory view. This skill never places an order, connects an account, handles credentials, or claims an executable arb without fully specified settlement and capital paths.

## Inputs

- Venue, exact series/market/contract ID, current rulebook text/version, source and retrieval time.
- Outcome definitions, inclusivity, tie/void/cancellation rules, timezone, observation interval, settlement index/station/source, rounding, expiry and redemption/collateral terms.
- Timestamped bid/ask and size/depth, tick, fee schedule and fee side, settlement status, liquidity/market state and currency conversion.
- Probability evidence with observation time, units, horizon, source, calibration sample and uncertainty. Weather requires station, local-day window and forecast initialization; crypto/index requires constituent/index and print/averaging convention.
- For backtests: point-in-time quotes, matured outcomes, fee/fill/market-status history, candidate universe and benchmark.

## Outputs

- Contract interpretation and unresolved-term checklist; mutually exclusive payout-state table.
- Probability interval/distribution with dated evidence; separate displayed price, midpoint and executable ask/bid.
- Per-contract payoff and expected-value table after stated fees/costs, break-even probability, depth and collateral lock; sensitivity to probability and settlement ambiguity.
- Relative-value/arbitrage classification, failure conditions, recommendation where warranted, and exact evidence that would reverse it.


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

## Integrated method

1. Freeze the exact contract and rule text. Map every possible state to payout, including ties, voids, cancellations, rounding and settlement-source failures. If a material clause is missing or ambiguous, stop numeric edge claims and issue a rulebook gap card.
2. Check that outcomes are mutually exclusive and exhaustive. Record event interval/timezone, observation source, expiration and redemption mechanics. Do not substitute spot price or a generic weather/crypto convention for the specified settlement method.
3. Normalize bid/ask, contract count, payout/collateral, fees and currency. For a binary long contract with payout `1` on win, per-contract gross expected value is `p*1 - ask`; net expected value subtracts the actual fee and other evidenced costs. State units and fee schedule. For short/other payout shapes, derive from the full state table rather than reuse the binary shortcut.
4. Determine event probability only from evidence available by the stated as-of time. Show model/reference, horizon, calibration and uncertainty. Weather distributions must correspond to the contract station/window/brackets; crypto/index distributions must correspond to its exact index and averaging rule. No hardcoded offsets or invented precision.
5. Compare the probability range with the fee-adjusted break-even price. If uncertainty overlaps break-even, call the edge indeterminate. If input calibration is weak, give scenario analysis rather than a point estimate.
6. Call an arbitrage only if every settlement state, leg, fee, spread, depth, timing, collateral lock/release, conversion, venue/counterparty and operational failure state is covered and jointly feasible. Otherwise describe it as a relative-value hypothesis, not arbitrage.
7. For historical evaluation, require point-in-time quotes, matured outcomes, contemporaneous fees, realistic fill assumptions and the complete selection universe. Mark unresolved or unfilled contracts; avoid lookahead, survivorship and selection bias.
8. Deliver conclusion, supporting rows, sensitivities, uncertainties and recommendation. Keep the advice non-executing; use the existing LiNKtrading system only and native Program Ledger/session references where relevant.

## Rules

- Missing exact settlement authority, bracket inclusivity, timezone or rounding means contract interpretation unresolved, regardless of a plausible market consensus.
- Midpoint is not an executable price. No edge without actual direction-specific price, size, fee and cost basis.
- Do not apply Kelly or another sizing formula absent a validated probability distribution and approved risk mandate. Report candidate risk size only as a clearly labeled scenario if inputs support it.
- Do not infer arbitrage from a basket of related contracts with uncovered state, timing, collateral, redemption or venue failure paths.
- Quarantine venue APIs, account operations, order placement, geofencing and live-ops instructions. Eric owns technical integration; Sara owns legal/tax questions.
- Jane can recommend a strategy or position change; no orders, account mutations, policy changes, activation or signing. Material/live/capital changes require Lisa and Carlos independent two-channel approval for the exact version.

## Focused evaluation cases (expected, not executed)

- Weather contract says “daily max at least 30 C” but station timezone and rounding are missing. Do not produce an authoritative probability; issue rulebook gap.
- “Index above 100 at 16:00” actually references a 5-minute mean, but no index rule or interval is supplied. Do not substitute a spot print.
- Model probability `0.54 ± 0.08`, ask `0.50`, fee-adjusted break-even `0.53`: uncertainty spans break-even, so edge is not robust.
- Two contracts appear to cover all outcomes but have different settlement times and locked collateral; no arbitrage claim absent complete joint paths.

## Source and release status

This draft independently expresses contract/payoff analysis. `source-material/` contains exact licensed source evidence and a hash manifest where retained. AGIPro's MIT license and copyright must accompany any copied substantial material; no provider/API/live workflow is imported. The crypto/index source map has an unresolved missing generic bracket reference; exact supplied contract rules remain mandatory. Not admitted or qualified; no source code, APIs or trading operation executed.


## Progressive disclosure

Read this skill first. Load `advanced/advanced.md` only for the relevant specialized calculation; use `references/schemas.json` for input/output shapes; consult `references/api-specs.md` before making any integration claim; use `references/source-provenance.json` and `SOURCES.md` for source/license boundaries. `examples/` contains illustrative inputs, bounded worked output and proposed adversarial cases, not live evidence or passing evaluations.

## Tool protocol and persistence

The frontmatter `read_file` and `write_file` tool names are logical capability aliases; map them only to the host’s ordinary `fs_read` and `fs_write` operations when those capabilities are actually supplied. Do not install, assume, or invoke a tool from this declaration. Prefer an available native CLI for local, authorized reads; a CLI wrapper only when its contract is inspected; a direct API only with an approved endpoint and contract; or MCP only when the matching server/tool is already exposed and authorized. These routes do not authorize provider calls or external effects.

The declared `.workdir/tasks/{{task_id}}/state.jsonl` path exists solely as the catalog validator’s resumability alias. Do not create that file. Record task progress and references in the existing LiNKtrading native session and Program Ledger; those native records remain authoritative. A specialist may prepare a bounded evidence slice for a generalist, but task ownership and review remain explicit.

## Contract pointers

Input: `references/schemas.json#/definitions/input`. Output: `references/schemas.json#/definitions/output`. Native task-state reference shape: `references/schemas.json#/definitions/state`. These are draft contracts; state is recorded through native session and Program Ledger references, not a JSONL sidecar.
