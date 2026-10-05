# Pairs and statistical-arbitrage research: method notes

## Source audit repairs

Both equity pair entrypoints spread raw price levels as A−βB and use ordinary ADF p-values while describing that as Engle-Granger cointegration; proper residual inference requires cointegration-specific critical values/p-values and declared deterministic terms/lags (or a supported `coint` test). Fixed 0.70 correlation/z=1.5/2/3/half-life gates are uncalibrated; correlation is only prefilter. Price difference and price ratio spreads are incompatible and need declared units/model. Full-sample hedge estimates/leaks into tests; multiple search inflates false discovery. Market-beta neutrality is distinct from cointegrating spread hedge. Their example long $5k A and short $5k×β B is not generally dollar-neutral; derive unit shares and evaluate factor beta separately. Borrow availability, fees, events, impact, leg risk and walk-forward cost proof required. No order/execution.

## Source support closure

AGIPro methodology.md and pairs_trading.md read. TraderMonty/Dr-Pabs methodology and cointegration-guide references and all scripts/tests remain unread/not copied; their unresolved statistical code-contract review blocks method qualification. AGIPro reference includes crypto examples/sizing/DEX content; those branches are excluded from equity method.
