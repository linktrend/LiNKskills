# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/nil-contract-reviewer-samir-patel/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "athlete_context": "Synthetic college basketball player; institution/state and remaining eligibility not provided.",
    "deal_and_agreement": "Brand endorsement grants perpetual, worldwide, irrevocable likeness rights for $500; full contract has 11 pages.",
    "institution_policy": "Current NIL disclosure policy not supplied.",
    "existing_deals_and_conflicts": "Other sponsorships unknown; exclusivity terms absent.",
    "state_and_authorities": "No state, NCAA/institution policy or current primary source confirmed.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
