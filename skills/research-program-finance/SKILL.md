---
name: research-program-finance
description: "Prepares R&D program budget, cash timing, and funding evidence for finance-owner review."
usage_trigger: "Use when a research or R&D owner asks Jane to organize a period-based budget, actual-versus-plan, restricted-funding, or milestone cash evidence packet for an active program."
version: 0.1.1
release_tag: v0.1.1
created: 2026-10-05
author: LiNKskills Library (draft)
tags: [research, program-finance, budget, evidence, draft]
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
scope_out: ["Jane coordinates evidence only; Sara and the named controller/accounting owner decide accounting treatment, classification, rate interpretation, and compliance.", "Do not write to bookkeeping, accounting, award, bank, or program ledgers. Use only the approved native Program Ledger/session for coordination state.", "Do not apply legal, accounting, GAAP, IFRS, Uniform Guidance, sponsor, or tax rules as conclusions without current authoritative owner-provided sources.", "Do not assume a default F&A rate, fixed runway threshold, capitalization treatment, or probability-of-success model.", "Do not create runtime JSON/JSONL state sidecars or add finance APIs, subscriptions, or paid tools.", "Do not claim evaluation, certification, admission, release, or publication from this draft."]
format_profile: simple
last_updated: 2026-10-05
---

# research-program-finance

## Purpose and boundary

Prepare a reviewable evidence packet for the budget, actual spend, funding restrictions, and cash timing of an R&D program already underway. This is an evidence coordination method. Jane does not operate the accounting system or decide treatment, eligibility, compliance, capitalization, indirect cost rules, or whether a program should continue. Sara and the named finance/controller owner make finance and accounting determinations.

This skill does not discover grant opportunities; use `research-grant-opportunities` for prospective funder discovery. It does not replace the existing general finance/accounting operations skill, whose current Odoo snapshot workflow has a different task boundary.

## Required inputs

- Program identifier, work packages, period boundaries, currency, and whether the request covers actuals, forecast, or both.
- Authorized source files or read access to actual ledger summaries, budget/forecast, commitments/encumbrances, and cash schedules.
- Funding-source restrictions and release/receipt timing, with the current award/agreement or named owner confirmation.
- F&A/indirect rate, base, exclusions, fringe loading, and effective dates only when a cited current agreement or policy provides them.
- Milestones, expected dates, cash need by period, and source/owner for each estimate.
- Named controller/finance owner (normally Sara for accounting questions) and requested review date.

If actuals, rate authority, restriction language, or dates are missing, do not fill them from a generic benchmark. Produce a gap-marked evidence packet or request the material input.

## Deliverables

- Period-by-period budget and actual-versus-plan table, separately labeling actual, committed, forecast, and proposed values.
- Direct-cost and indirect-cost view showing the cited rate, base, exclusions, effective period, and unresolved owner interpretation; no independent classification judgment.
- Burn and cash timing scenarios based only on supplied or verified period data, with assumptions shown and no unsupported single runway claim.
- Milestone-versus-cash schedule showing which period and funding pool each expected cash need draws on, with restrictions and timing clearly marked.
- Reconciliation exceptions, source ledger, assumptions, questions, and finance-owner review queue.

## Practical method

1. Set the program boundary, reporting periods, currency, source-as-of dates, and decision the packet supports. Distinguish awarded/committed funds from proposed or unawarded funds.
2. Inventory only authorized source artifacts. Record document/version/date, owner, period, currency, data grain, and whether values are actuals, commitments, budget, or forecast. Do not expose account credentials or unnecessary personal data.
3. Reconcile work-package budget to read-only actuals and commitments by period and currency. Preserve source totals; show any mapping, timing, or arithmetic discrepancy as an exception rather than silently forcing agreement.
4. Represent restrictions and cash availability separately: restricted award balance, unrestricted cash, approved commitments, expected receipts, and timing. A nominal funding amount is not automatically available for every work package or period.
5. Calculate the indirect-cost base only from the cited award, negotiated rate agreement, sponsor policy, or named controller instruction applicable to the specific award and dates. Show the base, each included/excluded category, source, and formula. If the exact applicable base or exclusion is unclear, mark unresolved and route it to Sara/controller; do not import threshold values from an example.
6. Keep direct-cost, fringe, and F&A layers visible so a reviewer can spot double counting or an unsupported rate/base. Apply a formula only when all inputs and the controlling agreement are supplied; label computed values as arithmetic derived from those inputs, not as accounting treatment.
7. Derive historical burn from actual cash/spend by stated periods only when the underlying actual series is complete enough for that period. Keep actual burn separate from forecast burn. Do not substitute lifetime or trailing averages as fact when no actual history is provided.
8. Map milestones to period-specific expected cash need, expected receipts, restrictions, and committed outflows. Show timing shortfalls and scenarios; do not impose a generic minimum-runway threshold or state that a milestone will be achieved.
9. Run sensitivity cases only for explicit alternative assumptions (for example, receipt timing or spend ramp). Show inputs and arithmetic so the named finance owner can reproduce them. Do not add probability-of-success weights, NPV, runway conclusions, or unsupported ROI claims.
10. List accounting, allowability, cost classification, capitalization, rate, and funder-rule questions verbatim with the precise supporting document/page or missing document; assign each to Sara/controller or the responsible owner. Do not resolve these questions.
11. Check source traceability, date and period alignment, currency, totals, actual/forecast separation, restrictions, formula inputs, and review queue. Return the packet as a draft and state what has not been verified or approved.

## Evidence and owner handoff

Use current award-specific and owner-provided records first. General public guidance can identify a question to ask, but it does not establish a program’s applicable accounting treatment or funder permission. Laws, policies, rates, dollar thresholds, and accounting frameworks are time- and jurisdiction-sensitive; verify current authoritative documents through the responsible owner before applying them. If that evidence is not available, leave the conclusion blank and show the gap.

This is not bookkeeping, a journal-entry proposal, an award modification, payment instruction, financing recommendation, or authorization to contact a funder. Jane coordinates the packet. Sara/controller approves finance/accounting choices. Eric owns technical interpretations of R&D milestones when needed.

## Native tool protocol

1. **Native CLI**: use an already available command-line tool only for an authorized local source and a read-only inspection or requested draft output.
2. **CLI wrapper**: use only an existing trusted wrapper when it is necessary; do not adopt the source project’s budget scripts.
3. Use currently supplied native file and search capabilities; no new integrations, accounts, subscriptions, or network access are dependencies.
4. Direct APIs and MCP are not dependencies. Never write to accounting, ledger, award, or bank systems.
5. Use supplied inline schemas as discovery. Call `get_tool_details` only if the host exposes it and additional schema detail is needed; otherwise record a real missing capability as a gap.

## Native session and Program Ledger

Keep working context in the calling native session. When a permitted Program Ledger integration is actually supplied and authorized, append only a concise coordination record and owner-review status. No successful write is assumed. Do not create `.workdir/tasks`, `state.jsonl`, or other JSON/JSONL runtime sidecars.

## Completion check

- Each amount has a period, currency, classification as actual/committed/budget/forecast, and source pointer or explicit gap.
- Restrictions, rate, base, exclusions, and effective dates are traceable to a current award-specific source or marked unresolved.
- Calculations are reproducible from supplied values; actuals remain separate from forecasts and scenarios.
- Milestone cash timing is visible without implying milestone success or making financing/accounting decisions.
- Finance-owner questions and review state are explicit; no external action or ledger write is claimed.

## Contracts

- Input: `references/schemas.json#/definitions/input`
- Output: `references/schemas.json#/definitions/output`
- Expected behavior only: `references/eval-suite.json`; no run or PASS is claimed.

## Progressive references

- Task-specific details: `advanced/advanced.md`
- Illustrative fixture: `examples/adversarial-case.md`
- Source provenance and notice: `references/source-provenance.md`
- Known-bad patterns: `references/old-patterns.md`


## Schema fixtures

See `examples/schema-cases.json` for a JSON Schema accepted input and a deliberate additional-property rejection case. These exercise schema shape only, not task behavior.
