# Fictional worked example

The following synthetic example demonstrates the output shape only. It is not a real analysis, evaluated fixture, or evidence of runtime behavior.

```json
{
  "status": "partial",
  "coverage_by_date": [
    {
      "date": "fictional-D1",
      "eligible_assets": 4,
      "valid_pairs": 4,
      "coverage": "4/4"
    }
  ],
  "ic_by_date": [
    {
      "date": "fictional-D1",
      "rank_ic": 0.6,
      "valid_pairs": 4
    }
  ],
  "ic_summary": {
    "mean": 0.6,
    "median": 0.6,
    "std": "undefined: n=1",
    "ic_ir": null,
    "interpretation": "one synthetic date; no inference"
  },
  "dependence_inference": {
    "method": "not computed",
    "horizon_overlap": "unknown",
    "effective_breadth": null
  },
  "quantiles": [
    {
      "bucket": "Q1",
      "return": null,
      "return_unit": "fraction",
      "weighting": "not supplied",
      "reason": "Return quantile was not computed because no panel was supplied."
    }
  ],
  "turnover_capacity_costs": {
    "turnover": null,
    "costs": null,
    "capacity": null
  },
  "decay": [],
  "fold_stability": [],
  "selection_adjustment": {
    "variants_tried": [
      "fictional single factor"
    ],
    "outer_holdout": "not evaluated"
  },
  "causal_assessment": {
    "status": "not_claimed",
    "reason": "no intervention/estimand"
  },
  "proposal": null,
  "gaps": [
    "No real return panel/cost inputs."
  ]
}
```
