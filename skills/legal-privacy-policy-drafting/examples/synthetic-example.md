# Synthetic example

```json
{
  "task_id": "20261004-1200-PRIV-000001",
  "request_ref": "synthetic-policy-brief-1",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/privacy-policy-stephane-boghossian/SKILL.md",
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/privacy-policy-generator-malik-taiar/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "business_identity_and_contact": "Synthetic example: business_identity_and_contact",
    "product_and_user_journeys": "Synthetic example: product_and_user_journeys",
    "user_geographies_and_jurisdictions": "Synthetic: company and user locations conflict; applicable law unresolved.",
    "data_categories_and_sources": "Synthetic example: data_categories_and_sources",
    "purposes_and_basis_evidence": "Synthetic: order fulfillment is described; marketing basis undocumented.",
    "vendors_and_transfers": "Synthetic example: vendors_and_transfers",
    "cookies_and_platform_tools": "Synthetic example: cookies_and_platform_tools",
    "retention_and_rights_processes": "Synthetic example: retention_and_rights_processes",
    "approved_template": "Synthetic: counsel template v2 supplied; legal currency not independently verified.",
    "review_mode": "Synthetic example: review_mode",
    "authority_sources_and_as_of": "Synthetic example: authority_sources_and_as_of"
  }
}
```

Expected: show jurisdiction conflict as unresolved; draft only confirmed order-fulfillment clauses; mark marketing basis, transfers and other unsupported claims as visible gaps; include practice-to-clause reconciliation and counsel/founder review.
