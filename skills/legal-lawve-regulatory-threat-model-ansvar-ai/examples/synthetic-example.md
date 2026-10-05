# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/regulatory-threat-model-ansvar-ai/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "system_snapshot": "Synthetic support chatbot: web UI \u2192 API service \u2192 hosted model; admin console separate trust zone.",
    "data_flows_and_people": "User messages may contain email addresses; logs and model retention unspecified.",
    "threat_scope": "Protect account data, prompt content, admin credentials and service availability.",
    "jurisdictions_and_roles": "Operating entity and market not provided; legal scope unknown.",
    "source_evidence": "Architecture sketch only; dependency list and current vulnerability feed absent.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
