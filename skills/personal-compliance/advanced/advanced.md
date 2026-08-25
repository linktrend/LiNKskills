# Advanced Personal Compliance Guidance

## Configuration is data, not authority

Require a consumer-owned configuration receipt for every window, threshold,
checkpoint, reminder, charger, and location context. A value in a request can
parameterize a calculation, but cannot grant permission to write private state or
send a reminder. Missing configuration is an explicit `needs-evidence` result.

## State transitions

Treat a selfie result as an append-only transition with the prior state and event
reference retained by the private consumer ledger. Do not infer completion from
silence, a calendar event, a message, or a missing image. A late report is distinct
from a completed-in-window report. Duplicate reminders are detected using opaque
consumer references, not message text.

## Rate learning and uncertainty

Reject impossible percentages, negative elapsed time, zero-duration rates, and
unlabelled charger/location observations. Keep charge and discharge estimates
separate. Mark estimates as provisional until the configured minimum observations
are met. Saturation is a model adjustment, not a claim about device health.

## Image correction

Accept only extracted fields and opaque image references supplied by a consumer
adapter. Material ambiguity asks for confirmation; immaterial ambiguity remains
labelled. A correction appends `{prior, proposed, reason, recorded_at}` and leaves
the prior confirmed value intact until the consumer explicitly confirms it.

## Failure handling

Privacy rejection, malformed input, missing evidence, unknown actions, and unsupported
diagnostic requests fail closed. Return a safe next action and the exact rollback
pointer. Never echo rejected private content into an error, telemetry, or fixture.
