# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `approved_facts_and_intended_message`: approved facts and intended message.
- `audiences_and_channels`: audiences and channels.
- `decision_owner_confidentiality_and_timing`: decision owner, confidentiality and timing.

## Completed output sections

- `message_drafts`: message drafts.
- `sequencing_and_faq`: sequencing and FAQ.
- `review_delivery_plan`: review/delivery plan.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
