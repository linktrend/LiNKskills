# Fictional worked example

This synthetic example demonstrates task-specific input and output shape only. Names, records, and figures are fictional; it is not a real research result, evaluation, or success receipt. Unavailable evidence and uncomputed quantities remain explicit.

## Input

```json
{
  "clinical_question": "Does intervention X improve outcome Y?",
  "population": "fictional adults meeting criterion P",
  "intervention": "X",
  "comparator": "usual care",
  "design_stage": "concept",
  "endpoints": {
    "primary": "Y at week 12",
    "secondary": [
      "safety events"
    ]
  },
  "follow_up": "12 weeks",
  "expected_event_or_variance_assumptions": null,
  "recruitment_sites": "unknown",
  "regulatory_ethics_context": "jurisdiction not specified",
  "clinical_owner": "named owner required",
  "biostatistician": "named owner required"
}
```

## Output

```json
{
  "schema_ref": "references/schemas.json#/definitions/output",
  "status": "fictional_example_not_evaluation_or_receipt",
  "example": {
    "status": "partial",
    "design_options": [
      {
        "design": "parallel randomized comparison",
        "rationale": "aligns with a comparative intervention question",
        "unresolved": "feasibility and ethical acceptability need owner review"
      }
    ],
    "population_and_allocation": {
      "eligibility": "criterion P needs clinical definition",
      "randomization": "proposed; allocation method not specified",
      "masking": "not specified"
    },
    "endpoint_hierarchy": {
      "primary": "Y at week 12",
      "secondary": [
        "safety events"
      ],
      "estimand": "not fully specified"
    },
    "sample_size_power": {
      "status": "not_computed",
      "reason": "event rate/variance, target effect, alpha, power and attrition assumptions absent",
      "assumptions": []
    },
    "feasibility_sensitivity": [
      "Recruitment rate, sites and follow-up burden unknown."
    ],
    "protocol_synopsis_outline": [
      "Question",
      "population",
      "intervention/comparator",
      "endpoints",
      "analysis plan",
      "safety monitoring",
      "ethics"
    ],
    "owner_review": {
      "clinical_owner": "required before use",
      "biostatistician": "required before use",
      "ethics_regulatory": "jurisdiction-specific review required"
    },
    "limitations": [
      "Illustrative design scaffold only; not protocol or medical advice."
    ]
  }
}
```
