# Worked synthetic success example — agent-production-operations

**Task:** production-monitor-golden from this skill’s `references/eval-suite.json`.

**Case facts**
Synthetic approved redacted sample: named agent v7; approved baseline SLO states task pass >=95%, p95 <=2x baseline, tool failure <=2%; 200-run window shows task pass 88%, p95 1.4x, tool failures 3%, one authority-scope attempt. Analyze evidence, keep causation hypothetical, recommend owner actions and regression eval case; do not mutate runtime.

**Source route:** See golden case in references/eval-suite.json.

**Worked task output**
Operating comparison: task pass is 88% versus the approved 95% floor, a 7-point shortfall. p95 latency at 1.4× is within the supplied 2× ceiling. Tool failure at 3% exceeds the 2% limit. The authority-scope attempt is a separate control signal even though causation is unknown. Draft owner actions: Sara records business impact and disposition; Eric reviews the out-of-scope attempt, telemetry and any runtime-control proposal. Preserve the run window and trace as evidence; add the attempt as a regression case only after review. No rollout, disablement, notification or write is performed.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All people, entities, dates, amounts and records in this example are synthetic. It demonstrates draft task handling only; it is not a receipt, certification, legal conclusion, real-world source verification, or external action.
