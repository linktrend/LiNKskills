# API and ownership specifications

## Read-only operations

| Operation | Effect | Contract |
| --- | --- | --- |
| `incident_intake` | none | Preserve incident identity, owner, state, severity, and evidence |
| `outage_review` | none | Record observed impact and recovery options |
| `security_coordination` | none | Preserve security evidence and Platform boundary; no credentials |
| `continuity_review` | none | Compare backup, recovery, dependency, and residual-risk evidence |
| `recovery_decision` | none | Draft owner-review options; never execute recovery |
| `closure_review` | none | Require closure evidence, owner review, and residual risks |

## Owning systems

The owning responder coordinates the incident. Platform owns platform controls;
the Program Ledger owns program state; deployment authority owns deploy,
rollback, isolation, and release decisions. This skill owns none of those
systems and has no connector, credential, scheduler, message transport, or
customer-record binding.

## Prohibited effects

`deploy`, `rollback`, `isolate`, `rotate_credentials`, `send`, `approve`,
`close`, `program.mutate`, and `deployment.mutate` are blocked. Internal and
customer communication is draft-only. Fixtures and telemetry retain synthetic
references and evidence hashes, never raw incident or customer data.
