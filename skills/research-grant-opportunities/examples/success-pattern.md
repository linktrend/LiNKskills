# Fictional worked example

This synthetic example demonstrates task-specific input and output shape only. Names, records, and figures are fictional; it is not a real research result, evaluation, or success receipt. Unavailable evidence and uncomputed quantities remain explicit.

## Input

```json
{
  "project_summary": "fictional early-stage sensor research",
  "applicant_stage": "early career",
  "institution": "fictional university",
  "geography": "US",
  "funder_scope": "NIH",
  "project_maturity": "preliminary concept",
  "preliminary_evidence": "none supplied",
  "budget_scope": "planning estimate absent",
  "submission_timing": "next cycle unknown",
  "named_opportunity": null
}
```

## Output

```json
{
  "schema_ref": "references/schemas.json#/definitions/output",
  "status": "fictional_example_not_evaluation_or_receipt",
  "example": {
    "status": "partial",
    "opportunity_table": [
      {
        "opportunity_id": "FIC-NIH-FOA-1",
        "official_source": "fictional notice placeholder",
        "source_checked_on": "not checked",
        "eligibility": "unknown",
        "mechanism": "unknown",
        "scope_fit": "cannot assess without aims",
        "deadline": "not verified",
        "budget_period": "not verified",
        "fit_evidence": "project summary only",
        "open_questions": [
          "Institution eligibility",
          "current notice and deadline"
        ]
      }
    ],
    "nih_evidence": {
      "institute": "not verified",
      "study_section": "not verified",
      "reporter_comparison": "not performed",
      "nosi": "not checked"
    },
    "proposal_evidence_outline": [
      "Specific aims evidence needed",
      "preliminary-data gap",
      "milestone/feasibility plan"
    ],
    "next_steps": [
      "Check current official opportunity notice and institutional eligibility."
    ],
    "limitations": [
      "No live funder source was checked.",
      "No universal NIH rule applied to non-NIH sources."
    ]
  }
}
```
