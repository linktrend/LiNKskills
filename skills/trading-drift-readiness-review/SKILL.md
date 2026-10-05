---
name: trading-drift-readiness-review
description: "Deterioration, drawdown response, monitoring and paper/live readiness evidence. Isolated draft; advisory analysis only."
usage_trigger: "Jane is asked whether a strategy deteriorated, why results changed, what risks deserve attention, or what evidence is needed before readiness can be assessed."
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

# Drift and readiness evidence review

## Use when

Use when Jane is asked whether strategy results deteriorated, why a measure changed, what deserves monitoring, or what evidence remains before readiness can be assessed. Jane can recommend strategy, position or risk changes from evidence. This skill does not set limits, configure alerts, trip a kill switch, approve a launch or change paper/live state.

## Inputs

- Native Program Ledger/session export or supplied records: version, strategy/account, instrument, currency, timestamps, P&L, flows, positions, fills/fees and opening equity.
- Predeclared reference/current windows and baseline; point-in-time features/predictions/returns, sample size, missingness, revisions and freshness.
- Approved risk mandate/version only if asking whether a policy breach occurred.
- Readiness evidence pointers and accountable owner for data lineage, stale feed detection, reconciliation, monitoring, incident/recovery, rollback and governance.

## Outputs

- Reconciliation status and like-for-like comparison table, including window boundaries and sample coverage.
- Drift diagnostics separated by input/feature, prediction, outcome/performance, execution and operational/data-quality categories.
- Hypotheses and competing explanations with supporting/disconfirming evidence; no causal conclusion from correlation alone.
- Readiness evidence matrix `verified / partial / missing / not applicable`, artifact pointer, owner and follow-up evidence. No green status inferred from absence of incidents.
- Advisory action candidates and risks, or explicit inability to assess; no control mutation.


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

1. Reconcile ledger/positions/cashflows and verify timestamp, currency and strategy version. If inputs do not tie or are stale, mark downstream performance comparison provisional or blocked.
2. Freeze baseline and current date windows, event-time conventions, cadence, feature versions and eligibility rules before inspecting results. Report sample count, missingness and class coverage for each window.
3. Compare like with like: input distributions, predictions/calibration, realized outcomes, net/gross returns and execution costs separately. Distinguish population/sample changes from value drift and operational data gaps.
4. If computing a distribution statistic such as PSI, document frozen reference bins, current out-of-range/missing rows, bin counts, formula and sensitivity. A heuristic statistic is diagnostic evidence only; no source threshold automatically establishes deterioration or triggers action.
5. Calculate drawdown from opening wealth and a reconciled dated equity path. State peak, external-flow treatment, realized/unrealized scope and currency. Return-to-peak does not erase an earlier drawdown.
6. Build candidate explanations such as regime/volatility shift, feature/label changes, universe composition, stale feed, higher spread/fees, capacity or sample noise. For each list confirming and falsifying evidence; do not claim cause without controlled evidence.
7. For readiness, inspect evidence pointers for data lineage, freshness, reconciliation, risk ownership, alert observability, incident response, recovery and rollback. `missing` means not demonstrated, not necessarily absent in reality. Eric verifies technical controls/contracts; Jane evaluates trading evidence; Lisa and Carlos own the relevant exact-version approvals.
8. Compare observed metrics to a supplied approved risk limit/version only if date/effective scope match. Otherwise report the metric and say policy compliance was not assessed.
9. Deliver advisory findings and proposed questions/strategy changes; do not configure a control, move paper/live state, enable trading or mutate policy.

## Rules

- No universal drawdown, PSI, sample-size, Sharpe or readiness threshold.
- Missing/empty state is unknown, not healthy. Backtest/paper evidence alone does not establish operational readiness.
- Jane may recommend sizing, targets, trims/exits or further validation where supported. Order execution, launch/readiness approval, adapter/alert configuration and risk-control implementation remain outside scope.
- Material/live/capital changes require Lisa and Carlos independent two-channel approval for exact version.
- Use native sessions/Program Ledger; no JSONL sidecar, source memory store or control state write.

## Focused evaluation cases (expected, not executed)

- NAV path 100→90→100: total return 0%, max drawdown 10%; initial wealth is the opening peak.
- PSI 0.24 with 30% current observations outside frozen reference bins: disclose out-of-range count and sensitivity; no automatic halt.
- Gross performance flat while net declines after fees double: costs are a plausible contributor; causation requires aligned, reconciled series.
- Breaker state empty and P&L partial: risk policy/readiness unknown, not green.
- Positive backtest and paper returns with no rollback owner/evidence: readiness remains incomplete.

## Source and release status

Exact ML4T source, Apache-2.0 LICENSE and NOTICE are preserved in `source-material/` and hashed in `provenance.json`. NOTICE identifies the companion resource and states that Apache-2.0 does not grant trademark rights. Other reference licenses remain separate; no GPL text/code copied. Draft only; current internal alert/control contract has not been verified.


## Progressive disclosure

Read this skill first. Load `advanced/advanced.md` only for the relevant specialized calculation; use `references/schemas.json` for input/output shapes; consult `references/api-specs.md` before making any integration claim; use `references/source-provenance.json` and `SOURCES.md` for source/license boundaries. `examples/` contains illustrative inputs, bounded worked output and proposed adversarial cases, not live evidence or passing evaluations.

## Tool protocol and persistence

The frontmatter `read_file` and `write_file` tool names are logical capability aliases; map them only to the host’s ordinary `fs_read` and `fs_write` operations when those capabilities are actually supplied. Do not install, assume, or invoke a tool from this declaration. Prefer an available native CLI for local, authorized reads; a CLI wrapper only when its contract is inspected; a direct API only with an approved endpoint and contract; or MCP only when the matching server/tool is already exposed and authorized. These routes do not authorize provider calls or external effects.

The declared `.workdir/tasks/{{task_id}}/state.jsonl` path exists solely as the catalog validator’s resumability alias. Do not create that file. Record task progress and references in the existing LiNKtrading native session and Program Ledger; those native records remain authoritative. A specialist may prepare a bounded evidence slice for a generalist, but task ownership and review remain explicit.

## Contract pointers

Input: `references/schemas.json#/definitions/input`. Output: `references/schemas.json#/definitions/output`. Native task-state reference shape: `references/schemas.json#/definitions/state`. These are draft contracts; state is recorded through native session and Program Ledger references, not a JSONL sidecar.
