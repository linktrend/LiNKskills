# Skill Quality Evaluation

## Task purpose and boundary

Evaluate whether a specified skill release reliably triggers and completes its intended task, using a frozen case set and supplied results or an already-authorized evaluator interface. This is a catalog-quality assessment artifact, owned by the Librarian/Skill Library. It does not perform skill creation, reverse engineering, architecture, admission, qualification, publication, activation, or runtime release action. The root `skill-architect` remains the authoritative pack-authoring workflow.

## Evaluation procedure

1. **Pin the candidate and intended behavior.** Record exact skill ID, immutable version/hash, trigger, user task, supported input contract, output contract, runtime/profile, and explicit scope-out behaviors. State the intended user outcome in observable terms. Missing release identity means return `needs_context`; do not evaluate a mutable folder as if it were immutable.
2. **Build a balanced suite.** Cover ordinary tasks, likely variations, boundary/underspecified inputs, known regressions, and adversarial inputs. Include task distribution and sampling rationale. Each case has a stable ID, frozen input/context, expected observable assertions, hard failures, evidence source, and whether judgment is deterministic or qualitative. Do not tune a rubric on final holdout cases.
3. **Separate measures.** Measure trigger precision/recall only with a defined sample of in-scope and out-of-scope requests; report the confusion matrix and sample denominator. Score task output against atomic assertions. Assess completeness, correctness, evidence grounding, tool/authority behavior, and abstention separately. Keep qualitative reviewer notes distinct from deterministic assertions. A raw preference winner is not evidence of objective correctness.
4. **Choose comparison design.** Compare baseline and candidate on the same frozen cases, same context, and same runtime settings when feasible. If only one version is available, report absolute performance and limitations rather than a causal improvement claim. When testing a description/trigger change, measure trigger behavior with matched prompts and separately verify task performance on prompts that invoke the skill. Preserve version identities; do not blend outputs from different runs.
5. **Score and inspect errors.** Compute per-case outcomes before aggregates. Report denominators, unrun cases and missing observations. Analyze error categories, severity, disagreement, confidence and sampling limits. Report exact failure examples by opaque case ID and minimized evidence. Never copy raw sensitive documents, secrets, or hidden reasoning into evaluation telemetry.
6. **Recommend revisions.** Link each recommendation to observed failure and relevant skill fragment. Distinguish demonstrated defect from hypothesis; propose smallest testable edit and regression coverage. Re-run only when an existing owner-approved harness is available and authorization, scope, isolation, and cost are already supplied. This pack makes no paid model call and does not call copied helper scripts.
7. **Deliver evidence packet.** Include candidate identity, task/trigger definition, suite hash, case-level results, rubric and evaluator identity, comparison conditions, arithmetic, unresolved disagreement, limitation, and recommendations. State explicitly `not qualified` unless a separate owner process has accepted evidence.

## Decision outcomes

- `no_claim`: results do not support a comparative claim or evaluation was descriptive only.
- `hold`: a hard failure, missing provenance, scope violation, or unresolved validity issue makes the candidate unsuitable for downstream review.
- `candidate_for_independent_review`: evidence is sufficiently complete for a different qualified owner to inspect; this does not qualify, admit, publish or activate the skill.

## Same-task comparison

- `skill-architect` is complementary: it authors/migrates/refines a pack and checks structure; this task measures behavior across frozen cases and versions.
- `agent-workforce-evaluation` is adjacent but distinct: it evaluates agent/workflow runs; this task evaluates a skill release's trigger, procedure, outputs and regression behavior. The same frozen case/run evidence may be referenced, but task contracts and owner outcomes are separate.
- Upstream source's repeated loop, analyzer/comparator/grader decomposition, benchmark aggregation and description trigger measurement informed this method. Original UI/scripts are retained unchanged and are not callable dependencies.

## Tool boundary

Use current native `read` for supplied artifacts and native `write`/`edit` only for a requested internal plan or report. Do not call upstream Python scripts, interactive HTML viewers, paid model APIs, benchmark runners, or catalog/provider tools. `get_tool_details` means inspect current visible schema and owner toolcard, not call an alias. Consumer checkpoint state remains SQLite/native-owner controlled; do not use JSONL as runtime state.
