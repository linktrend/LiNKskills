# Worked synthetic success example — legal-lawve-litigation-deadline-calendar-dave-marcus

**Task:** golden-task from this skill’s `references/eval-suite.json`.

**Case facts**
- `scheduling_order`: Synthetic signed order dated 2026-09-01: expert reports due 2026-11-10; trial 2027-02-01; service-adjusted response deadline not stated.
- `forum_and_proceeding`: Caption identifies a state trial court; state/local rule source not supplied.
- `service_method`: Unknown; do not calculate derived dates.
- `known_modifications`: Order states no extension; later docket activity not supplied.
- `calendar_preferences`: Draft table only; no attendee invitations.
- `scope_and_as_of`: Synthetic scope only; law applicability unknown unless identified in the case facts.

**Source route:** lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/litigation-deadline-calendar-dave-marcus/SKILL.md

**Worked task output**
Draft date table: expert reports—10 Nov 2026, explicit in the 1 Sep 2026 signed order; trial—1 Feb 2027, explicit in that order. Service-adjusted response deadline is not stated and stays blank. State/local rules, service method and later docket updates are missing; do not calculate a derived date or create an event/invite until checked.

**Method/contract check:** The example follows this skill’s active trigger and procedure in `SKILL.md` and `advanced/advanced.md`; it is bounded by the output contract in `references/schemas.json`. Where a source-selection/applicability note is present, use that route and its stated limits; it does not substitute for current authority. It does not represent an executed native operation.

**Limit:** All case facts are synthetic. No current primary legal text is supplied unless stated in the case; legal applicability and conclusions remain unverified where the example says so. This is a draft demonstration, not legal advice, approval, filing, or external action.
