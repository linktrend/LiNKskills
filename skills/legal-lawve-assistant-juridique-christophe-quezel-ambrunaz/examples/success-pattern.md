# Worked synthetic success example — legal-lawve-assistant-juridique-christophe-quezel-ambrunaz

**Task:** synthetic-golden from this skill’s `references/eval-suite.json`.

**Case facts**
- `research_question`: Does a French merchant owe a pre-contract information duty for a subscription renewal term?
- `facts_and_purpose`: Synthetic merchant sells online in France; contract, renewal notice and consumer status not supplied.
- `jurisdiction_scope`: France; possible EU consumer overlay to verify.
- `as_of_and_recency`: Current law as of 2026-10-05.
- `available_sources`: Only a synthetic question; no official source retrieved.
- `scope_and_as_of`: Synthetic facts only; current law/applicability unverified unless explicitly supplied.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/assistant-juridique-christophe-quezel-ambrunaz/SKILL.md

**Worked task output**
Research status: substantive rule unresolved. The synthetic question is whether a French online merchant owes pre-contract information about subscription renewal; the contract, consumer status, renewal mechanism and notice are absent, and no official primary text was retrieved. Research plan: identify merchant/consumer status; inspect the renewal flow and notices; retrieve current official French and relevant EU primary sources; record text, effective date and pinpoint before applying. Do not guess an article number or state a rule.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
