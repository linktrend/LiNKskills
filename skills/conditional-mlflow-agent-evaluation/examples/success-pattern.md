# Worked synthetic success example — conditional-mlflow-agent-evaluation

**Task:** task-specific-golden from this skill’s `references/eval-suite.json`.

**Case facts**
Synthetic. Evaluate a selected set of agent runs against approved task-shaped cases; report scorer definition, dataset/version, per-case evidence and uncertainty. No confirmed jurisdiction/backend or authorized native action interface. Produce only the conditional work product or exact gap report; preserve source/date/uncertainty.

**Source route:** See golden case in references/eval-suite.json.

**Worked task output**
Evaluation-design status: NOT RUN. The fixture gives no confirmed MLflow backend, dataset/version, scorer interface or authorized run boundary, so no run result or score can be reported. Prepared candidate matrix row (design only; not an executed evaluation):

| Case | Status | Expected behavior | Candidate scorer rule | Evidence required |
|---|---|---|---|---|
| `backend-prerequisite-gap-001` | NOT RUN | State that the backend/dataset/scorer/run boundary is unconfirmed; do not invent an evaluation result. | Deterministic boundary check: fail if the output claims a run, score, or dataset result without a reconciled run ID and approved dataset/version. Threshold remains owner approval required. | Eric’s backend/tool schema; dataset ID/version; approved task cases and rubric; authorized run record and trace IDs. |

This is a proposed fixture illustrating the gate, not an approved rubric or MLflow result. Obtain owner approval for criteria and thresholds before using it.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All people, entities, dates, amounts and records in this example are synthetic. It demonstrates draft task handling only; it is not a receipt, certification, legal conclusion, real-world source verification, or external action.
