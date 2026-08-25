# Private health source, destination, and review record

## Source and licence review

| Source | Review use | Licence/attribution posture |
| --- | --- | --- |
| [WHO physical activity](https://www.who.int/news-room/fact-sheets/detail/physical-activity) | Evidence framing for exercise proposals; no copied clinical advice | WHO public guidance; rules are summarized, not reproduced; attribution retained. |
| [NHS sleep and tiredness](https://www.nhs.uk/live-well/sleep-and-tiredness/) | Sleep terminology and uncertainty cross-check | UK Crown copyright guidance; no text, template, or personal record is bundled. |
| [CDC healthy weight](https://www.cdc.gov/healthy-weight-growth/about/index.html) | Measurement and estimate caution | U.S. public guidance; no patient content or treatment recommendation is bundled. |

This release contains generic method rules and synthetic fixtures only. It does
not provide medical advice, diagnose, prescribe, change treatment, or copy
source text. Consumers must obtain qualified clinical review for any medical
question; the skill does not infer that review occurred.

## Private destination contract

The owning consumer supplies a private local destination and access controls.
Detailed observations, photos, treatment/appointment records, nutrition,
measurements, and uncertainty records remain there. A handoff may contain only
an explicitly requested `capacity_state`; no underlying health cause may be
attached. LiNKskills does not own the private database, image store, calendar,
transport, retention policy, credentials, or emergency service.

The helper's effects contract is exact and fail-closed:
`external_calls=[]`, `mutations=[]`, `calendar_reminders=[]`,
`messages_sent=[]`, and `data_exports=[]`. A reminder is a deduplicated
proposal, not a calendar operation.

## Existing-overlap and security review

| Existing method | Decision |
| --- | --- |
| `department-head` | Not reused: role/management communication is not private health state. |
| `task-decomposition` | Not reused: generic planning does not own health fields, privacy, or calculations. |
| `company-communication` | Boundary only: a consumer may format a safe capacity summary, but this skill owns no transport wording. |

Security review rejects live identifiers, credentials, unredacted images,
private records in fixtures or telemetry, unknown fields, diagnosis,
treatment-change instructions, stock emergency wording, spot-reduction claims,
calendar calls, and detailed export. Maintenance review requires versioned
schemas, deterministic calculations, append-only uncertainty/correction
records, profile hashes, and a rollback pointer to the exact absent base.

## Rollback and ownership

Rollback is `ABSENT@610e5a42b2356d2da5eaea0ef95cea806f93f45e/tree:158d87825593e781e43d9a4eaaecf1259c6387e0`.
Discarding the unintegrated release changes no consumer store, transport,
calendar, clinical record, or private destination.
