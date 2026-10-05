# Fictional worked example

This synthetic example demonstrates task-specific input and output shape only. Names, records, and figures are fictional; it is not a real research result, evaluation, or success receipt. Unavailable evidence and uncomputed quantities remain explicit.

## Input

```json
{
  "syllabus_or_objectives": "fictional course objective: explain experimental design",
  "learner_level": "intermediate",
  "language": "English",
  "recency_balance": "foundational plus current",
  "topic_constraints": [
    "randomization",
    "measurement"
  ],
  "time_budget": "4 weeks"
}
```

## Output

```json
{
  "schema_ref": "references/schemas.json#/definitions/output",
  "status": "fictional_example_not_evaluation_or_receipt",
  "example": {
    "status": "partial",
    "topic_outcome_map": [
      {
        "outcome": "Explain randomization",
        "week": 1,
        "assessment": "draw allocation scheme"
      }
    ],
    "readings": [
      {
        "source_id": "FIC-READ-1",
        "citation": "Fictional reading placeholder; not a real citation",
        "link": null,
        "topic": "randomization",
        "level": "intermediate",
        "summary": "Use this slot for a verified foundational reading.",
        "access": "not checked",
        "citation_verified": false
      }
    ],
    "sequence_rationale": "Start with design vocabulary, then measurement and application.",
    "discussion_and_application_prompts": [
      "What allocation mechanism prevents predictable assignment?"
    ],
    "evidence_and_access_gaps": [
      "No real syllabus or verified citations supplied."
    ]
  }
}
```
