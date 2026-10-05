# People Analytics: task method and acceptance

## Trigger and task edge

Use when an authorized requester needs a people-data analysis, metric definition, engagement/attrition analysis, HR dashboard, or validated group-level model.

The single-task result is: Reproducible analysis with denominators, filters, data-quality status and caveats. Separate adjacent work stays routed to its own task.

## Required evidence

- Business question and decision/use boundary
- Authorized aggregated or pseudonymized people data with field definitions and date
- Population, cohort, geography and privacy minimum-group rule
- Metric definitions, benchmark source if applicable, and expected audience

## Procedure and branch notes

1. Define the business question, intended decision, analysis type, population and what the output must not be used to decide. Prefer aggregate descriptive work before a predictive model.
2. Inventory available fields, source dates, join keys, missingness, duplicates, definitions, sample sizes and privacy controls. Preserve exclusions and quantify how they change the denominator.
3. For each metric, write formula, numerator, denominator, time window, cohort and unit before calculation. E.g. separation rate = separations during period ÷ average headcount in period; distinguish voluntary and involuntary only when source labels support it.
4. For engagement surveys, report invitations, responses and response rate; show question scale, missing answers and group sizes before averages. Compare periods only when questions/scales/populations are comparable.
5. For attrition or hiring funnels, calculate stage counts and conversion with one consistent cohort definition; do not infer causation from subgroup differences. For compensation/pay-equity analysis, route detailed model to compensation task and require an approved factor set and qualified reviewer.
6. Use a model only if the requester has a valid use case, adequate labeled data and review capacity. Report train/test separation, calibration/error metrics, subgroup performance, leakage risks and limits; never produce individual flight-risk scores or automated employment recommendations.
7. Validate calculations independently, compare quantitative patterns with relevant qualitative context, test a credible alternative explanation, and label correlation vs cause.
8. Deliver only aggregated outputs meeting the supplied privacy threshold. Suppress or combine small cells; if no threshold is provided, expose no small subgroup results and ask the data owner. Include source/definition notes and propose monitoring only; do not set system alerts.

## Acceptance checks

- Every material input and rule has an evidence reference or is labeled an assumption/open question.
- Calculations show formula, denominator, units, population and source date; arithmetic is independently rechecked.
- Findings distinguish observed facts, attributed statements, hypotheses, assumptions and owner decisions.
- Missing evidence blocks only the conclusion that depends on it; complete unaffected sections.
- Personal data is minimized and any small-group disclosure is suppressed under the supplied privacy rule.
- Drafts contain no unsupported legal, company-policy, approval, employment or fairness conclusion.
- No external effect, message, system mutation, filing, signature or business decision occurs.

## Jurisdiction, evidence and escalation

Do not assume a jurisdiction, entity, employment classification, policy, reporting standard or legal duty. For current law, verify official primary authorities for the actual location/date and route interpretation to qualified counsel. Treat secondary articles and source examples as research leads only. Preserve date, record ID, source scope and contradictory evidence. Escalate only material safety, legal, retaliation, privacy or decision-right issues; routine drafts continue within scope.

## Source base and integrated methods

**Source selection and active integration.** Strongest base: Tuanductran HR analytics for the broad people-data analysis task. Borghei people-analytics adds explicit question-to-method framing, readiness checks, predictive evaluation and survey-analysis branches. Individual risk scoring and benchmark targets are not adopted; relevant specialized analyses route to their atomic skills. The named source originals are preserved under `references/upstream/`; see `references/source-selection.md` for pinned source identity, merge decision and exclusions.

Exact pinned repositories, commits, source trees, hashes, licensing notices and copy paths are recorded in `references/upstream/SOURCE-MANIFEST.json`. Source permissions do not confer consumer authority, and source scripts were not executed.
