# Known source-pattern hazards

Both equity pair entrypoints spread raw price levels as A−βB and use ordinary ADF p-values while describing that as Engle-Granger cointegration; proper residual inference requires cointegration-specific critical values/p-values and declared deterministic terms/lags (or a supported `coint` test). Fixed 0.70 correlation/z=1.5/2/3/half-life gates are uncalibrated; correlation is only prefilter. Price difference and price ratio spreads are incompatible and need declared units/model. Full-sample hedge estimates/leaks into tests; multiple search inflates false discovery. Market-beta neutrality is distinct from cointegrating spread hedge. Their example long $5k A and short $5k×β B is not generally dollar-neutral; derive unit shares and evaluate factor beta separately. Borrow availability, fees, events, impact, leg risk and walk-forward cost proof required. No order/execution.

## Repair rule

Separate verified observation, calculation, inference, scenario, and advisory. Never infer successful evaluation from structural validation.
