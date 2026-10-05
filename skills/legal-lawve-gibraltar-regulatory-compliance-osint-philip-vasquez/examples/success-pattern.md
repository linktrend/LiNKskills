# Worked synthetic success example — legal-lawve-gibraltar-regulatory-compliance-osint-philip-vasquez

**Task:** golden-task from this skill’s `references/eval-suite.json`.

**Case facts**
- `issue_and_decision`: Synthetic question whether Gibraltar limitation period affects a commercial claim.
- `gibraltar_connection`: Parties and performance are in England; contract has no Gibraltar clause or activity.
- `candidate_regimes`: Requester mentions Gibraltar without supporting documents.
- `primary_sources`: No Gibraltar legislation or court source attached.
- `comparison_request`: No England/Gibraltar comparison requested.
- `scope_and_as_of`: Synthetic scope only; law applicability unknown unless identified in the case facts.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/gibraltar-regulatory-compliance-osint-philip-vasquez/SKILL.md

**Worked task output**
Jurisdiction screen: stated parties/performance are in England and the contract has no Gibraltar clause/activity; requester’s Gibraltar reference alone does not establish a connection. Do not apply Gibraltar law or silently substitute English/UK rules. Ask for forum, contract, entity or conduct facts that may connect the claim to Gibraltar, then retrieve current Gibraltar primary sources and record retrieval date. Current limitation analysis remains unresolved.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
