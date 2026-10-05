# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/icelandic-contract-review-magnus-smarason/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "contract_and_version": "Synthetic services agreement v4 plus unsigned schedule; amendment referenced but missing.",
    "parties_and_transaction": "Icelandic software supplier and foreign buyer; service delivered remotely.",
    "governing_law_and_forum": "Agreement clause states Icelandic law; forum clause blank.",
    "business_objectives": "Buyer wants termination flexibility and data export; no approved fallback.",
    "primary_authority_snapshot": "No current Icelandic primary authority supplied.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
