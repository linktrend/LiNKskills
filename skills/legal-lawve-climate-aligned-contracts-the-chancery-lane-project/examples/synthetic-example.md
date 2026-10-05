# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/climate-aligned-contracts-the-chancery-lane-project/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "contract_context": "Synthetic supplier agreement; governing law and current climate clause not supplied.",
    "climate_objective": "Buyer asks for annual emissions reporting and a 30% reduction by 2030; no baseline or boundary defined.",
    "operational_evidence": "Supplier can report Scope 1/2; Scope 3 data and independent assurance unavailable.",
    "approved_positions": "No approved negotiation fallback provided.",
    "authority_as_of": "No primary law attached; synthetic as-of 2026-10-04.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
