# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/dpdpa-tanaji-hemant-naik/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "entity_and_processing": "Synthetic India retailer stores online orders; paper receipts also exist; which data is digitized is partly unknown.",
    "data_and_people": "Adult customers and some child purchasers; identifiers and data source unclear.",
    "purpose_and_basis": "Order fulfilment and promotional messages; separate consent evidence absent.",
    "processor_and_transfers": "One hosted CRM; processor terms and data location unknown.",
    "official_authority_snapshot": "No current official Act, Rules or commencement notice attached.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
