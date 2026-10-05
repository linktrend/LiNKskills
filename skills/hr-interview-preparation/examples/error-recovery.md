# Fictional recovery: interview request missing timing and panel

This case demonstrates partial interview preparation plus a precise intake gap. The input field names follow `references/schemas.json#/definitions/input`; `task_inputs.interview_duration_minutes` and `task_inputs.panel` are required by that schema.

## Input

```json
{
  "task_id": "20261005-0930-HR-000002",
  "request_ref": "synthetic:request-oncall-engineer-02",
  "source_refs": ["synthetic:approved-oncall-role-brief-v2"],
  "data_classification": "synthetic",
  "task_inputs": {
    "role_context": "On-call Reliability Engineer, intermediate level.",
    "approved_role_requirements": [
      "Use monitoring evidence to scope an incident.",
      "Communicate a reversible mitigation and its risks.",
      "Produce a clear handoff for the next on-call engineer."
    ],
    "interview_stage": "technical interview",
    "constraints": ["No candidate evidence supplied."]
  }
}
```

The HR helper reports `NEEDS_CONTEXT` with missing paths `task_inputs.interview_duration_minutes` and `task_inputs.panel`. It reports field names only and does not echo the input values. The schema remains the authoritative full contract.

## Work completed from available facts

| Competency | Approved requirement | Draft evidence question | Neutral probe |
|---|---|---|---|
| Incident scoping | Use monitoring evidence to scope an incident | “Describe an incident where the initial alert did not show the full impact. How did you determine scope?” | “Which signal changed your assessment?” |
| Mitigation judgment | Communicate a reversible mitigation and risks | “Tell us about a mitigation you proposed under uncertainty. What made it reversible?” | “What was the rollback signal?” |
| Handoff quality | Produce a clear on-call handoff | “Give an example of a handoff that let another engineer continue without repeating your investigation.” | “What remained unknown at handoff?” |

These are draft core questions linked to the approved requirements. A timed agenda, panel ownership, and final question selection remain provisional because the available evidence does not provide the interview duration or interviewers. Do not invent a 30/45/60-minute schedule or assign an interviewer by role title.

## Questions to finish the kit

1. How many minutes are available for this stage, including candidate questions and close?
2. Which interviewers will attend, and who owns the hiring decision?

Once supplied, allocate the three competencies to the panel, set a realistic agenda, and complete the anchored scorecard/debrief. No candidate is evaluated in this example.
