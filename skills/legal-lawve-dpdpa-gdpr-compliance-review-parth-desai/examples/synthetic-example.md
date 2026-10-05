# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/dpdpa-gdpr-compliance-review-parth-desai/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "document_text_and_type": "Synthetic SaaS DPA v3: processor may use data for service and analytics; no subprocessor list attached.",
    "parties_and_roles": "India vendor and EU startup; contract labels parties controller/processor but actual purposes not established.",
    "data_categories_and_people": "Account data and support tickets; children/sensitive data unknown.",
    "processing_and_transfer_facts": "Hosting region and onward transfers unknown; analytics purpose stated.",
    "authority_snapshot": "No current official Act/Rules or GDPR source attached.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
