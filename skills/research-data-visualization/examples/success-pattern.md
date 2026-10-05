# Fictional worked example

This synthetic example demonstrates task-specific input and output shape only. Names, records, and figures are fictional; it is not a real research result, evaluation, or success receipt. Unavailable evidence and uncomputed quantities remain explicit.

## Input

```json
{
  "question": "Show monthly fictional signup counts by channel.",
  "audience": "product team",
  "dataset_ref": "FIC-SIGNUPS",
  "schema": "month, channel, count",
  "provenance": "synthetic",
  "units": "users",
  "time_period": "2025-Q1",
  "grouping": "month and channel",
  "output_destination": "static slide",
  "interactivity_required": false
}
```

## Output

```json
{
  "schema_ref": "references/schemas.json#/definitions/output",
  "status": "fictional_example_not_evaluation_or_receipt",
  "example": {
    "status": "complete",
    "chart_choice": {
      "mark": "line with one series per channel",
      "reason": "ordered monthly time comparison",
      "aggregation": "sum of counts by month/channel"
    },
    "data_transform_notes": {
      "source": "fictional three-month sample",
      "missing_months": "none",
      "units": "users",
      "denominator": "raw counts; no population denominator supplied"
    },
    "chart_spec": {
      "x": "month",
      "y": "count",
      "series": "channel",
      "title": "Synthetic signups by month and channel",
      "zero_baseline": "yes",
      "uncertainty": "no interval; no sampling model supplied"
    },
    "artifact_status": "specification_only",
    "accessibility_checks": [
      "Direct labels or distinct marker/dash patterns",
      "Color contrast check required at render",
      "Do not use color alone"
    ],
    "visual_integrity_checks": [
      "No truncated y-axis",
      "Show units and period"
    ],
    "limitations": [
      "Fictional data; no chart rendered."
    ]
  }
}
```
