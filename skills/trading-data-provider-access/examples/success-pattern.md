# Fictional worked example

The following synthetic example demonstrates the output shape only. It is not a real analysis, evaluated fixture, or evidence of runtime behavior.

```json
{
  "status": "partial",
  "coverage_matrix": [
    {
      "provider": "Fictional Provider A",
      "field": "daily protocol TVL",
      "asset_scope": "fictional chain",
      "history": "unknown",
      "freshness": "documentation not supplied",
      "evidence_ref": "none"
    }
  ],
  "freshness_and_history": [
    {
      "field": "TVL",
      "timestamp_semantics": "unknown",
      "history_depth": "unknown"
    }
  ],
  "units_and_methodology": [
    {
      "metric": "TVL",
      "currency": "USD",
      "valuation_method": "unknown"
    }
  ],
  "terms_and_reuse": [
    {
      "status": "not reviewed",
      "redistribution": "unknown"
    }
  ],
  "quota_cost": [
    {
      "plan": "unspecified",
      "quota": "unknown",
      "price": "unknown"
    }
  ],
  "disagreement_risks": [
    "TVL methodology and chain coverage may differ; no comparable values supplied."
  ],
  "existing_path_fit": {
    "interface_ref": "not supplied",
    "assessment": "unresolved"
  },
  "smallest_gap": null,
  "handoff": {
    "owner": "Eric",
    "request": "verify existing interface field support after docs/terms review"
  },
  "limitations": [
    "Fictional shape only; no current API docs or provider access checked."
  ]
}
```
