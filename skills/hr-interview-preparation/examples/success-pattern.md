# Fictional task: Customer Support Escalation Analyst interview kit

This worked case demonstrates the interview-preparation task. The task envelope uses the exact input field names and required fields in `references/schemas.json#/definitions/input`; the helper checks only required-field presence/basic types. All candidate and company facts are fictional.

## Input

```json
{
  "task_id": "20261005-0930-HR-000001",
  "request_ref": "synthetic:request-support-analyst-01",
  "source_refs": ["synthetic:approved-role-brief-v1"],
  "data_classification": "synthetic",
  "task_inputs": {
    "role_context": "Customer Support Escalation Analyst, intermediate level; owns investigation and routing of complex product-support cases, not people management.",
    "approved_role_requirements": [
      "Reconstruct an incident timeline from support records.",
      "Separate confirmed facts from customer-reported claims.",
      "Escalate suspected privacy or security incidents promptly through the designated process.",
      "Write a concise customer update that states the next action without promising an unverified fix."
    ],
    "interview_stage": "structured hiring-manager interview",
    "interview_duration_minutes": 60,
    "panel": ["Support Lead", "Privacy Operations Partner"],
    "source_versions": ["synthetic:approved-role-brief-v1"],
    "constraints": ["Use the same core questions for candidates at this stage.", "No candidate-specific evidence supplied."]
  }
}
```

## Draft interview kit

**Role bar source:** synthetic approved-role brief v1, supplied for this example. The four listed requirements are the only approved criteria used. This is a design draft; it does not assess or rank a candidate.

| Competency | Approved requirement | Observable evidence | Interviewer |
|---|---|---|---|
| Timeline reconstruction | Reconstruct incident timeline | Orders events, notes source and time for each, and identifies gaps rather than filling them in | Support Lead |
| Evidence calibration | Separate confirmed facts from reports | Labels customer claims, system observations, and hypotheses separately; asks what would verify a claim | Support Lead |
| Escalation judgment | Escalate suspected privacy/security incidents promptly | Recognizes a trigger, preserves relevant facts, follows the designated route, and avoids independent investigation beyond role | Privacy Operations Partner |
| Customer communication | Give accurate next action without promising an unverified fix | Uses clear language, owns the next update, and distinguishes investigation from resolution | Support Lead |

### Core question bank

Use the same core questions for every candidate. Ask the alternate prompt if the candidate has not encountered the exact situation.

| Competency | Behavioral question | Situational question | Neutral probes |
|---|---|---|---|
| Timeline reconstruction | “Tell us about a complex support issue where the sequence of events was unclear. How did you reconstruct it?” | “A customer reports that a feature failed before an account change, but the available logs show only the account change. What would you record first?” | “Which source established that time?” “What remains uncertain?” |
| Evidence calibration | “Describe a time a customer’s explanation differed from the evidence you could verify. How did you handle the difference?” | “A customer says a colleague accessed their data, but you have no access log yet. How would you describe that in the case?” | “What was confirmed?” “What evidence would change your view?” |
| Escalation judgment | “Tell us about a time you identified a possible privacy or security issue outside your authority to resolve.” | “A support ticket includes an unexpected export of another account’s records. What would you do next?” | “What would you avoid doing?” “Which designated route would you use?” |
| Customer communication | “Give an example of explaining an unresolved technical issue without overpromising.” | “The investigation is ongoing and there is no verified workaround. Draft the next two sentences you would send.” | “What can you commit to?” “When would you update the customer?” |

### 60-minute agenda

| Minutes | Segment | Lead |
|---:|---|---|
| 0–5 | Introductions, role scope, and interview format | Support Lead |
| 5–17 | Timeline reconstruction | Support Lead |
| 17–29 | Evidence calibration | Support Lead |
| 29–43 | Escalation judgment | Privacy Operations Partner |
| 43–53 | Customer communication | Support Lead |
| 53–58 | Candidate questions | Both |
| 58–60 | Close and explain next steps | Support Lead |

### Anchored scorecard

Score each competency only from the evidence elicited by its question. `Not assessed` is separate from the 1–4 scale.

| Score | Anchor for this role |
|---:|---|
| 1 | Elicited evidence demonstrates a material gap: confuses a reported claim with verified fact or proposes acting outside escalation authority. Absence of elicited evidence is not assessed, not a score of 1. |
| 2 | Partial evidence: identifies some sources or next steps but needs material prompting to preserve uncertainty or route correctly. |
| 3 | Meets the stated requirement: gives a specific, ordered method, accurate fact labels, appropriate escalation, or a bounded customer update. |
| 4 | Strong evidence beyond the stated bar: independently applies a repeatable method, explains trade-offs, and prevents unsupported conclusions while keeping the case moving. |
| Not assessed | No usable evidence was elicited, the question was skipped, or the interview ran out of time. Do not convert to zero. |

| Competency | Score / not assessed | Evidence and question ID | Follow-up evidence needed |
|---|---|---|---|
| Timeline reconstruction |  |  |  |
| Evidence calibration |  |  |  |
| Escalation judgment |  |  |  |
| Customer communication |  |  |  |

### Debrief and limits

Interviewers complete scores independently, then compare concrete examples against the four approved requirements. Record disagreement and missing evidence; do not average impressions or turn a score into an automatic hiring decision. No candidate evidence was supplied, so candidate assessment, accommodation handling, and hiring outcome are not assessed. The hiring decision owner is not specified in the fixture and must be confirmed by the role owner.
