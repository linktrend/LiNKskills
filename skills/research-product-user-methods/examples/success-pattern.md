# Fictional worked example

This synthetic example demonstrates task-specific input and output shape only. Names, records, and figures are fictional; it is not a real research result, evaluation, or success receipt. Unavailable evidence and uncomputed quantities remain explicit.

## Input

```json
{
  "decision_goal": "identify onboarding friction in a prototype",
  "product_stage": "prototype",
  "target_users": "new administrators",
  "segments": [
    "first-time",
    "experienced"
  ],
  "known_risks": [
    "recruiting only advocates"
  ],
  "available_evidence": "no sessions supplied",
  "access_and_consent": "consent process required"
}
```

## Output

```json
{
  "schema_ref": "references/schemas.json#/definitions/output",
  "status": "fictional_example_not_evaluation_or_receipt",
  "example": {
    "status": "complete",
    "method_rationale": "moderated task-based usability sessions can locate friction; exploratory, not prevalence estimation",
    "study_plan": {
      "tasks": [
        "Create first workspace",
        "Invite a teammate"
      ],
      "moderator_script": "Ask participant to think aloud; do not lead.",
      "recording": "only with explicit consent"
    },
    "participant_criteria": {
      "target": "new administrators",
      "exclude": "team members who built prototype",
      "recruitment": "varied experience; selection limitations documented"
    },
    "sample_and_saturation": {
      "target_sessions": 5,
      "basis": "small formative round to discover issues, not statistical saturation claim",
      "stop_rule": "review after five and decide whether new themes continue"
    },
    "coded_observations": [
      {
        "participant": "P1 synthetic",
        "task": "create workspace",
        "observation": "looked for save confirmation",
        "evidence": "fictional note",
        "code": "feedback_visibility"
      }
    ],
    "candidate_insights": [
      {
        "insight": "confirmation feedback may be unclear",
        "recurrence": "1/1 synthetic participant",
        "limitation": "single fictional observation; hypothesis only"
      }
    ],
    "consent_privacy": [
      "Obtain consent; minimize personal data; allow withdrawal."
    ],
    "limitations": [
      "No real participant sessions conducted."
    ]
  }
}
```
