# Source selection and comparison

## Selected source

- `anthropics/knowledge-work-plugins@8444efcd48f7012f09797778a36a33e73d0861f4:human-resources/skills/recruiting-pipeline/SKILL.md`
- Distinct task: Summarize recruiting funnel data accurately and identify process bottlenecks; do not evaluate candidate worth, change candidate status, contact candidates or make hiring decisions.
- Source subtree and Apache-2.0 notice are copied byte-for-byte under `references/upstream/`; source hashes are in `SOURCE-MANIFEST.json`.

## Task boundary

Use when asked for a recruiting pipeline status, candidate counts by stage, stage aging, conversion or source effectiveness from authorized ATS or supplied data. This task remains separate from adjacent HR tasks because its primary output, trigger, and evidence differ. The source's connector names and suggested automatic operations are not treated as available tools or authority.

## Adaptation decisions

- Retained: source task's actual intent and task-specific methods reflected in `advanced/advanced.md`.
- Adapted: specific calculations/retrieval/output sections are evidence-based, typed, privacy-minimized and mapped to actual visible consumer tools.
- Excluded: automatic ATS/HRIS updates, outbound messages, invented policy/legal/market/rating rules, and decision authority.
- Draft status: no library admission, runtime qualification or activation is claimed.

## Neighboring source comparison

- This reports ATS stage and conversion facts. It does not design interview plans, source candidates, decide selection, draft/issue offers, or run end-to-end recruiting.
