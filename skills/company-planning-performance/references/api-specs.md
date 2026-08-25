# API and ownership specifications

## Consumer-owned inputs

The consumer supplies plan references, horizon, period, objectives, KPI values,
delivery signals, and evidence references. The skill accepts synthetic,
redacted, or public evidence only and does not authenticate or retrieve it.

## Read-only normalization contract

| Operation | Effect | Contract |
| --- | --- | --- |
| `plan_review` | none | Build a horizon/objective/KPI review |
| `kpi_review` | none | Preserve target, forecast, actual, and evidence |
| `variance_review` | none | Compare only same-unit, same-period values |
| `reprioritization` | none | Draft proposed owner review only |
| `program.create` | blocked | Program state belongs to the consumer |
| `task.create` | blocked | Task state belongs to the consumer |
| `schedule.activate` | blocked | No scheduler or activation authority |
| `credential.read` | blocked | No credentials or connectors |

The skill owns no Program Ledger, project database, KPI store, calendar,
connector, transport, or mutable pointer. It must not duplicate or silently
supersede state owned by a consumer system.

## Evidence and licensing

Fixtures use only synthetic references and values. External sources, if used by
a consumer, must be supplied as provenance references with currentness and
licence review outside this helper. No private company data or customer data is
retained in releases or telemetry.
