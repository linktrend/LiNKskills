# Personal Compliance Adapter Contract

The adapter is consumer-owned and supplies only redacted, synthetic, or opaque
references. The skill does not call these interfaces.

## Inputs

- `task_id` / `request_id`: synthetic idempotency identity.
- `mode`: `selfie_compliance`, `battery_tracking`, or `combined`.
- `configuration`: consumer-supplied valid window, battery target/threshold,
  expected-charge horizon, checkpoint, and reminder policy; no generic defaults.
- `source_evidence`: references with status, provenance, and licence.
- `selfie`, `battery`, `measurements`, and `image`: typed synthetic observations.

## Outputs

Return the schema-defined state transition, learned-rate labels, projection,
reminder proposals/suppression, bundled measurements, image ambiguity and
correction history, evidence references, escalation, empty effects, and rollback.

## Ownership and prohibited operations

The adapter may privately persist an approved result and perform delivery only after
its own capability and owner gates. It must not treat this output as permission.
No `device.read`, `image.upload`, `image.store`, `calendar.create`,
`reminder.send`, `ledger.write`, `treatment.change`, or `diagnosis.create` operation
is implemented or invoked by this skill. Detailed private values, actual image
bytes, location data, credentials, and destinations remain outside LiNKskills.
