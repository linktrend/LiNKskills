# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `observed_process_and_responsible_roles`: observed process and responsible roles.
- `trigger_prerequisites_and_intended_reader`: trigger, prerequisites and intended reader.
- `approval_exception_rules`: approval/exception rules.
- `acceptance_evidence`: acceptance evidence.

## Completed output sections

- `controlled_sop_draft`: controlled SOP draft.
- `execution_checklist`: execution checklist.
- `walkthrough_and_revision_record`: walkthrough and revision record.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
