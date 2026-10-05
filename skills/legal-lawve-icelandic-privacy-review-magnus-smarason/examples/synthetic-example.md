# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/icelandic-privacy-review-magnus-smarason/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "processing_description": "Synthetic Iceland clinic intake uses kennitala, appointment details and optional health notes.",
    "controller_processor_roles": "Clinic decides purpose; cloud vendor hosts records; processor terms not supplied.",
    "document_and_controls": "Notice says data retained \u201cas needed\u201d; no retention schedule or DSAR workflow supplied.",
    "iceland_connection": "Clinic established in Iceland; patient location varies.",
    "authority_snapshot": "No current Icelandic regulator/primary source attached.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
