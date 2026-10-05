# Source selection and comparison

## Selected source

- `anthropics/knowledge-work-plugins@8444efcd48f7012f09797778a36a33e73d0861f4:human-resources/skills/people-report/SKILL.md`
- Distinct task: Answer a specific people question with reproducible definitions, aggregate metrics and limitations; avoid unsupported individual risk profiling.
- Source subtree and Apache-2.0 notice are copied byte-for-byte under `references/upstream/`; source hashes are in `SOURCE-MANIFEST.json`.

## Task boundary

Use when asked for a defined workforce snapshot or analysis such as headcount, attrition, representation, organization health or engagement from authorized data. This task remains separate from adjacent HR tasks because its primary output, trigger, and evidence differ. The source's connector names and suggested automatic operations are not treated as available tools or authority.

## Adaptation decisions

- Retained: source task's actual intent and task-specific methods reflected in `advanced/advanced.md`.
- Adapted: specific calculations/retrieval/output sections are evidence-based, typed, privacy-minimized and mapped to actual visible consumer tools.
- Excluded: automatic ATS/HRIS updates, outbound messages, invented policy/legal/market/rating rules, and decision authority.
- Draft status: no library admission, runtime qualification or activation is claimed.

## Neighboring source comparison

- Tuanductran `hr-analytics` covers broader dashboards, predictive analysis and data governance. This pack answers a defined people-report question with denominator, privacy and methods controls; do not fold an entire analytics platform workflow into it.
