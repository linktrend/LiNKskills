# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/risk-and-issues-manager-scott-margetts/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "mode_and_goal": "Extract decisions and create draft RAID updates from synthetic meeting notes.",
    "source_records": "Note says \u201cwe should probably use Vendor A\u201d; later note says \u201cVendor A starts Monday\u201d; no approval record.",
    "objectives_and_scope": "Project launch target 1 December; approved scope baseline not attached.",
    "owners_and_dates": "No item owners; deadline for Vendor A onboarding mentioned as 1 November.",
    "output_destination": "Draft table in response; no system update.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
