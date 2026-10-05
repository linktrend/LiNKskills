# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/pci-compliance-tanaji-hemant-naik/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "entity_role_and_volume": "Synthetic online merchant, transaction volume and validation tier unknown.",
    "data_flow_inventory": "Hosted checkout returns a payment token; PAN capture is by third party; merchant logs and support tooling not mapped.",
    "architecture_and_segmentation": "Network diagram missing; segmentation test not supplied.",
    "control_evidence": "MFA policy exists; latest access review and ASV scan absent.",
    "current_pci_authority": "No current PCI SSC standard/SAQ supplied.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
