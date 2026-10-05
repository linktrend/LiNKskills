# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/eu-ai-act-high-risk-classifier-oliver-schmidt-prietz/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "system_and_version": "Synthetic hiring-rank model v1 recommends candidate ordering; EU rollout under consideration.",
    "provider_deployer_roles": "Vendor supplies model; employer configures ranking; contractual roles not attached.",
    "use_case_and_users": "Recruiter-facing employment screening; no automatic rejection shown.",
    "annex_i_or_iii_evidence": "No product-safety-law link asserted; Annex III employment-use facts supplied.",
    "authority_snapshot": "No current official Act or classification guidance attached.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
