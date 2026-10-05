# Fictional worked example

This synthetic example demonstrates task-specific input and output shape only. Names, records, and figures are fictional; it is not a real research result, evaluation, or success receipt. Unavailable evidence and uncomputed quantities remain explicit.

## Input

```json
{
  "question": "How many fictional events occurred by category in period P?",
  "data_ref": "FIC-TABLE-1",
  "schema": {
    "table": "events",
    "columns": [
      "event_id",
      "category",
      "event_date"
    ]
  },
  "dialect": "SQLite",
  "definitions": {
    "event": "one row per event"
  },
  "units": "count",
  "time_range": "2025-01-01/2025-12-31",
  "population": "all rows in fixture table",
  "permissions": "read-only"
}
```

## Output

```json
{
  "schema_ref": "references/schemas.json#/definitions/output",
  "status": "fictional_example_not_evaluation_or_receipt",
  "example": {
    "status": "complete",
    "provenance": {
      "source": "FIC-TABLE-1",
      "as_of": "synthetic",
      "row_count": 3
    },
    "query": "SELECT category, COUNT(*) AS n FROM events WHERE event_date >= :start AND event_date < :end GROUP BY category ORDER BY category;",
    "parameters": {
      "start": "2025-01-01",
      "end": "2026-01-01"
    },
    "filters_and_joins": {
      "filters": "inclusive start, exclusive end",
      "joins": "none"
    },
    "result_counts": {
      "rows_returned": 2,
      "source_rows_in_period": 3
    },
    "profile_and_quality": {
      "duplicate_event_ids": 0,
      "null_categories": 0,
      "units": "event count"
    },
    "results": [
      {
        "category": "A",
        "n": 2
      },
      {
        "category": "B",
        "n": 1
      }
    ],
    "interpretation": "In the synthetic table, category A has 2 of 3 events and B has 1; this does not explain causes.",
    "limitations": [
      "Fictional three-row fixture."
    ]
  }
}
```
