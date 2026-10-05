# Worked synthetic success example — legal-lawve-qcm-generateur-christophe-quezel-ambrunaz

**Task:** golden-task from this skill’s `references/eval-suite.json`.

**Case facts**
- `subject_and_objective`: Synthetic introductory course: distinguish evidence, inference and assumption in legal analysis.
- `learner_level`: Undergraduate year 1; prior knowledge introductory.
- `assessment_mode`: Formative/evaluative with explanatory feedback; single answer.
- `question_count_and_scoring`: 6 questions, 4 options each; no negative marking.
- `source_materials`: Instructor-provided 2-page handout, synthetic and dated 2026-09-01.
- `export_target`: Structured preview table; no platform write.
- `scope_and_as_of`: Synthetic scope only; law applicability unknown unless identified in the case facts.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/qcm-generateur-christophe-quezel-ambrunaz/SKILL.md

**Worked task output**
Six-item preview; one answer per item, four choices, no negative marking. The premises below are fictional and self-contained; check alignment to the supplied handout before use.

| # | Item | Choices | Key and rationale |
|---|---|---|---|
| 1 | A dated access log records three failed logins. | A Evidence · B Inference · C Assumption · D Recommendation | **A.** The log directly records the observed events; it does not identify a cause. |
| 2 | “The log stopped at 17:00, so nobody accessed the system later.” | A Evidence · B Inference · C Assumption · D Recommendation | **B.** This conclusion goes beyond the recorded period. |
| 3 | The analyst writes, “Assume the archive covers the full week,” because no coverage note is supplied. | A Evidence · B Inference · C Assumption · D Finding | **C.** Coverage is explicitly posited, not established. |
| 4 | The signed policy excerpt states, “Reviews occur monthly.” | A Evidence · B Inference · C Assumption · D Recommendation | **A.** This is a statement in a supplied source; authenticity/currentness can still be checked. |
| 5 | “The new control probably caused the lower error count,” based only on before/after totals. | A Evidence · B Inference · C Assumption · D Definition | **B.** Causation is inferred; other explanations have not been tested. |
| 6 | “The reviewer will approve the exception,” although no reviewer or decision is identified. | A Evidence · B Inference · C Assumption · D Verified decision | **C.** It presumes a future decision without evidence. |

Instructor check: the key tests the stated evidence/inference/assumption objective, not current French law. The two-page handout’s alignment remains to be verified. No platform export.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
