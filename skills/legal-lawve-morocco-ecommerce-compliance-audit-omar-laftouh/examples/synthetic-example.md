# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/agent-authority-charter-builder-arkadiy-miteiko/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "agent_identity": "Synthetic refund assistant v2; staging only; purpose is to draft refund recommendations.",
    "principal_and_delegation": "No signed delegation supplied; product manager says refunds under $20 are allowed.",
    "systems_and_data": "Read order records; can draft case notes; no payment write interface supplied.",
    "action_inventory": "Read order, draft recommendation, approve refund, initiate payment, close case.",
    "human_controls": "Finance owner not named; support lead can review draft; suspension route unknown.",
    "evidence_requirements": "Case ID, source records, reviewer identity, approval timestamp, policy version.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
