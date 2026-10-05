# Fictional worked example

This synthetic example demonstrates task-specific input and output shape only. Names, records, and figures are fictional; it is not a real research result, evaluation, or success receipt. Unavailable evidence and uncomputed quantities remain explicit.

## Input

```json
{
  "learning_target": "predict next-period class Y",
  "data_ref": "FIC-PANEL-1",
  "provenance": "synthetic panel",
  "observation_unit": "entity-day",
  "feature_timing": "available at prior close",
  "target_horizon": "next day",
  "train_test_chronology": "train before 2024-01; test 2024-01 onward",
  "groups": "entity",
  "leakage_risks": [
    "overlap",
    "scaling"
  ],
  "baseline": "majority class",
  "metric": "balanced accuracy",
  "deployment_decision": "research only",
  "constraints": "no deployment"
}
```

## Output

```json
{
  "schema_ref": "references/schemas.json#/definitions/output",
  "status": "fictional_example_not_evaluation_or_receipt",
  "example": {
    "status": "partial",
    "task_frame": {
      "target": "next-period Y class",
      "observation_unit": "entity-day",
      "horizon": "1 day",
      "feature_availability": "prior close, assumed for fixture"
    },
    "data_checks": {
      "rows": 12,
      "entities": 2,
      "time_range": "synthetic 2023-12 to 2024-01",
      "missingness": "not reported",
      "leakage_flags": [
        "scaling must fit on train only",
        "purge overlapping label window"
      ]
    },
    "validation_design": {
      "split": "chronological",
      "train": "before 2024-01",
      "test": "2024-01",
      "grouping": "entity-aware",
      "holdout_status": "not evaluated"
    },
    "baseline": {
      "name": "majority class",
      "score": null,
      "status": "not computed"
    },
    "pipeline": {
      "preprocessing": "fit on training folds only",
      "model": "not fit",
      "selection": "not performed"
    },
    "metrics_and_uncertainty": {
      "metric": "balanced accuracy",
      "estimate": null,
      "interval": null,
      "status": "not evaluated"
    },
    "generalization_risks": [
      "Only two synthetic entities; test period too small to support a performance claim."
    ],
    "findings": [
      "No model was trained; this is a validation plan, not evidence of predictive performance."
    ]
  }
}
```
