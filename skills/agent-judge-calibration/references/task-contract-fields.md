# Named task contracts

The task input and completed output fields below are mandatory in `references/schemas.json`. Each input carries a summary, evidence references and one of verified, Principal-reported, proposed, conflicting or unknown. Unknown evidence is allowed as an explicit gap; it is not permission to fabricate. Each completed output section carries a substantive summary, evidence references and any named artifact references.

## Inputs

- `one_property_rubric_dimensions_and_anchored_scales`: one-property rubric dimensions and anchored scales.
- `authorized_held_out_human_labeled_examples_and_disagreement_evidence`: authorized held-out human-labeled examples and disagreement evidence.
- `direct_pairwise_objective_and_observed_judgments`: direct/pairwise objective and observed judgments.
- `candidate_ids_and_swapped_position_mapping`: candidate IDs and swapped-position mapping.
- `budget_and_execution_authority`: budget and execution authority.

## Completed output sections

- `anchored_evidence_first_grader_specification`: anchored evidence-first grader specification.
- `held_out_calibration_and_disagreement_analysis`: held-out calibration and disagreement analysis.
- `position_consistent_pairwise_results_or_tie`: position-consistent pairwise results or TIE.
- `per_criterion_scores_uncertainty_and_limitations`: per-criterion scores, uncertainty and limitations.
- `judge_version_drift_and_review_plan`: judge version/drift and review plan.

NEEDS_CONTEXT, REFUSED, FAILED and PENDING_APPROVAL may return only completed sections. A schema shape pass does not establish mathematical, legal or factual correctness; those require the task method and meaningful evaluation.
