# Interview modules

Do not start the real interview during corrective setup. Sara reads existing authorized records first, prefills facts, then asks only material unknown/conflicting questions in manageable rounds. Status values: verified / Principal-reported / proposed / conflicting / unknown. Every fact needs source, date and owner. No tax elections, bank authority, accounting basis or worker location is inferred.

- [Entity, ownership and jurisdiction](01-entity.md) — Legal specialist with tax/compliance.
- [Products, revenue and customers](02-revenue.md) — Controller with David business input.
- [Banks, funding and financial authority](03-banks.md) — Treasury specialist.
- [Existing books, reporting and tax preparation](04-books.md) — Controller and tax/compliance specialist.
- [Human employees and consultants](05-humans.md) — Finance Operations/human HR specialist.
- [Agent workforce quality and lifecycle](06-agents.md) — Tax/compliance specialist for evaluation; Sara operational mandate.
- [Legal matters, contracts and corporate records](07-legal.md) — Legal/corporate specialist.
- [Ventures, plans and operating coordination](08-operations.md) — Sara with executive/Program owners.
- [Records, classification and continuity](09-records.md) — Sara; Librarians and Eric technical owners.
- [Approvals, limits and continuing ownership](10-authority.md) — Sara; Lisa and Principal approve within authority.

## Register record contract

Start from `fact-register-template.json`, which contains no assumed company facts. Validate the register against `../schemas.json#/definitions/interview_register`. Every recorded fact, answer and unresolved decision needs a source reference, source date and owner; `unknown` records need a concrete follow-up, and `conflicting` records point to the other record IDs. Keep unknown facts and unresolved decisions empty until evidence or an interview question creates a record.

`native_checkpoint_ref` is an opaque consumer-native metadata projection only. Do not place raw facts, documents, or session history in it. `register-schema-cases.json` contains synthetic contract fixtures; run `python3 test_register_schema.py` from this directory for offline positive/negative shape checks. These checks do not test interview behavior or authorize persistence.
