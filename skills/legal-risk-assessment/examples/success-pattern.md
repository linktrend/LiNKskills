# Worked synthetic success example — legal-risk-assessment

**Task:** task-specific-golden from this skill’s `references/eval-suite.json`.

**Case facts**
Synthetic vendor-data exposure risk: logs show 2 test records accessed by an unknown service account; containment is confirmed but completeness of access logs is unknown; no company scoring rubric, jurisdiction, or legal notice rule is supplied. Prepare an unrated or explicitly qualitative risk memo with evidence, plausible impact/likelihood uncertainty, mitigation options, owners, and precise legal questions.

**Source route:** See golden case in references/eval-suite.json.

**Worked task output**
Qualitative, unrated memo: confirmed from the fixture: two test records were accessed by an unknown service account and containment is reported complete. Unknown: whether logs cover all access, whether other records were affected, jurisdiction, notice rule and company scoring method. Residual risk cannot be scored; preserve logs and access identity, validate containment scope, and assign an owner to establish log completeness. Counsel question: which affected-person and jurisdiction facts are needed before any notice-duty analysis? No notice sent.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
