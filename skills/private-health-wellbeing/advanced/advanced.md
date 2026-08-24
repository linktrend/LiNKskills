# Private health field rules

## Assessment and checkpoints

An initial or monthly assessment may omit a field, but the output must carry
`not_reported`; omission is not permission to infer. The three checkpoint
fields are independent: `energy`, `mood`, and `stress` each use an integer from
1 through 5. `capacity_state` is a separate bounded state (`low`, `steady`, or
`available`) and is never treated as a health diagnosis or cause.

Before asking a question, compare its stable field name with `known_answers`.
If it is already known, do not ask it again; return a failed redundant-question
result. This is a contract rule, not a model preference.

## Calculations and estimates

- Hydration is `bottle_ml - remaining_ml`; reject negative or missing values.
- Sleep duration uses supplied start/end timestamps and records the resulting
  minutes plus timezone/source evidence. Overnight spans are allowed; ambiguous
  timestamps are not.
- Protein and nutrition values are estimates only. Every estimate names its
  basis and uncertainty; no nutritional or medical target is prescribed.
- Measurements retain `device` and `source` separately. A scale value is not a
  waist value, and a bowel observation is not a symptom diagnosis.

## Treatment, images, and exercise

Treatment/appointment mode can capture a supplied appointment reference,
combined dose record, or dose-change question, but it cannot alter a dose,
diagnose, or create an instruction. Meal/photo mode requires a synthetic or
redacted image reference, an uncertainty note for material ambiguity, and an
append-only correction record when the owner supplies a correction.

Exercise output is a proposal grounded in at least one supplied evidence
reference. Reject claims about spot reduction or guaranteed body-area change.
Do not substitute a generic safety or emergency script for missing evidence.

## Reminders and export

Reminder requests are deduplicated by a caller-supplied stable `reminder_key`
and remain a proposed private record; the skill never invokes a calendar.
Detailed measurements, images, treatment data, and nutrition data cannot be
exported. An explicitly requested `capacity_state` may be included in the
consumer's own bounded handoff, with no underlying health cause attached.
