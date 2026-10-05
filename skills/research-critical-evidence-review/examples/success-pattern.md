# Fictional worked example

This synthetic example demonstrates task-specific input and output shape only. Names, records, and figures are fictional; it is not a real research result, evaluation, or success receipt. Unavailable evidence and uncomputed quantities remain explicit.

## Input

```json
{
  "claim": "A fictional intervention improves outcome Y.",
  "decision": "whether evidence supports further study",
  "population": "fictional population P",
  "comparator": "usual care",
  "outcome": "Y at 12 weeks",
  "study_refs": [
    "FIC-TRIAL-1"
  ],
  "design_details": "parallel randomized design; synthetic summary only",
  "measurement": "Y units not supplied",
  "analysis": "results not supplied",
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
    "claim_evidence_matrix": [
      {
        "claim": "intervention improves Y",
        "source_id": "FIC-TRIAL-1",
        "estimate": null,
        "unit": "not supplied",
        "direction": "not assessable",
        "supports": "unknown",
        "contradicts": "unknown"
      }
    ],
    "design_appraisal": {
      "design": "parallel randomized (fictional description)",
      "allocation": "not verifiable",
      "masking": "not supplied",
      "follow_up": "not supplied",
      "analysis_population": "not supplied"
    },
    "bias_and_validity": {
      "selection": "unclear",
      "measurement": "unclear",
      "missing_outcome": "unknown",
      "confounding": "risk reduced only if randomization implemented; implementation unverified",
      "selective_reporting": "unknown"
    },
    "uncertainty_and_alternatives": [
      "No outcome estimate or denominator supplied."
    ],
    "conclusion": "insufficient information to determine whether the claim is supported.",
    "evidence_gaps": [
      "Full report, protocol, outcome data and analysis plan."
    ],
    "causal_limits": "No causal conclusion from a design label alone."
  }
}
```
