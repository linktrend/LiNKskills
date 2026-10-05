# Worked synthetic success example — legal-lawve-mandatory-verification-larissa-meredith-flister

**Task:** synthetic-golden from this skill’s `references/eval-suite.json`.

**Case facts**
- `propositions`: “The employer must notify every employee within 24 hours under Article 9.”
- `citations`: Draft cites “Data Protection Regulation, Art. 9,” no jurisdiction or regulation number.
- `jurisdiction_and_date`: Unspecified jurisdiction; requested as of 2026-10-05.
- `primary_source_access`: No official authority source supplied or retrieved.
- `document_context`: Synthetic internal draft; legal citation style not specified.
- `scope_and_as_of`: Synthetic facts only; current law/applicability unverified unless explicitly supplied.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/mandatory-verification-larissa-meredith-flister/SKILL.md

**Worked task output**
Verification result: NOT VERIFIED. “Data Protection Regulation, Art. 9” is ambiguous without jurisdiction/regulation identity, and the 24-hour employer-notice proposition has no supporting official source. Do not guess which Article 9 or validate the claim from its title. Request the governing jurisdiction, instrument number, facts triggering notice and official text; then check each proposition and effective date independently.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
