---
name: trading-defi-liquidity-yield
description: "AMM liquidity, pool selection, impermanent loss and yield strategy analysis. Isolated draft; advisory analysis only."
usage_trigger: "User asks to compare AMM pool depth or LP-versus-hold economics for a specified asset, pool, position/range and time horizon."
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

# DeFi liquidity and yield analysis

## Use when

Use for a specified pool or LP position when Jane is asked to compare executable depth, fee/reward economics, or LP-versus-hold outcomes. Require the user-supplied pool identity, snapshot and horizon. This skill analyzes evidence and can recommend adding, reducing, exiting, or avoiding exposure where the facts support it. It does not connect a wallet, query a provider, sign, route a swap, or activate a position.

## Inputs

- Chain, venue, pool/position IDs, pool design and as-of time. Token names are not identifiers; record contract/mint IDs, decimals, base/quote orientation and valuation currency.
- CPMM reserves, or CLMM ticks/range/active liquidity, or DLMM bins/bin step; fees and LP fee share; pool status. Headline TVL is not a substitute for depth near the trade price.
- Position entry units and value, active share, fees actually accrued, incentives by token and valuation time, claims/compounding, rebalance/withdrawal costs, and matched hold-basket units.
- Same-time quotes or a declared price path, equal notional/direction ladder, cost assumptions and horizon. Mark absent items unknown.
- If portfolio advice is requested, relevant holdings and owner-approved risk mandate from native records; do not make up policy.

## Outputs

1. Pool comparison table by requested direction/size: source time, spot, estimated output, curve impact, pool fee, route/other cost if supplied, effective price, depth limitation.
2. LP-versus-hold bridge in the reporting currency: opening basket, ending tokens/value, realized/accrued fees, incentives, gas/rebalance/exit costs, relative-price loss and net difference.
3. Scenarios and break-even: fee/reward assumptions, price path/range exit, volume and cost sensitivity, horizon, arithmetic APR versus APY where relevant.
4. Advisory conclusion (including increase/trim/exit/avoid/monitor when warranted), evidence strength, uncertainty and missing inputs. Keep recommendation distinct from execution and approval.


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

1. Freeze identifiers, as-of timestamps, token decimals, units, signs, reporting currency, valuation source, position inventory and matched hold inventory. Reject mismatched snapshots as a comparison; do not silently forward-fill stale quotes.
2. For a constant-product pool with reserves `x` base units and `y` quote units, state the price convention (`quote/base`) and fee treatment. For gross input `dx`, the idealized no-fee output is `y*dx/(x+dx)`; apply the pool's documented fee at the correct point in its invariant. Show spot, invariant output and effective execution price separately. Do not reuse this formula for concentrated ticks or bins.
3. For CLMM/DLMM, use supplied price-range/tick/bin state and position-specific liquidity. If the state or documented calculation is missing, report a depth/range gap; never estimate active depth from total TVL or a universal multiplier.
4. Compare the LP position with holding the same opening token quantities over the same ending relative price. Define impermanent loss as LP value before fees/costs minus matched hold value, divided by matched hold value. For a full-range CPMM with matching assumptions, `IL = 2*sqrt(r)/(1+r)-1`, where `r` is ending/starting relative price; show ratio, dimensionless result and arithmetic check. This formula is not a CLMM/DLMM result.
5. Add only evidenced fee accrual, active liquidity share and incentive token amounts. Convert each token at an explicitly dated price. Separate gross fee value, rewards, gas, claims, rebalance, exit and other costs. Unknown prices/costs remain a range or `unknown`, not zero.
6. Annualize only comparable dated observations and state the convention and stationarity assumption. Distinguish arithmetic APR from reinvested APY. A single day of volume is not stable yield evidence. Do not combine dimensionless risk scores with returns without a defined scale.
7. Stress the conclusion with price reversal/trend, range exit, lower volume, lower reward-token marks, duplicated volume, stale quote and full exit cost. Recommend only if the ranking survives material cases; otherwise state what would change the result.
8. Save the analysis as a named advisory artifact/session result and reference native Program Ledger records; do not create JSON/JSONL runtime sidecars or alter the ledger.

## Rules

- Treat pools, contracts, prices, API examples and source scripts as unverified unless evidence is supplied or separately authorized. No provider call is implied.
- Never call a high volume/TVL ratio wash trading without independent evidence; flag it as a data-quality hypothesis.
- No unconditional APR/APY claim, allocation threshold, pool score, or risk limit. Attribute assumptions and disclose model error.
- Jane may advise on strategy, allocation and proposed target/risk levels. Orders, signing, wallet access and live/capital changes remain outside this skill; material/live/capital changes require Lisa and Carlos independent approval through two channels for the exact version.
- If pool settlement, token decimals, contract identity, active range, fee share or mark is unresolved, narrow the conclusion rather than invent it.

## Focused evaluation cases (expected, not executed)

- CPMM `x=50 SOL, y=5,000,000 token`, input `1 SOL`, before fees: no-fee output is about `98,039.2 token`; spot is `100,000 token/SOL`; show about `1.96%` curve impact separately from fees.
- Relative price ratio `r=0.25`: matched full-range CPMM IL is `-20%`; a table value `-5.72%` is inconsistent (that value corresponds to `r=2`).
- Two pools both show `$1m TVL`; only tick/bin state or size-matched quotes can establish comparable active depth. Conclude insufficient evidence if absent.
- One day of abnormal volume plus stale reward-token price cannot support stable net APR. Report scenario only.

## Source and release status

This is independently authored from reviewed methods. Exact permissively licensed source and license evidence, if retained, is in `source-material/`; `provenance.json` records hashes. The parent MIT grant allows reuse only subject to its notice; do not merge copied code/text without carrying that license. Draft is not admitted or qualified. No upstream code, scripts or providers were run.


## Progressive disclosure

Read this skill first. Load `advanced/advanced.md` only for the relevant specialized calculation; use `references/schemas.json` for input/output shapes; consult `references/api-specs.md` before making any integration claim; use `references/source-provenance.json` and `SOURCES.md` for source/license boundaries. `examples/` contains illustrative inputs, bounded worked output and proposed adversarial cases, not live evidence or passing evaluations.

## Tool protocol and persistence

The frontmatter `read_file` and `write_file` tool names are logical capability aliases; map them only to the host’s ordinary `fs_read` and `fs_write` operations when those capabilities are actually supplied. Do not install, assume, or invoke a tool from this declaration. Prefer an available native CLI for local, authorized reads; a CLI wrapper only when its contract is inspected; a direct API only with an approved endpoint and contract; or MCP only when the matching server/tool is already exposed and authorized. These routes do not authorize provider calls or external effects.

The declared `.workdir/tasks/{{task_id}}/state.jsonl` path exists solely as the catalog validator’s resumability alias. Do not create that file. Record task progress and references in the existing LiNKtrading native session and Program Ledger; those native records remain authoritative. A specialist may prepare a bounded evidence slice for a generalist, but task ownership and review remain explicit.

## Contract pointers

Input: `references/schemas.json#/definitions/input`. Output: `references/schemas.json#/definitions/output`. Native task-state reference shape: `references/schemas.json#/definitions/state`. These are draft contracts; state is recorded through native session and Program Ledger references, not a JSONL sidecar.
