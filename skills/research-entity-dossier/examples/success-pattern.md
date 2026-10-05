# Fictional worked example

This synthetic example demonstrates task-specific input and output shape only. Names, records, and figures are fictional; it is not a real research result, evaluation, or success receipt. Unavailable evidence and uncomputed quantities remain explicit.

## Input

```json
{
  "entity_name": "Fictional Example Labs",
  "identifier": "fictional-registry-id-001",
  "hypothesis": "The organization launched product Z in 2024.",
  "purpose": "meeting preparation",
  "period": "2023-01-01/2025-12-31",
  "public_source_boundary": "public records supplied by user",
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
    "identity": {
      "name": "Fictional Example Labs",
      "identifier": "fictional-registry-id-001",
      "jurisdiction": "not supplied",
      "disambiguation": "synthetic fixture"
    },
    "timeline": [
      {
        "date": "2024-06",
        "event": "product Z announcement",
        "source_id": "FIC-PRESS-1",
        "source_date": "2024-06-01",
        "quality": "unverified synthetic source"
      }
    ],
    "hypothesis_evidence": {
      "supports": [
        {
          "claim": "announcement exists in fixture",
          "source_id": "FIC-PRESS-1"
        }
      ],
      "against": [],
      "assessment": "not independently verified"
    },
    "ownership_product_funding": {
      "ownership": "not supplied",
      "product": "announcement only",
      "funding": "not supplied"
    },
    "source_quality_and_recency": [
      {
        "source_id": "FIC-PRESS-1",
        "type": "company statement",
        "independent_confirmation": "none"
      }
    ],
    "unresolved_questions": [
      "Did product Z ship or reach customers?"
    ],
    "citation_audit": {
      "links_opened": false,
      "citation_completeness": "fixture only"
    }
  }
}
```
