# Advanced Finance Operations Logic

## Forecast and runway

- Normalize supplied inflows and outflows by period and currency before any
  arithmetic. Do not silently convert currencies; request an approved rate
  source when currencies differ.
- Report a base case and a bounded downside case. The downside case must name
  its assumptions (for example, delayed receivables or a specified cost range)
  and must never be presented as a measured fact.
- Runway is a scenario estimate: available cash divided by scenario net burn.
  If available cash or burn is missing, return `UNKNOWN` and identify the
  missing evidence instead of estimating from unrelated fields.

## Budget, invoice, payment, and expense controls

- Match records only on supplied stable references plus period, currency, and
  amount. A similar description is not proof of a match.
- Keep `observed`, `inferred`, `missing`, and `conflicting` statuses separate.
- Budget versus actual output must preserve the source period and category;
  it must not rewrite the source budget or classify an unmatched line as zero.
- Invoice, payment, and expense tracking observes status and ageing. It does
  not post, settle, approve, or change a source record.

## Close and risk gate

- A close checklist may identify missing reconciliations, supporting documents,
  owner confirmations, and period-lock evidence. It cannot declare a period
  legally or financially closed.
- Material variance, stale snapshots, missing contract metadata, privacy risk,
  or a requested mutation produces `PENDING_APPROVAL`.
- Every risk has an evidence reference, impact, confidence, and proposed owner;
  unknown impact is explicit rather than guessed.

## Contract and provenance gate

- Accept only an exact `contract_id`, `contract_version`, snapshot digest, and
  declared read-only operations supplied by the consumer.
- `source_commit`, `release_tag`, `content_digest`, and `rollback_release` are
  release metadata, not a claim that this skill performed deployment.
- A blank external-effects list is required for a completed read-only brief.
