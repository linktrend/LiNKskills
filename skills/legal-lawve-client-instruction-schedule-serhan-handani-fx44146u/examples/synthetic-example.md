# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/client-instruction-schedule-serhan-handani-fx44146u/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "matter_and_forum": "Synthetic Smith v North Ltd; forum and counsel owner not established.",
    "case_file_refs": "Pleadings and 3 letters supplied; letter refers to missing Exhibit 7; two witness notes disagree on delivery date.",
    "issues_and_opponent_positions": "Delivery on 4 May vs 9 May; opponent asserts 4 May.",
    "client_accessibility": "Client reports dyslexia; supervising solicitor suitability decision not supplied.",
    "output_format": "Accessible issue-by-issue table and one-page cover-note draft.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
