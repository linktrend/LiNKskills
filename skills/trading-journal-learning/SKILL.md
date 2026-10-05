---
name: trading-journal-learning
description: "Trade journal, bounded lessons and setup-learning methods. Isolated draft; advisory analysis only."
usage_trigger: "Jane is asked to review closed or maturing trades, compare planned execution/results, study a named setup cohort, or prepare a postmortem."
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

# Trade journal and bounded learning

## Use when

Use when Jane is asked to review closed/maturing trades, compare original intent with fills/exits, study a named setup cohort, or prepare a postmortem. Jane may recommend strategy/position/risk changes from evidence. This is an analysis of existing records, not a journal write, automated memory update or order workflow.

## Inputs

- Native Program Ledger/session or supplied fill/journal export with stable IDs, partial legs, side, units, currency, timestamps/timezone, fees, funding/borrow, provenance and source version.
- Original contemporaneous thesis, signal, intended horizon, sizing/risk, stop/target and benchmark. Preserve later edits as later facts.
- Cohort setup definition, point-in-time universe including rejected/failed candidates, event timestamp, requested horizon, price/quote path, benchmark and cost model.
- Human reflection only if provided; do not infer emotion, motive, discipline or diagnosis.

## Outputs

- Plan-versus-fill/exit table with gross/net bridge, intended versus realized risk, slippage/fees and unresolved rows.
- Cohort report for each horizon: eligible, mature and pending counts; direction-adjusted returns; MFE/MAE; benchmark; stop path; costs; limitations.
- Evidence-ranked lessons with counterexamples and selection/censoring caveats; process adherence is separated from outcome luck.
- Advisory recommendations when supported; exact uncertainty and evidence needed to reverse them.


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

1. Define trade/cohort/period, as-of date, time zone, inclusion criteria and maturity horizons. Keep rejected candidates, failed trades and immature outcomes visible where records allow.
2. Reconcile fills with stable IDs and signed partial legs. Allocate costs by supplied method and currency. Calculate gross and net only after fees/funding/borrow and dated FX; list unreconciled residuals.
3. Retrieve only contemporaneous plan facts. Compare actual path to original thesis, trigger, intended size, risk, stop/target and exit rules. Missing plan fields stay missing; never reconstruct them from a winning/losing outcome.
4. For a cohort, freeze event time and session calendar. Calculate direction-adjusted return from a declared reference, MFE/MAE over explicit horizons and a stop/gap convention; include benchmark and costs. Do not compare unlike setups or calendars.
5. For each horizon, classify records as eligible, mature or pending. Report counts and outcome distributions separately; overlapping trades/windows, missing bars and small samples constrain inference.
6. Show realized cash by event date separately from closed-trade cohort cumulative P&L. A trim of 20 in the prior period and close of 30 now means current realized cash 30 and cohort cumulative 50, never 70 current cash.
7. Use all closed trades including breakevens for all-closed win rate; optionally provide a separate non-flat/decided denominator. Profit factor is undefined when no losses exist. Singleton sample standard deviation is undefined. Mean currency P&L does not prove edge.
8. If reporting R, calculate against immutable initial side-aware risk: for a long, initial risk per unit is `entry - original stop`; for a short it is `original stop - entry`, times quantity and contract multiplier where applicable. Preserve the original stop/risk after later trailing or stop changes. If initial stop/risk was absent or nonpositive, report R as undefined rather than substitute a trailed stop.
9. Preserve raw MAE/MFE; do not “improve” results with later adjusted stops. Define exact calendar boundaries for monthly/weekly cohorts, not “four weeks” or average weekly rates.
10. Separate adherence evidence from outcome. A time gap, language or profit/loss does not establish motive or causal learning. Any behavioral note must quote or refer to supplied contemporaneous reflection and remain a hypothesis.
11. State evidence-supported lessons, counterexamples, alternatives, selection/censoring risk and recommendations. Reference the native Program Ledger/session; do not create a parallel journal, memory JSONL, index, or strategy mutation.

## Rules

- Keep pending trades pending until the declared horizon matures. A favorable intraday excursion is not a completed horizon outcome.
- No fabricated psychology, causal attribution, general win probability, or source-derived automatic cutoff.
- Use explicit units/signs, fee convention, timestamps, denominator and sample size for every measure.
- Jane may recommend increase/trim/exit, target or risk proposals when evidence and mandate allow; execution, signing, live activation and capital changes are not permitted here. Material/live/capital changes require Lisa and Carlos independent two-channel approval for the exact version.
- Native state is the source of record. No JSONL runtime sidecar or imported source memory lifecycle.

## Focused evaluation cases (expected, not executed)

- Long 10 at 10, exit 4 at 12 and 6 at 9, fee 1: gross +2, net +1; report weighted partial legs and fee currency.
- Requested three-session outcome has only two sessions observed, despite +9% intraday MFE: classify as pending.
- Cohort excludes rejected candidates and failures: selection bias prevents general setup-performance claim.
- Entry occurs eight minutes after a losing exit: chronology only; motive is unproven.
- Two source files have identical hashes and cutoff rules: one method contribution; cutoffs remain uncalibrated.
- Long entry 100 with original stop 95 risks 5/unit; later stop moves to 98 and trade gains 10: report 2R against original risk, not 5R from the trailing stop. Missing original stop means R undefined.

## Source and release status

Exact AGIPro source and its MIT license/copyright are retained in `source-material/` with source, license and notice hashes in `provenance.json`. Other repository license records are separate. This draft contains no upstream code, source memory schema, JSONL lifecycle or copied scripts. Not admitted or qualified.


## Progressive disclosure

Read this skill first. Load `advanced/advanced.md` only for the relevant specialized calculation; use `references/schemas.json` for input/output shapes; consult `references/api-specs.md` before making any integration claim; use `references/source-provenance.json` and `SOURCES.md` for source/license boundaries. `examples/` contains illustrative inputs, bounded worked output and proposed adversarial cases, not live evidence or passing evaluations.

## Tool protocol and persistence

The frontmatter `read_file` and `write_file` tool names are logical capability aliases; map them only to the host’s ordinary `fs_read` and `fs_write` operations when those capabilities are actually supplied. Do not install, assume, or invoke a tool from this declaration. Prefer an available native CLI for local, authorized reads; a CLI wrapper only when its contract is inspected; a direct API only with an approved endpoint and contract; or MCP only when the matching server/tool is already exposed and authorized. These routes do not authorize provider calls or external effects.

The declared `.workdir/tasks/{{task_id}}/state.jsonl` path exists solely as the catalog validator’s resumability alias. Do not create that file. Record task progress and references in the existing LiNKtrading native session and Program Ledger; those native records remain authoritative. A specialist may prepare a bounded evidence slice for a generalist, but task ownership and review remain explicit.

## Contract pointers

Input: `references/schemas.json#/definitions/input`. Output: `references/schemas.json#/definitions/output`. Native task-state reference shape: `references/schemas.json#/definitions/state`. These are draft contracts; state is recorded through native session and Program Ledger references, not a JSONL sidecar.
