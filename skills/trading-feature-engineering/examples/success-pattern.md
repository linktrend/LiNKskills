# Fictional worked example

The following synthetic example demonstrates the output shape only. It is not a real analysis, evaluated fixture, or evidence of runtime behavior.

```json
{
  "status": "partial",
  "definitions": [
    {
      "name": "mom_5",
      "formula": "close[t-1]/close[t-6]-1",
      "units": "fraction",
      "entity_group": "instrument",
      "lookback_bars": 5,
      "known_at": "bar close plus one bar delay",
      "warmup": "6 bars",
      "null_policy": "preserve",
      "denominator_rule": "prior close must be nonzero",
      "hypothesis": "short trend persistence; untested"
    }
  ],
  "availability_audit": [
    {
      "feature": "close[t]",
      "decision_time": "same bar close",
      "finding": "not available before close; lag required"
    }
  ],
  "label_timing": {
    "target": "5-session arithmetic return",
    "decision": "close t",
    "first_fill": "next session open",
    "exit": "close t+5",
    "same_bar_tie": "not applicable"
  },
  "folds": [
    {
      "fold": "fictional-1",
      "preprocessing_fit": "train only",
      "purge": "label windows overlap at boundary; 5 observations excluded",
      "embargo": "not set; dependence analysis missing"
    }
  ],
  "redundancy": [
    "Pairwise correlations not computed; input data absent."
  ],
  "validation": {
    "status": "not_evaluated",
    "metrics": []
  },
  "proposal": null,
  "gaps": [
    "Point-in-time universe and price source not supplied."
  ],
  "owner_handoffs": [
    "Eric: implementation contract if requested."
  ]
}
```
