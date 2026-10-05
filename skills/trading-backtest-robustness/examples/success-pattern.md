# Fictional worked example

The following synthetic example demonstrates the output shape only. It is not a real analysis, evaluated fixture, or evidence of runtime behavior.

```json
{
  "status": "partial",
  "protocol_card": {
    "hypothesis_version": "fictional-v1",
    "signal_time": "session close",
    "first_fill": "next session open",
    "data_window": "fictional 3 sessions",
    "train_validation_holdout": "not defined",
    "cost_stack": "commission supplied as fictional 1 bp/side; spread/impact missing"
  },
  "fold_results": [
    {
      "fold": "fictional-fold-1",
      "gross_return": "not computed",
      "net_return": "not computed",
      "status": "insufficient observations"
    }
  ],
  "portfolio_series": {
    "initial_nav": 100000,
    "currency": "USD",
    "values": [
      100000,
      100100
    ],
    "fictional": true,
    "reconciliation": "two synthetic marks; not a performance estimate"
  },
  "cost_sensitivity": [
    {
      "case": "base",
      "status": "partial",
      "missing": [
        "spread",
        "impact"
      ]
    }
  ],
  "parameter_surface": [],
  "trial_adjustment": {
    "variants_recorded": 1,
    "untouched_holdout": "not evaluated",
    "DSR": "not computed"
  },
  "worst_case": {
    "status": "unknown"
  },
  "limitations": [
    "Synthetic illustration only."
  ],
  "decision": "inconclusive",
  "advisory_proposal": null,
  "gaps": [
    "No point-in-time market history or execution assumptions."
  ],
  "handoffs": [
    "Eric for event-level simulator if authorized."
  ]
}
```
