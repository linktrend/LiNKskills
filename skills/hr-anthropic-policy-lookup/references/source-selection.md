# Source selection and comparison

## Selected source

- `anthropics/knowledge-work-plugins@8444efcd48f7012f09797778a36a33e73d0861f4:human-resources/skills/policy-lookup/SKILL.md`
- Distinct task: Find the current authoritative internal policy text and explain it plainly with exact citations; do not create policy or give unsupported legal conclusions.
- Source subtree and Apache-2.0 notice are copied byte-for-byte under `references/upstream/`; source hashes are in `SOURCE-MANIFEST.json`.

## Task boundary

Use when asked what an existing company handbook or policy says about leave, benefits, remote work, expenses, travel, conduct or a related procedure. This task remains separate from adjacent HR tasks because its primary output, trigger, and evidence differ. The source's connector names and suggested automatic operations are not treated as available tools or authority.

## Adaptation decisions

- Retained: source task's actual intent and task-specific methods reflected in `advanced/advanced.md`.
- Adapted: specific calculations/retrieval/output sections are evidence-based, typed, privacy-minimized and mapped to actual visible consumer tools.
- Excluded: automatic ATS/HRIS updates, outbound messages, invented policy/legal/market/rating rules, and decision authority.
- Draft status: no library admission, runtime qualification or activation is claimed.

## Neighboring source comparison

- This resolves questions against existing approved policy text. It is separate from handbook/policy authoring, compliance audits, and legal advice.
