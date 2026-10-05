# Synthetic example

This fictional fixture illustrates structure only; it contains no actual client/company facts or current legal authority.

```json
{
  "task_id": "20261004-1200-LEGAL-000001",
  "request_ref": "synthetic-case-001",
  "source_refs": [
    "lawve-ai/awesome-legal-skills@045f738df65ae53867c2f69f7e8a1e4f61816290:skills/litigation-deadline-calendar-dave-marcus/SKILL.md"
  ],
  "data_classification": "synthetic",
  "task_inputs": {
    "scheduling_order": "Synthetic signed order dated 2026-09-01: expert reports due 2026-11-10; trial 2027-02-01; service-adjusted response deadline not stated.",
    "forum_and_proceeding": "Caption identifies a state trial court; state/local rule source not supplied.",
    "service_method": "Unknown; do not calculate derived dates.",
    "known_modifications": "Order states no extension; later docket activity not supplied.",
    "calendar_preferences": "Draft table only; no attendee invitations.",
    "scope_and_as_of": "Synthetic scope only; law applicability unknown unless identified in the case facts."
  }
}
```

Expected result: a draft with the task-specific sections above, source-backed findings, unknown applicability where the fixture does not establish it, and no external effects or mutations.
