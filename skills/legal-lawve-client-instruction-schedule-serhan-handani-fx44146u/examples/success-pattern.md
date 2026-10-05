# Worked synthetic success example — legal-lawve-client-instruction-schedule-serhan-handani-fx44146u

**Task:** golden-task from this skill’s `references/eval-suite.json`.

**Case facts**
- `matter_and_forum`: Synthetic Smith v North Ltd; forum and counsel owner not established.
- `case_file_refs`: Pleadings and 3 letters supplied; letter refers to missing Exhibit 7; two witness notes disagree on delivery date.
- `issues_and_opponent_positions`: Delivery on 4 May vs 9 May; opponent asserts 4 May.
- `client_accessibility`: Client reports dyslexia; supervising solicitor suitability decision not supplied.
- `output_format`: Accessible issue-by-issue table and one-page cover-note draft.
- `scope_and_as_of`: Synthetic scope only; law applicability unknown unless identified in the case facts.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/client-instruction-schedule-serhan-handani-fx44146u/SKILL.md

**Worked task output**
Draft issue schedule: Issue 1—delivery date: witness notes conflict (4 May vs 9 May); opposing party asserts 4 May; preserve all three as attributed statements. Issue 2—Exhibit 7 is referenced but missing. Client reports dyslexia; do not draft/send a leading question until supervising solicitor assesses suitability and witness-use risk. Request forum/counsel owner and missing exhibit. Accessible table/cover note can be drafted after that review; nothing is sent.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
