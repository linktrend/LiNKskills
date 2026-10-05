# Financial control test method cards

Use only the card matching the named control and requested test objective. These cards preserve usable method branches from the pinned audit-support and SOX-testing sources while treating their example frequency bands, legal standards, and default assumptions as nonbinding. See the exact originals and license notice under `upstream/anthropics--knowledge-work-plugins@8444efcd48f7/finance/skills/`.

## Card A — Scope and control matrix

Capture control ID/name, process, owner, performer, reviewer, frequency, population, timing, evidence retained, control objective, relevant assertion (if provided), preventive/detective, manual/automated/IT-dependent-manual, and source-of-report dependency. Map a control area only to the owner's actual process: revenue/order-to-cash, procurement-to-pay/AP, payroll, period close, treasury, fixed assets, inventory, IT general controls, entity-level monitoring, or journal entries. Do not infer a key control from the area label. Record which framework and reporting entity the owner says are in scope; otherwise mark `not established`.

## Card B — Population and sample design

Before selection, preserve the report/query ID, filters, extraction timestamp, date window, statuses, population row count and amount total, and tie-out source. If the population is not complete/reliable, explain the affected procedures and do not represent sample results as population evidence. Use only the authorized plan's sample size and method. A random sample needs a fixed ordered population and recorded algorithm/seed. A targeted selection (high value, unusual, period end, new vendor/customer, prior exception) is a separate risk-focused sample and must not be described as representative. A systematic sample must state its interval, start point and ordered population. Provide replacement/invalid-item handling only when the approved method specifies it. Source examples that suggest a number of samples by frequency are prompts to discuss a proposed plan, never defaults or audit standards.

## Card C — Evidence and test-result table

One row per selected item: `selection_id`, population ID, transaction date/amount, control performer and reviewer, expected step/criterion, evidence ID and date, evidence observed, result (`pass`, `exception`, `not tested`, `insufficient evidence`), exception fact, explanation attributed to its speaker, and follow-up owner/date. Preserve original evidence references; do not paste raw restricted finance evidence into reusable skill material. For automated evidence, distinguish current configuration inspection from evidence over the whole period. For IT-dependent manual evidence, test both the manual review and report completeness/accuracy when those are in scope.

## Card D — Report completeness and accuracy (IPE)

For a report or spreadsheet used as evidence, record source system/report name, report owner, query or saved-view identity, parameters and filters, covered dates, record count, amount total, extraction timestamp, and destination/evidence ID. Independently compare completeness and accuracy attributes to an authorized source or control total. Record failures separately from the control test. A screenshot/signoff does not, by itself, establish report population completeness, field accuracy or reviewer precision.

## Card E — Design vs operation

**Design:** map the control's performer, action, precision/timing, evidence, exception escalation and stated objective; identify missing design elements as questions, not as automatic deficiencies. **Operation:** inspect dated instance evidence that the specified performer executed the action and handled exceptions during the requested period. A policy or process narrative alone cannot establish operating effectiveness. Preserve design observations and operating deviations in separate sections.

## Card F — Exception aggregation and draft discussion

Report each observed deviation and evidence limitation independently. Aggregate only under an approved company/auditor framework and supplied materiality/likelihood criteria. Prompt the accountable reviewer for potential magnitude, likelihood, affected account/assertion/period, key-control status, prior related issues, and supported compensating evidence. Do not decide `significant deficiency`, `material weakness`, audit reliance, or remediation sufficiency without the applicable authority and facts. The output is a factual discussion draft, not a certification or audit opinion.

## Source map

- `upstream/.../finance/skills/audit-support/SKILL.md`: control attributes and matrix, evidence/documentation, design/operating tests, report/IPE checks, exceptions, IT-dependent/automated branches, and deficiency discussion.
- `upstream/.../finance/skills/sox-testing/SKILL.md`: control-area/task triggers, population and sampling method branches, sample reproducibility, test workpaper structure and period-specific evidence.
- SOX-only procedures remain conditional on confirmed scope. Do not reuse source legal citations or source sample-size tables as current guidance without an authoritative current source and applicability check.
