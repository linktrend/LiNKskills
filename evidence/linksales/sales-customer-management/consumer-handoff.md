# LiNKsales consumer handoff

Pin `sales-customer-management@1.1.0` together with content digest
`skill-release:cf4533d190b3c66ad4b260d317f0657db682b698b723f7a6249445d1e940d912`.
The Skills gateway must require both values and must reject draft, `latest`,
mutable, digest-mismatched, unqualified, or unavailable releases without
fallback.

This methodology prepares LiNKsales work before conversion. It does not grant
send, Odoo, CRM mutation, payment, contract, activation, or other execution
authority. Once evidenced conversion occurs, route the prepared handoff to
LiNKclient; do not continue customer-lifecycle work through this skill.

Publication is on implementation HOLD: the local Eval Runner passed, but sealed isolation certification and a live Skills gateway publication/consumer receipt are unavailable. The dependency remains disabled until the consumer independently accepts the
exact pin. Rollback withdraws only this release pointer, restores the prior
catalogue, and leaves the consumer dependency disabled. Immutable release
content is retained.
