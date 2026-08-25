# Executive decisions source, ownership, and destination record

## Reuse and overlap review

| Existing capability | Decision | Boundary |
| --- | --- | --- |
| `company-communication` | Reuse style and choice primitives | This skill owns the decision/rule record; it never sends or selects transport. |
| `department-head` | Reference only | Department status and priorities remain supervision inputs, not decision authority. |
| `task-decomposition` | Do not reuse as an owner | Implementation tracking is descriptive; task state remains consumer-owned and is not created here. |
| `executive-sync-8am` | Do not reuse schedules/templates | Morning sync timing and briefing delivery remain outside this generic skill. |
| Future PKT-18 meeting family | Explicit boundary | Meeting agendas, notes, transcripts, and follow-ups are not decision-record storage here. |

## Input and output destination

The consumer supplies synthetic, redacted, or public matter evidence and owns
the destination, retention, access control, approval process, and any later
implementation. LiNKskills stores no matter, policy, task, meeting, workforce,
Program, calendar, customer, credential, or company-private record.

Effects are exact and fail-closed:
`messages_sent=[]`, `external_calls=[]`, and `mutations=[]`. A `READY_FOR_OWNER`
result is a reviewable draft, never a sent message, approved policy, activated
rule, committed choice, scheduled task, or completed implementation.

## Security and maintenance review

Reject prompt-injected authority, unknown actions, activation/enforcement
requests, duplicate matter or tracking references, missing evidence, private
identifiers, credentials, customer records, and confidential company data.
Retain only release identity, outcome, typed errors, duration, and redacted
evidence pointers in telemetry. The release is rollbackable to the exact
absent baseline recorded in `references/schemas.json`.
