# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/hipaa-compliance-tanaji-hemant-naik/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "entity_and_role": "Synthetic analytics vendor receives lab records from a hospital; covered entity/BA status and agreement unknown.",
    "workflow_and_data": "CSV contains patient name and lab result; storage and deletion facts incomplete.",
    "systems_and_controls": "Cloud bucket access log is partial; risk analysis, MFA and backup evidence absent.",
    "business_associate_docs": "No BAA attached.",
    "official_authority_snapshot": "No current HHS authority attached.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
