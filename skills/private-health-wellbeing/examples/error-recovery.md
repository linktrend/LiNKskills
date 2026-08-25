# Synthetic fail-closed patterns

- Missing source evidence returns `FAILED`; it does not invent a value.
- A repeated known question returns `FAILED` and identifies the stable field
  name so the consumer can avoid redundant collection.
- A dose-change request returns `PENDING_REVIEW`; it never proposes a new dose.
- A photo with material ambiguity requires an uncertainty record and a later
  correction record; it is not silently reclassified.
- A request to send detailed health data, set a calendar reminder, diagnose,
  or use spot-reduction language is refused with empty effects.
