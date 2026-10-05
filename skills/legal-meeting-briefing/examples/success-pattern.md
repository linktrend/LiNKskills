# Worked synthetic success example — legal-meeting-briefing

**Task:** task-specific-golden from this skill’s `references/eval-suite.json`.

**Case facts**
Synthetic board compliance meeting, 30 minutes: supplied agenda includes approve draft policy, review two overdue obligations, and discuss vendor contract; source notes conflict on one due date and list no owner for the second obligation. Produce timeboxed brief, evidence and open question, two actions with unresolved fields, no circulation.

**Source route:** See golden case in references/eval-suite.json.

**Worked task output**
30-minute draft agenda: 0–5 confirm decisions and scope; 5–13 review overdue obligation A (due date disputed; preserve both source dates); 13–20 review overdue obligation B (owner not supplied); 20–27 discuss vendor contract; 27–30 record decisions and next steps. Decision/action register: policy approval is a decision item, not approved yet; obligation A needs source/date reconciliation; obligation B needs an owner; contract discussion has no stated decision request. Draft only; no circulation or tracker update.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
