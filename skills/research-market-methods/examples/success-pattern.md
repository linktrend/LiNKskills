# Fictional worked example

This synthetic example demonstrates task-specific input and output shape only. Names, records, and figures are fictional; it is not a real research result, evaluation, or success receipt. Unavailable evidence and uncomputed quantities remain explicit.

## Input

```json
{
  "decision": "estimate annual addressable spend for fictional product",
  "product": "Fictional analytics tool",
  "geography": "Region R",
  "period": "2025",
  "market_boundary": "eligible mid-market firms",
  "unit": "annual subscription USD",
  "source_data": "none; synthetic assumptions only",
  "sizing_assumptions": {
    "eligible_firms": 1000,
    "annual_price_usd": 1200
  },
  "survey_target": "operators",
  "segments": [
    "small",
    "mid-market"
  ],
  "precision_needs": "exploratory only"
}
```

## Output

```json
{
  "schema_ref": "references/schemas.json#/definitions/output",
  "status": "fictional_example_not_evaluation_or_receipt",
  "example": {
    "status": "complete",
    "market_boundary": "fictional eligible firms in Region R; annual spend",
    "top_down": {
      "eligible_firms": 1000,
      "annual_price_usd": 1200,
      "calculation": "1000 × $1,200",
      "tam_usd": 1200000,
      "evidence": "synthetic assumptions, not market facts"
    },
    "bottom_up": {
      "calculation": null,
      "status": "not computed",
      "reason": "no customer/seat/penetration evidence"
    },
    "segment_comparison": [
      {
        "segment": "mid-market",
        "period": "2025",
        "basis": "fictional firm count",
        "value": 1000,
        "unit": "firms"
      }
    ],
    "survey_design": {
      "target": "operators",
      "sampling_frame": "not supplied",
      "method": "not finalized",
      "sample_size": "not computed",
      "limitation": "exploratory requirement does not establish precision"
    },
    "assumption_ledger": [
      "All figures are fictional and user-style assumptions only."
    ],
    "unresolved_gaps": [
      "Verify firm count, willingness to pay, competitors and adoption rate."
    ]
  }
}
```
