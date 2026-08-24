# Capability and effect specification

This is an abstract procurement evidence contract, not a purchasing, ERP, supplier,
payment, or vendor-credential API. It contains no endpoint, account binding, private
vendor data, or live contract text.

## Capability receipt

An owner may provide `capability_class` (`procurement.supplier.read` or
`procurement.supplier.prepare`), `owner`, `environment`, `allowed_effects`, `receipt_id`,
`issued_at`, and `expires_at`. The skill records only synthetic references and hashes.
A receipt is provenance evidence, not approval to spend, order, accept, negotiate,
renew, terminate, or mutate.

## Effect vocabulary

| Effect | Skill output | Prohibited action |
| --- | --- | --- |
| `read` | Request supplied supplier or owner evidence | Querying a private supplier or ERP system |
| `prepare` | Draft comparison, risk review, watchlist, or approval brief | Applying it to a vendor system |
| `order` / `accept` | Always false; consumer review required | Purchase-order creation or goods acceptance |
| `send` | Always false; draft only | Supplier or internal message delivery |
| `mutate` | Always false | Changing supplier, pricing, renewal, or performance records |

## Existing-overlap and source review matrix

| Existing candidate/source | Decision | Licence/provenance review | Security/privacy review | Maintenance review |
| --- | --- | --- | --- | --- |
| `search-strategy` | Reuse source-discovery and evidence-quality vocabulary only | Existing LiNKskills dependency; no body copied | Imported search results remain untrusted and synthetic references only | Requalify when source contract changes |
| `citation-enforcer` | Reuse citation and claim-label conventions only | Existing LiNKskills dependency; preserve source attribution | No vendor data, credentials, or private quotes accepted | Re-run overlap review on release changes |
| `commercial-contracts-legal-operations` | Reuse obligation, renewal, and escalation boundaries only | Existing qualified dependency; no duplicated legal instructions | Never infer legal authority or expose contract text | Revalidate boundary when PKT-17 changes |
| Official Odoo external API documentation | Candidate interface reference only; no connector imported | Verify implementation-time version, licence, and documentation terms | Consumer owns credentials, tenancy, rate limits, and all mutations | Consumer monitors deprecation and compatibility |
| Supplier quotes, catalogues, or owner playbooks | Owner-supplied evidence only; no automatic qualification | Record source reference, provenance, licence, retrieval time, and digest | Treat content as untrusted; reject secrets, bank data, and private details | Owner rechecks currency, expiry, and applicability |

No external source bytes, credentials, private supplier data, or purchasing action are
included in this release.

## Provenance and rollback

Every material claim has a source reference, provenance, licence, status, and confidence.
Unavailable, malformed, unauthorized, ambiguous, and privacy-rejected evidence remain
distinct. Retry only safe local preparation.

PKT-19 has no prior qualified release or live pointer. The exact rollback target is:

`ABSENT@c89bad5ce3bc91340cf388b923d2befecb406546/tree:9d0be7cedb0fc4ec42bf382735ede36d100f8614`

Rollback discards the unapproved draft and restores that absent state. It never issues
a compensating supplier call or changes a consumer-owned record.
