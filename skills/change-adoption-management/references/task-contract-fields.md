# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `approved_change_and_sponsor`: approved change and sponsor.
- `affected_agent_human_roles`: affected agent/human roles.
- `readiness_communication_and_adoption_evidence`: readiness, communication and adoption evidence.

## Completed output sections

- `stakeholder_readiness_assessment`: stakeholder/readiness assessment.
- `adoption_and_training_plan`: adoption and training plan.
- `measured_effectiveness_review`: measured effectiveness review.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
