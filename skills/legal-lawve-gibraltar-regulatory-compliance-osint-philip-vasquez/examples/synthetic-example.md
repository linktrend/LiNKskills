# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/gibraltar-regulatory-compliance-osint-philip-vasquez/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "issue_and_decision": "Synthetic question whether Gibraltar limitation period affects a commercial claim.",
    "gibraltar_connection": "Parties and performance are in England; contract has no Gibraltar clause or activity.",
    "candidate_regimes": "Requester mentions Gibraltar without supporting documents.",
    "primary_sources": "No Gibraltar legislation or court source attached.",
    "comparison_request": "No England/Gibraltar comparison requested.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
