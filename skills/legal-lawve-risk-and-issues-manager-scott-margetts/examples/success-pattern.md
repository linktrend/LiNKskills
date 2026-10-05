# Worked synthetic success example — legal-lawve-risk-and-issues-manager-scott-margetts

**Task:** golden-task from this skill’s `references/eval-suite.json`.

**Case facts**
- `mode_and_goal`: Extract decisions and create draft RAID updates from synthetic meeting notes.
- `source_records`: Note says “we should probably use Vendor A”; later note says “Vendor A starts Monday”; no approval record.
- `objectives_and_scope`: Project launch target 1 December; approved scope baseline not attached.
- `owners_and_dates`: No item owners; deadline for Vendor A onboarding mentioned as 1 November.
- `output_destination`: Draft table in response; no system update.
- `scope_and_as_of`: Synthetic scope only; law applicability unknown unless identified in the case facts.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/risk-and-issues-manager-scott-margetts/SKILL.md

**Worked task output**
Draft RAID entries: (D-1, proposed decision) “use Vendor A” is tentative; later “Vendor A starts Monday” may imply a decision but has no approval record—owner/decider unresolved. (R-1) onboarding may proceed before approval; likelihood/status not supplied. (A-1) launch target is 1 December; scope baseline missing. (I-1) no item owners assigned. Preserve 1 November onboarding date as a note, not verified status. Ask who decided and obtain scope baseline; no register update.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
