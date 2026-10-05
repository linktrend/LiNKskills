# Fictional worked example

This synthetic example demonstrates task-specific input and output shape only. Names, records, and figures are fictional; it is not a real research result, evaluation, or success receipt. Unavailable evidence and uncomputed quantities remain explicit.

## Input

```json
{
  "research_question": "How does intervention X affect outcome Y in population P?",
  "purpose": "orientation",
  "review_type": "scoping",
  "audience": "research team",
  "population": "fictional adults with condition P",
  "concepts": [
    "intervention X",
    "outcome Y"
  ],
  "date_bounds": "2019-01-01/2026-10-05",
  "source_access": [
    "fictional database A",
    "user-supplied reports"
  ],
  "constraints": "English, abstracts available",
  "as_of": "2026-10-05"
}
```

## Output

```json
{
  "schema_ref": "references/schemas.json#/definitions/output",
  "status": "fictional_example_not_evaluation_or_receipt",
  "example": {
    "status": "partial",
    "search_log": [
      {
        "source": "fictional database A",
        "query": "(\"intervention X\" AND outcome Y)",
        "searched_on": "2026-10-05",
        "records_returned": 2,
        "deduplicated": 1,
        "coverage_note": "synthetic fixture only"
      }
    ],
    "screening_flow": {
      "retrieved": 2,
      "duplicates_removed": 1,
      "screened": 1,
      "included": 1,
      "exclusion_reasons": []
    },
    "inclusion_criteria": [
      "population P",
      "reports outcome Y"
    ],
    "evidence_synthesis": [
      {
        "theme": "short-term outcome",
        "claim": "One fictional report describes a short-term change; direction and magnitude are not supplied.",
        "source_ids": [
          "FIC-1"
        ],
        "design": "unknown",
        "quality_limits": [
          "abstract only"
        ],
        "counterevidence": "none available"
      }
    ],
    "bibliography": [
      {
        "source_id": "FIC-1",
        "citation": "Fictional report FIC-1 (synthetic; not a real citation)",
        "verified": false,
        "locator": "abstract"
      }
    ],
    "coverage_gaps": [
      "Only one synthetic record screened; not a systematic evidence base."
    ],
    "review_type_claim": "orientation map, not comprehensive review",
    "limitations": [
      "No real search was performed."
    ]
  }
}
```
