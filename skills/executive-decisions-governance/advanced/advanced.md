# Executive decision field rules

## Matter and evidence

- `matter_ref` is unique within the consumer and is never minted by a
  connector or silently reused.
- `source_evidence` contains only `fixture:`, `source:`, or `consumer:`
  references with an explicit `confirmed`, `reported`, or `not_reported` status.
- Missing evidence blocks a readiness claim. A supplied `not_reported` item is
  retained as uncertainty rather than filled by inference.

## Choices and decisions

- Every decision brief has at least two distinct choices, each with a tradeoff,
  and includes `Other — specify` unless the owner explicitly states the set is
  exhaustive.
- Recommendation is separate from the owner decision. `approved` and
  `rejected` are record statuses only; the skill never performs them.
- An approval record requires a named owner reference and a selected choice.

## Rule impact and implementation tracking

- Rule impact records describe proposed scope and rationale; they never activate
  or enforce a rule.
- Tracking records retain item, owner, status, and evidence reference. They do
  not become tasks, schedules, standing rules, meetings, or Program state.
- Duplicate tracking item IDs and duplicate evidence references fail closed.

## Mobile and privacy

Lead with the matter and requested owner decision, keep the brief compact, and
preserve uncertainty. Use synthetic, redacted, or public inputs only. Reject
credentials, identifiers, private records, customer content, and confidential
company material in fixtures, output, telemetry, and subordinate access.
