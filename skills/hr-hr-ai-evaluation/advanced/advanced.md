# HR AI Vendor Evaluation: task method and acceptance

## Trigger and task edge

Use when comparing or evaluating an AI product/vendor for a specified HR use case before procurement or deployment.

The single-task result is: Evidence-based vendor comparison matrix. Separate adjacent work stays routed to its own task.

## Required evidence

- Use case, intended users, workflow and affected population
- Vendor/product documentation, model/version, data flow and contractual facts
- Owner-supplied acceptance criteria, security/privacy requirements and available test set
- Procurement, privacy, security, legal and HR decision owners

## Procedure and branch notes

1. Define one HR use case and the exact task the product would support. Identify affected users/candidates/employees and whether the output affects consequential employment decisions.
2. Collect dated vendor/product evidence: model/version, input/output, data retention and training use, subprocessors, controls, security, accessibility, human override, audit logs and contract terms. Mark claims not independently verified.
3. Build a comparison using owner-supplied criteria. Include task accuracy, false positives/negatives, subgroup/error analysis where lawful and adequately sampled, privacy/security, accessibility, integration burden, explanation and fallback.
4. Design a representative, consent/permission-appropriate test set. Separate development and holdout cases, specify labels and adjudication, and report denominators and confidence limits. Do not use real sensitive HR records unless specifically authorized and privacy-controlled.
5. Evaluate output quality and failure severity per use case. A high aggregate score does not establish safe performance for subgroups or unusual cases. Record missing coverage and adversarial cases.
6. Compare vendors and a non-AI/manual alternative. Recommend no-go, limited pilot questions or next evidence; do not procure, deploy, configure, or claim legal compliance.
7. Deliver findings and exact approvals/evidence still needed for security, privacy, HR policy, procurement and counsel.

## Acceptance checks

- Every material input and rule has an evidence reference or is labeled an assumption/open question.
- Calculations show formula, denominator, units, population and source date; arithmetic is independently rechecked.
- Findings distinguish observed facts, attributed statements, hypotheses, assumptions and owner decisions.
- Missing evidence blocks only the conclusion that depends on it; complete unaffected sections.
- Personal data is minimized and any small-group disclosure is suppressed under the supplied privacy rule.
- Drafts contain no unsupported legal, company-policy, approval, employment or fairness conclusion.
- No external effect, message, system mutation, filing, signature or business decision occurs.

## Jurisdiction, evidence and escalation

Do not assume a jurisdiction, entity, employment classification, policy, reporting standard or legal duty. For current law, verify official primary authorities for the actual location/date and route interpretation to qualified counsel. Treat secondary articles and source examples as research leads only. Preserve date, record ID, source scope and contradictory evidence. Escalate only material safety, legal, retaliation, privacy or decision-right issues; routine drafts continue within scope.

## Source base and integrated methods

**Source selection and active integration.** Tuanductran HR AI-evaluation source is the base; retain vendor comparison, fit-for-purpose testing and bias/privacy criteria. HR AI governance is a separate lifecycle/policy task; this evaluation does not authorize procurement or deployment. The named source originals are preserved under `references/upstream/`; see `references/source-selection.md` for pinned source identity, merge decision and exclusions.

Exact pinned repositories, commits, source trees, hashes, licensing notices and copy paths are recorded in `references/upstream/SOURCE-MANIFEST.json`. Source permissions do not confer consumer authority, and source scripts were not executed.
