# Known failure patterns

- Sources conflict on full vs half spread and per-side vs round-trip treatment; make convention explicit and compute each crossing once.
- Some source snippets mix bps and decimal fractions or misstate reserve-based impact equations; check dimensional consistency and do not reuse unverified formulas.
- Fixed “minimum credible” friction, borrow APR, locate-failure rates and fee tables are stale-sensitive and universe-specific; require dated observations or scenario labels.
- Capacity formulas must use same-currency notional ADV or same-unit quantity ADV; factor portfolio NAV, price, contract multiplier and asset-panel orientation.
- Square-root impact models have calibration/domain limits; Almgren-Chriss is not universal, and AMM/CLMM depth differs from equity ADV.
- Upstream recommendations about Jupiter quotes, broker APIs, execution schedules, paid data and engine setup are not dependencies or authorization. Eric owns technical implementation.
- Treating a research draft or fixture as a trade recommendation, authorization, evaluation receipt, or certification.
- Writing JSON/JSONL runtime sidecars instead of using native session and approved Program Ledger.
