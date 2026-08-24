# Finance Operations Interface and Source Review

## Approved Odoo contract boundary

This skill targets an approved consumer-owned Odoo tool/API contract. The
contract is an input, not an implementation detail. The consumer must supply:

- `contract_id` and immutable `contract_version`;
- exact snapshot `content_digest`, `retrieved_at`, period, currency, and source owner;
- the read operation declarations for invoices, payments, expenses, budgets,
  cash balances/flows, and period-status observations; and
- the owning adapter's authority and escalation contact.

The consumer owns Odoo endpoint/model mapping, transport, credentials, rate
limits, retries, tenancy, privacy filtering, and every mutation. This skill
must receive a bounded snapshot and must not call Odoo or an MCP/API connector.
The approved contract-review sources are named below. They are references only;
this release imports no service code, prompts, credentials, or customer data.

## Named external sources and licence posture

| Source | Version/status | Licence or terms posture | Use in this release |
| :--- | :--- | :--- | :--- |
| [Anthropic Claude Platform model documentation](https://platform.claude.com/docs/en/about-claude/models/overview) | Current platform documentation reviewed 2026-08-24 | Proprietary service documentation; no copied prompts, model weights, SDK source, or service content | Candidate capability and currentness review only |
| [Anthropic Commercial Terms of Service](https://www.anthropic.com/legal/commercial-terms) | Effective 2025-06-17 at review time | Commercial service terms; they do not grant a licence to copy or redistribute the service | Terms, privacy, output-ownership, and human-review boundary review only |
| [Odoo 19 External JSON-2 API](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html) | Odoo 19.0, External JSON-2 API | Documentation/API contract reference; no Odoo code or endpoint implementation is imported | Approved read-operation contract reference only |
| [Odoo 19 licence documentation](https://www.odoo.com/documentation/19.0/legal/licenses.html) | Odoo 19.0 | Community Edition: LGPL-3; Enterprise Edition: Odoo Enterprise Edition License v1.0; Odoo Apps: Odoo Proprietary License v1.0 | Licence/hosting qualification gate; no Odoo software or Apps content is bundled |

The Odoo contract therefore remains version-bound to Odoo 19.0 and must record
whether the consumer is using Community, Enterprise, or another explicitly
qualified edition before selection. The consumer owns hosting, pricing-plan
eligibility, endpoint/model mapping, transport, credentials, and mutations.
Snapshot and output provenance references are restricted by schema to the
official Anthropic and Odoo documentation URI patterns listed above.

## Candidate and reuse review

| Candidate or existing primitive | Decision | Licence/security/maintenance posture | Boundary |
| :--- | :--- | :--- | :--- |
| Anthropic Claude Platform and small-business service candidates | Review candidate only; no import | Named documentation and Commercial Terms above; recheck provenance, prompt safety, maintenance, privacy, and service terms during the external lifecycle | No copied prompt, connector, credential, or private fixture |
| Official Odoo 19 External JSON-2 API and licence sources | Contract reference | Named Odoo 19 API and licence sources above; edition and hosting terms are qualification inputs | Consumer adapter owns transport and mutations |
| `revenue-adapter-base` | Reuse as normalized revenue input | Existing LiNKskills dependency; preserve source references and do not duplicate normalization | Supplies records only |
| `studio-controller` | Narrow reuse for close/review controls | Qualified local primitive after its ledger/connector assumptions are removed | Review guidance only; no system of record |

## Read-only operation vocabulary

The approved contract may expose equivalent operation names, but the snapshot
must declare the exact mapping. The skill may observe:

`invoices.read`, `payments.read`, `expenses.read`, `budgets.read`,
`cash_flow.read`, and `period_status.read`.

The following are never accepted as this skill's effects:

`invoice.create`, `invoice.update`, `payment.post`, `expense.approve`,
`journal.post`, `budget.write`, `period.close`, `credential.read`, or any
unlisted operation. An unknown operation fails closed.

## Output and provenance

Completed output carries the exact candidate release metadata: release tag
`v1.0.0`, source commit
`1d5a9d7d39e18dd8acfa14392f06f4d22211d060`, source tree
`315d69b89ff8930dfc2944ac049ccd7c965a548a`, and metadata digest
`sha256:29c5514089f263961992e0fcd42be61700fdee69560aea865222528ce3dbfe2f`.
It also carries the input snapshot digest, contract ID/version, allowlisted
source references, and an empty `external_calls`/`mutations` declaration.

Rollback is a catalog action and is bound to the exact qualified prior
identity `catalog:starter-foundation@1.0.0`, whose source parent commit is
`2d24e55e96caf4fc2ec37330d30d740805904368` and source tree is
`fa328aa50c7febaefb22f9c22f883587c49e9e3f`. This packet creates no live
pointer or activation. The migrated controller's prior exact release remains
`studio-controller@v1.0.0`.
