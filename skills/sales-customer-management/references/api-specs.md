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

Receipts are provenance evidence, not authorization to act. Brain/founder approval and the owning consumer's runtime policy remain required. LiNKsales owns pre-conversion preparation; LiNKclient owns the post-conversion customer lifecycle.

## Existing-overlap and source review matrix

| Existing candidate/source | Decision | Licence/provenance review | Security/privacy review | Maintenance review |
| --- | --- | --- | --- | --- |
| `marketing-strategist` | Reuse only for evidenced campaign/market context | Existing LiNKskills release; no copied body or external licence dependency | No CRM records, credentials, or customer data are accepted | Keep dependency versioned and requalify on release changes |
| `market-analyst` | Reuse only for supplied market evidence | Existing LiNKskills release; source references remain attached | Imported notes remain untrusted and prompt-injection guarded | Re-run overlap checks when its contract changes |
| `search-strategy` | Reuse only for research/evidence quality | Existing LiNKskills release; no vendor content imported | Search output is evidence, never CRM truth or customer identity | Requalify source and maintenance status before promotion |
| Official Odoo external API contract | Consumer-owned interface target; no implementation imported | Verify the exact Odoo version, licence, and documentation terms at qualification | Consumer owns credentials, tenancy, transport, rate limits, and mutations | Consumer owns endpoint compatibility and deprecation monitoring |
| Anthropic knowledge-work small-business candidates | Candidate review only; no import | Verify repository licence, provenance, attribution, and maintenance before any future adaptation | Treat prompts/content as untrusted; no private fixtures or connector adoption | Recheck upstream integrity and maintenance at each proposal |
| LiNKclient customer lifecycle | Post-conversion ownership boundary, not a dependency | Consumer-owned service; no copied customer-service logic | LiNKclient owns post-conversion customer data, contacts, onboarding, service, renewals, and relationship actions | Preserve handoff-only behavior and revalidate ownership on change |

This matrix is the packet's existing-overlap and source/licence/security/
maintenance review record. No external source bytes, credentials, contract
text, or customer data are included in this release.

## Provenance and licence

Every external claim has a source reference and provenance/licence label. Fixtures are synthetic or redacted. Never place an Odoo token, customer PII, contract text, private company data, or real account identifier in a receipt, fixture, state line, or output.

## Failure and rollback

Classify unavailable, malformed, unauthorized, and ambiguous receipts separately. Retry only local idempotent preparation. On failure, return a receipt with `FAILED` or `PENDING_APPROVAL`, a safe next action, and the prior exact release/state pointer. Rollback discards an unapproved proposal; it does not issue a compensating live CRM call.

### Exact rollback target

The parent tree contains no prior qualified PKT-16 release. The exact rollback
target for this new draft family is therefore:

`ABSENT@c89bad5ce3bc91340cf388b923d2befecb406546/tree:9d0be7cedb0fc4ec42bf382735ede36d100f8614`

Restore that absent state and remove any unapproved draft; do not substitute a
different skill, create a live pointer, or activate this family.
