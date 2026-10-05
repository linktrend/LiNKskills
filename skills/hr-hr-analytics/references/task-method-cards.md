# Task-specific method cards

Use only the branch matching the requested deliverable. Preserve the full source procedures under `upstream/`; this concise card index is not a substitute for the substantive Phase 2 method.

- **Branch 1:** Define the business question, intended decision, analysis type, population and what the output must not be used to decide. Prefer aggregate descriptive work before a predictive model.
- **Branch 2:** Inventory available fields, source dates, join keys, missingness, duplicates, definitions, sample sizes and privacy controls. Preserve exclusions and quantify how they change the denominator.
- **Branch 3:** For each metric, write formula, numerator, denominator, time window, cohort and unit before calculation. E.g. separation rate = separations during period ÷ average headcount in period; distinguish voluntary and involuntary only when source labels support it.
- **Branch 4:** For engagement surveys, report invitations, responses and response rate; show question scale, missing answers and group sizes before averages. Compare periods only when questions/scales/populations are comparable.
- **Branch 5:** For attrition or hiring funnels, calculate stage counts and conversion with one consistent cohort definition; do not infer causation from subgroup differences. For compensation/pay-equity analysis, route detailed model to compensation task and require an approved factor set and qualified reviewer.
- **Branch 6:** Use a model only if the requester has a valid use case, adequate labeled data and review capacity. Report train/test separation, calibration/error metrics, subgroup performance, leakage risks and limits; never produce individual flight-risk scores or automated employment recommendations.
- **Branch 7:** Validate calculations independently, compare quantitative patterns with relevant qualitative context, test a credible alternative explanation, and label correlation vs cause.
- **Branch 8:** Deliver only aggregated outputs meeting the supplied privacy threshold. Suppress or combine small cells; if no threshold is provided, expose no small subgroup results and ask the data owner. Include source/definition notes and propose monitoring only; do not set system alerts.
