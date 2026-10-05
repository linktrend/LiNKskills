# Worked synthetic success example — legal-lawve-icelandic-contract-review-magnus-smarason

**Task:** golden-task from this skill’s `references/eval-suite.json`.

**Case facts**
- `contract_and_version`: Synthetic services agreement v4 plus unsigned schedule; amendment referenced but missing.
- `parties_and_transaction`: Icelandic software supplier and foreign buyer; service delivered remotely.
- `governing_law_and_forum`: Agreement clause states Icelandic law; forum clause blank.
- `business_objectives`: Buyer wants termination flexibility and data export; no approved fallback.
- `primary_authority_snapshot`: No current Icelandic primary authority supplied.
- `scope_and_as_of`: Synthetic scope only; law applicability unknown unless identified in the case facts.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/icelandic-contract-review-magnus-smarason/SKILL.md

**Worked task output**
Contract review issues: v4 services agreement states Icelandic governing law; forum clause is blank. Unsigned schedule and referenced amendment are missing. Buyer priorities are termination flexibility and data export, but no approved fallback exists. Draft negotiation questions for termination notice/transition and export format/cost, mark any clause text as proposed, and request missing documents. Do not state Icelandic legal rules without current local primary authority or treat preferences as approved positions.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
