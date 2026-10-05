# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/collaboration-platform-advisor-scott-margetts/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "matter_or_program_scope": "Synthetic three-jurisdiction commercial matter with internal team, client contacts and outside counsel.",
    "platform_capabilities": "Teams-like platform; no live tenant/toolcard supplied.",
    "workflow_pain_points": "Weekly status collection is late; owners copy dates manually from a task spreadsheet.",
    "information_classification": "Privileged advice, internal budget and client-shareable filings.",
    "success_measures": "One reliable milestone view updated weekly; owner is legal operations lead.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
