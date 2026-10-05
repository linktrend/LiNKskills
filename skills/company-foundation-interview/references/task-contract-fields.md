# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `known_fact_source_register`: known fact/source register.
- `authorized_existing_company_records_and_reference_availability`: authorized existing company records and reference availability.
- `ten_interview_module_scope`: ten interview module scope.
- `owner_and_approval_matrix`: owner and approval matrix.

## Completed output sections

- `verified_principal_reported_proposed_conflicting_unknown_fact_register`: verified/Principal-reported/proposed/conflicting/unknown fact register.
- `applicability_and_obligation_questions`: applicability and obligation questions.
- `system_access_role_process_assessment`: system/access/role/process assessment.
- `policy_procedure_form_and_odoo_requirement_inventory`: policy/procedure/form and Odoo requirement inventory.
- `professional_review_and_approval_dependency_plan`: professional review and approval/dependency plan.
- `implementation_acceptance_plan_and_checkpoint`: implementation acceptance plan and checkpoint.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.

## Persisted interview register

The separate fact/decision/answer/artifact/checkpoint record shape is `references/schemas.json#/definitions/interview_register`. The neutral starter is `references/interview/fact-register-template.json`. Every recorded fact, answer and unresolved decision carries its source reference, source date and owner; unknowns carry a follow-up, and conflicting facts/answers identify the other record IDs. Checkpoint metadata contains only an opaque consumer-native reference and item IDs, never raw session contents or facts. Contract fixtures and the offline shape test are under `references/interview/`; passing them proves structure only, not interview quality or runtime persistence.
