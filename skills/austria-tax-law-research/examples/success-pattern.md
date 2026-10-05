# Worked synthetic success example — austria-tax-law-research

**Task:** task-specific-golden from this skill’s `references/eval-suite.json`.

**Case facts**
Synthetic. Research a tax question expressly governed by Austrian law. No confirmed jurisdiction/backend or authorized native action interface. Produce only the conditional work product or exact gap report; preserve source/date/uncertainty.

**Source route:** See golden case in references/eval-suite.json.

**Worked task output**
Tax research cannot start at a substantive rule: the fixture names Austria but gives no tax type, taxpayer/entity, transaction, tax year or official authority. Return a research plan with those missing fields and require a current official Austrian tax source with effective date before stating treatment. Do not infer filing duty, rate, deadline or tax position from the jurisdiction label alone.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
