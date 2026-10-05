# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/normalisation-juridique-christophe-quezel-ambrunaz/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "source_document": "Synthetic French contract DOCX text export, v1; original file hash is supplied separately.",
    "language_and_locale": "French (France); English-defined terms appear in quotes.",
    "editing_mode": "Propose safe typography and separately flag judgment edits; no native DOCX editor shown.",
    "style_and_whitelist": "House style absent; preserve all defined terms and citations.",
    "output_options": "Provide reversible change register and example corrections, do not claim file edited.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
