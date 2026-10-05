# Source selection and comparison

## Selected source

- `anthropics/knowledge-work-plugins@8444efcd48f7012f09797778a36a33e73d0861f4:human-resources/skills/comp-analysis/SKILL.md`
- Distinct task: Analyze compensation positioning from authorized company records and explicitly identified market evidence. Produce a sourced comparison and options; do not set pay or make an employment decision.
- Source subtree and Apache-2.0 notice are copied byte-for-byte under `references/upstream/`; source hashes are in `SOURCE-MANIFEST.json`.

## Task boundary

Use when asked to benchmark a role, assess pay-band placement, compare offer competitiveness, analyze supplied compensation data, or model an equity grant. This task remains separate from adjacent HR tasks because its primary output, trigger, and evidence differ. The source's connector names and suggested automatic operations are not treated as available tools or authority.

## Adaptation decisions

- Retained: source task's actual intent and task-specific methods reflected in `advanced/advanced.md`.
- Adapted: specific calculations/retrieval/output sections are evidence-based, typed, privacy-minimized and mapped to actual visible consumer tools.
- Excluded: automatic ATS/HRIS updates, outbound messages, invented policy/legal/market/rating rules, and decision authority.
- Draft status: no library admission, runtime qualification or activation is claimed.

## Neighboring source comparison

- Tuanductran `hr-compensation-benefits` covers broader compensation/benefits program strategy. This pack is the narrower benchmarking, band-position and equity-analysis task; use the broader pack for program design, not as a duplicate.
