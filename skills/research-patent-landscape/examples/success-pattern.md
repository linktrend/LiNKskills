# Fictional worked example

This synthetic example demonstrates task-specific input and output shape only. Names, records, and figures are fictional; it is not a real research result, evaluation, or success receipt. Unavailable evidence and uncomputed quantities remain explicit.

## Input

```json
{
  "invention_or_identifier": "fictional modular sensor interface",
  "purpose": "landscape",
  "jurisdictions": [
    "US"
  ],
  "as_of": "2026-10-05",
  "known_art": [
    "FIC-PAT-1"
  ],
  "public_source_boundary": "user-supplied fictional documents"
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
        "source": "fictional patent index",
        "query": "\"modular sensor interface\"",
        "searched_on": "2026-10-05",
        "result_count": 2
      }
    ],
    "families": [
      {
        "family_id": "FIC-FAM-1",
        "members": [
          "FIC-PAT-1",
          "FIC-PUB-2"
        ],
        "deduplication_basis": "same fictional priority claim",
        "priority_date": "2020-01-01",
        "publication_date": "2021-07-01",
        "grant_date": null,
        "status": "not verified",
        "jurisdiction": "US"
      }
    ],
    "claim_passages": [
      {
        "document": "FIC-PAT-1",
        "claim": "synthetic claim excerpt about a connector",
        "locator": "claim 1",
        "relevance": "shares connector feature; scope comparison not legal conclusion"
      }
    ],
    "coverage": {
      "jurisdictions": [
        "US"
      ],
      "databases": [
        "fictional index"
      ],
      "cutoff": "2026-10-05"
    },
    "unresolved_checks": [
      "Current legal status and ownership not verified."
    ],
    "legal_handoff": "Evidence packet only; Sara/qualified patent counsel evaluates legal significance.",
    "limitations": [
      "Fictional identifiers and excerpt.",
      "No novelty, validity or FTO conclusion."
    ]
  }
}
```
