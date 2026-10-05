# Data and interface boundary — trading-performance-attribution

No external provider/API/adapter is a dependency of this draft. The input contract is a user-supplied snapshot or pointer to existing native LiNKtrading records. `period, ledger_snapshot, opening_nav, cash_flows, fills_costs_income, benchmark_and_calendar` are task dimensions, not asserted schema fields of any installed adapter.

Eric must supply exact repository/path/ref/commit/tree, installed package/version readback, matched release/API documentation, field-level units/precision/time/sequence/error/freshness semantics, and caller/consumer proof before a technical integration claim. Do not infer installed or supported capability from reference documentation, names, or this draft.

Sara owns legal, accounting and tax treatment. Jane's analysis may include strategy and target/risk recommendations where supported; those remain advisory. No credentials, provider calls, orders, signing, live activation, deployment, or policy mutation. Durable task references use existing native session and Program Ledger state only; no JSON/JSONL sidecars.
