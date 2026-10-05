# Source selection and comparison

## Selected source

- `anthropics/knowledge-work-plugins@8444efcd48f7012f09797778a36a33e73d0861f4:human-resources/skills/draft-offer/SKILL.md`
- Distinct task: Assemble supplied approved terms into a clear, internally consistent offer draft and manager notes; never extend or send the offer.
- Source subtree and Apache-2.0 notice are copied byte-for-byte under `references/upstream/`; source hashes are in `SOURCE-MANIFEST.json`.

## Task boundary

Use when a hiring owner requests a draft offer letter or negotiation brief for a candidate whose offer decision is already in scope. This task remains separate from adjacent HR tasks because its primary output, trigger, and evidence differ. The source's connector names and suggested automatic operations are not treated as available tools or authority.

## Adaptation decisions

- Retained: source task's actual intent and task-specific methods reflected in `advanced/advanced.md`.
- Adapted: specific calculations/retrieval/output sections are evidence-based, typed, privacy-minimized and mapped to actual visible consumer tools.
- Excluded: automatic ATS/HRIS updates, outbound messages, invented policy/legal/market/rating rules, and decision authority.
- Draft status: no library admission, runtime qualification or activation is claimed.

## Neighboring source comparison

- Offer composition is separate from compensation analysis: it assembles already approved terms into letter text; compensation analysis provides evidence/options and never sets offer terms.
