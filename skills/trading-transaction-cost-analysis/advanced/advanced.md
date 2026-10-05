# Method notes

## 1. Freeze the asset, side, order quantity/notional, reference price, horizon, NAV and currency

Freeze the asset, side, order quantity/notional, reference price, horizon, NAV and currency. Normalize units first; do not mix bps, percentages, decimal fractions, shares, contracts, base currency or quote currency.
## 2. If only portfolio weight is given, derive traded notional = absolute weight change × NAV and quantity = notional / price, adjusting for contract multiplier where applicable

If only portfolio weight is given, derive traded notional = absolute weight change × NAV and quantity = notional / price, adjusting for contract multiplier where applicable. Preserve per-asset dimensions before aggregation; do not difference across the asset axis.
## 3. Build cost components separately: commissions/venue fees, spread crossing (state whether full spread or half-spread per side), slippage relative to the chosen benchmark, market impact, borrow/financing, fixed transaction charges and taxes where supplied

Build cost components separately: commissions/venue fees, spread crossing (state whether full spread or half-spread per side), slippage relative to the chosen benchmark, market impact, borrow/financing, fixed transaction charges and taxes where supplied. Prevent overlapping components from being charged twice.
## 4. Use time-matched point-in-time quotes, fee schedules, realized fills, volatility, volume/ADV and borrow observations when available

Use time-matched point-in-time quotes, fee schedules, realized fills, volatility, volume/ADV and borrow observations when available. Label stale, illustrative or model-imputed values; do not quote generic source floors as current universal rates.
## 5. Compute participation = order quantity / ADV quantity or order notional / same-currency ADV notional using compatible periods

Compute participation = order quantity / ADV quantity or order notional / same-currency ADV notional using compatible periods. If denominator is absent, incomparable or zero, do not calculate capacity. Report order as fraction of ADV and any stated participation cap.
## 6. Choose a model only within its supported domain

Choose a model only within its supported domain. A square-root/Almgren-Chriss-type impact model needs calibrated coefficient, volatility and participation units; disclose threshold/domain and compare with empirical fills or quote curves. For AMMs, distinguish pool impact, route/fee and quote staleness; do not equate order-book ADV with pool reserves.
## 7. For shorts, charge point-in-time borrow and financing only for the modeled holding period

For shorts, charge point-in-time borrow and financing only for the modeled holding period. A locate failure means no entry; record a missed opportunity or skipped trade, not a worse fill or extra slippage. If failure probability is unobserved, show scenario cases rather than inventing a rate.
## 8. Aggregate side-specific costs into round-trip cost and net expected return only where gross-return horizon, benchmark and cost timing align

Aggregate side-specific costs into round-trip cost and net expected return only where gross-return horizon, benchmark and cost timing align. Show algebra and denominators; include 1x/2x/3x sensitivities and break-even move without claiming the strategy is profitable or unprofitable absent an owner criterion.
## 9. Conclude with constraints, uncertainty, input gaps and route implementation/configuration questions to Eric

Conclude with constraints, uncertainty, input gaps and route implementation/configuration questions to Eric. No API calls, provider connection, engine edits or order execution.