# Capability and effect specification

This is an abstract contract for an owning integration. It is not an Odoo API client and contains no endpoint, credential, account-binding, or customer-data implementation.

## Odoo pipeline capability receipt

An owner may provide a receipt with `capability_class` (`crm.pipeline.read` or `crm.pipeline.write`), `owner`, `environment`, `allowed_effects`, `receipt_id`, `issued_at`, and `expires_at`. The skill only prepares a request with `mode: prepare`, a synthetic record reference, proposed fields, evidence references, and an idempotency key. A write request remains `PENDING_APPROVAL`; absence or expiry of the receipt is `blocked`. The skill never calls Odoo or claims persistence.

## Effect vocabulary

| Effect | Skill output | Prohibited action |
| --- | --- | --- |
| `read` | Request a supplied owner to provide evidence | Querying Odoo itself |
| `prepare` | Draft a pipeline/proposal/handoff artifact | Applying it to a CRM |
| `send` | Always `false`; draft only | Email, chat, or customer-service delivery |
| `write` | Owner-gated proposal only | Record mutation, stage update, or payment |

Receipts are provenance evidence, not authorization to act. Brain/founder approval and the owning consumer's runtime policy remain required. LiNKreach owns customer-service and relationship operations.

## Provenance and licence

Every external claim has a source reference and provenance/licence label. Fixtures are synthetic or redacted. Never place an Odoo token, customer PII, contract text, private company data, or real account identifier in a receipt, fixture, state line, or output.

## Failure and rollback

Classify unavailable, malformed, unauthorized, and ambiguous receipts separately. Retry only local idempotent preparation. On failure, return a receipt with `FAILED` or `PENDING_APPROVAL`, a safe next action, and the prior exact release/state pointer. Rollback discards an unapproved proposal; it does not issue a compensating live CRM call.
