# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/bacen-compliance-sentinel-rafael-mastronardi/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "institution_and_activities": "Synthetic fintech says it is a payment institution in Brazil; license/supervisory status not supplied.",
    "regulatory_topics": "Cloud outsourcing and Open Finance consent review.",
    "control_evidence": "Vendor contract mentions encryption; no exit plan, audit right or consent log supplied.",
    "service_and_data_flow": "Cloud region in US; customer transaction data may be processed; exact criticality unknown.",
    "current_authority_refs": "No official BCB/CMN text attached.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
