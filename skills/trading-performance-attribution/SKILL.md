---
name: trading-performance-attribution
description: "Net performance, attribution, postmortems, residual edge and coaching. Isolated draft; advisory analysis only."
usage_trigger: "User asks to reconcile and explain realized/backtest performance, strategy/benchmark attribution, signal-cohort outcomes or a closed-trade postmortem."
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

# Performance attribution and postmortem

## Use when

Use for a fixed-period net performance explanation, benchmark/strategy attribution, a matured signal cohort, or a closed-trade postmortem. Jane may recommend strategy or position changes when evidence supports them; this method does not alter the ledger or strategy settings.

## Inputs

- Native ledger/export identity and version; opening NAV, dated deposits/withdrawals, holdings/fills, fees, financing, dividends and valuations.
- Period boundaries/timezone, reporting currency, risk-free series and benchmark/factor series with matching calendars.
- For signal cohorts: point-in-time universe (including rejected candidates if available), signal time/direction, declared horizon, gross/net return, costs and predeclared regime tags.
- Corporate actions, futures roll, stale marks, reconciliation tolerance if governed, and any owner-approved mandate version.

## Outputs

- Reconciliation bridge: opening equity + flows + realized/unrealized P&L + income - costs = ending equity; residual breaks listed.
- Dated realized cash versus closed-cohort cumulative P&L report; partial exits remain attached to original cohort and never double-count capital.
- Net/gross, benchmark and factor attribution table with exact sample/calendar/annualization and unresolved contribution.
- Closed-trade/cohort postmortem and evidence-ranked recommendations with counterexamples, uncertainty and no causal claim beyond evidence.


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

1. Fix the period in calendar dates/timezone and identify the ledger version. Reconcile beginning equity, external flows, marked positions, fills, fees/financing/dividends and ending equity before attribution. Keep a residual and stop strong conclusions if it exceeds only a supplied governed tolerance.
2. Separate return measurement from cash flows. State whether using time-weighted return, money-weighted return or simple P&L/NAV and why. Define cash-flow timing and avoid comparing mismatched denominators.
3. Report realized cash by event date separately from closed-trade/cohort cumulative P&L. A trade trimmed 20 earlier and closed 30 now has cohort cumulative P&L 50 while current-period realized cash is 30; never present 70 as current cash. Preserve stable trade IDs across partial closes.
4. Calculate gross and net P&L from signed units and actual fills. Show fees, borrow/funding, dividends and currency conversion separately. Preserve realized and unrealized amounts; never infer missing cost as zero.
5. Calculate benchmark excess only on aligned periods and same currency/calendar. Attribute asset/sector/factor effects only with supplied mapping and a stated model; unexplained residual remains residual. Association is not causal proof.
6. For trade cohorts, freeze event time, inclusion universe, direction, maturity horizon, stop/gap convention and cost assumptions. Separate eligible, mature and pending observations; show failed/rejected candidates when evidence exists.
7. Report win rate over all closed trades including breakeven in the all-closed denominator, plus a separate decided/non-flat denominator if helpful. Profit factor is undefined when there are no losses; do not label it infinite. Singleton sample standard deviation is undefined. Mean currency P&L alone does not establish edge.
8. Annualize only with exact dated calendar boundaries, declared trading/annualization convention and sufficient history. CAGR is based on compounded start/end wealth and elapsed time; an arithmetic mean is not CAGR. Avoid substituting four weeks for a month or average weekly rates for calendar-period returns.
9. State risk-free input, drawdown basis, starting wealth, external-flow handling and empirical-tail sample. Expose missing downside data and sensitivity; do not claim precise tail confidence from a short sample.
10. Give the net attribution, counterexamples and proposed strategy/position/risk changes if warranted. Reference native Program Ledger/session artifacts; do not write JSONL or mutate source state.

## Rules

- If reconciliation fails, label attribution provisional and identify specific break sources.
- Do not count cash flows as investment return or count partial close P&L twice.
- Never infer intent, skill, edge, causal factor or regime change from mean P&L or a short sample alone.
- Jane’s recommendations are advisory. No order, signing, capital move, live activation, mandate mutation or unauthorized threshold. Material/live/capital changes require Lisa and Carlos independent approval in two channels for exact version.
- Sara owns tax/accounting treatment. Use only supplied approved conventions; label accounting/tax treatment unresolved otherwise.

## Focused evaluation cases (expected, not executed)

- Trim cohort P&L 20 in prior period, close final 30 now: current realized cash 30; cohort cumulative 50; never current period 70.
- Closed outcomes `+5, 0, -5`: all-closed win rate 1/3; decided-only 1/2; PF 1.0 if net conventions match.
- Three winners and no losses: profit factor undefined, not infinite.
- One observation: sample standard deviation undefined; mean currency result is descriptive, not proof of edge.
- No opening wealth/flows and an annual arithmetic mean return: do not report CAGR or a flow-adjusted total return.

## Source and release status

The draft is independently authored. Exact selected source and its MIT license/copyright are retained under `source-material/`; provenance records commit and file/license hashes. Other licenses remain separate and no GPL source is copied. Not admitted or qualified; input reconciliation and method validation remain outstanding.


## Progressive disclosure

Read this skill first. Load `advanced/advanced.md` only for the relevant specialized calculation; use `references/schemas.json` for input/output shapes; consult `references/api-specs.md` before making any integration claim; use `references/source-provenance.json` and `SOURCES.md` for source/license boundaries. `examples/` contains illustrative inputs, bounded worked output and proposed adversarial cases, not live evidence or passing evaluations.

## Tool protocol and persistence

The frontmatter `read_file` and `write_file` tool names are logical capability aliases; map them only to the host’s ordinary `fs_read` and `fs_write` operations when those capabilities are actually supplied. Do not install, assume, or invoke a tool from this declaration. Prefer an available native CLI for local, authorized reads; a CLI wrapper only when its contract is inspected; a direct API only with an approved endpoint and contract; or MCP only when the matching server/tool is already exposed and authorized. These routes do not authorize provider calls or external effects.

The declared `.workdir/tasks/{{task_id}}/state.jsonl` path exists solely as the catalog validator’s resumability alias. Do not create that file. Record task progress and references in the existing LiNKtrading native session and Program Ledger; those native records remain authoritative. A specialist may prepare a bounded evidence slice for a generalist, but task ownership and review remain explicit.

## Contract pointers

Input: `references/schemas.json#/definitions/input`. Output: `references/schemas.json#/definitions/output`. Native task-state reference shape: `references/schemas.json#/definitions/state`. These are draft contracts; state is recorded through native session and Program Ledger references, not a JSONL sidecar.
