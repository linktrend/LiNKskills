# Fictional worked example

This synthetic example demonstrates task-specific input and output shape only. Names, records, and figures are fictional; it is not a real research result, evaluation, or success receipt. Unavailable evidence and uncomputed quantities remain explicit.

## Input

```json
{
  "question": "Compare how two fictional reports define outcome Y.",
  "documents": [
    {
      "source_id": "FIC-A",
      "title": "Synthetic report A",
      "version": "1",
      "locator": "pp. 2-3"
    },
    {
      "source_id": "FIC-B",
      "title": "Synthetic report B",
      "version": "1",
      "locator": "section 4"
    }
  ],
  "desired_depth": "comparative",
  "audience": "analyst",
  "output_format": "markdown"
}
```

## Output

```json
{
  "schema_ref": "references/schemas.json#/definitions/output",
  "status": "fictional_example_not_evaluation_or_receipt",
  "example": {
    "status": "complete",
    "source_notes": [
      {
        "source_id": "FIC-A",
        "claim": "Y is measured at week 4.",
        "evidence_locator": "p. 2",
        "method": "self-report",
        "limitation": "synthetic example"
      },
      {
        "source_id": "FIC-B",
        "claim": "Y is measured at week 12.",
        "evidence_locator": "section 4",
        "method": "instrument score",
        "limitation": "synthetic example"
      }
    ],
    "comparison_table": [
      {
        "dimension": "measurement time",
        "FIC-A": "week 4",
        "FIC-B": "week 12",
        "implication": "estimates are not directly comparable without a time-alignment rationale"
      }
    ],
    "argument_map": [
      "Both discuss Y.",
      "They use different measurement times and measures."
    ],
    "synthesis": "The two reports address the same named outcome but operationalize it differently; do not pool values without a harmonization rule.",
    "omissions_and_conflicts": [
      "No numerical result or population details supplied."
    ],
    "source_list": [
      "FIC-A (fictional)",
      "FIC-B (fictional)"
    ],
    "citations_verified": false
  }
}
```
