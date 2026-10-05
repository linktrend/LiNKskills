# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/tsa-compliance-tanaji-hemant-naik/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "operator_and_sector": "Synthetic freight railroad says it may be subject to TSA requirements; coverage documents absent.",
    "critical_systems": "Dispatch and signaling systems listed; criticality analysis not supplied.",
    "directive_and_order_refs": "No current directive/order text or notice attached.",
    "security_evidence": "Coordinator listed but 24/7 coverage, incident plan and control evidence absent.",
    "incident_or_reporting_facts": "No current incident asserted.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
