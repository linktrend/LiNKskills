# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/az-eu-website-privacy-audit-mirza-chiragov/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "site_materials": "Synthetic site: az-example.test, privacy text dated 2024-03, banner screenshot shows Accept and Settings, no refusal button visible.",
    "site_languages": "Azerbaijani and English; only English supplied.",
    "audience_and_market": "Founder says AZ-only; checkout screenshot shows EU country selector; actual targeting unknown.",
    "processing_context": "Marketing site with analytics cookie; controller legal entity not supplied.",
    "audit_depth": "Evidence table plus concise summary.",
    "as_of_date": "Synthetic review date 2026-10-04; current official sources not supplied.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
