# Method notes

## 1. Normalize instrument, side, price/quantity units, tick/lot constraints, entry, timezone, observation granularity, costs and actions

Normalize instrument, side, price/quantity units, tick/lot constraints, entry, timezone, observation granularity, costs and actions. Reject incompatible units and unresolved position side.
## 2. Calculate per-unit and total initial risk from entry-to-stop distance, quantity and multiplier; state currency and whether costs/funding are included

Calculate per-unit and total initial risk from entry-to-stop distance, quantity and multiplier; state currency and whether costs/funding are included. For shorts reverse price inequalities and cash-flow signs.
## 3. Represent each candidate method separately: fixed distance/percent, volatility or support reference, trailing ratchet, profit target, elapsed-time rule, signal reversal and liquidity deterioration

Represent each candidate method separately: fixed distance/percent, volatility or support reference, trailing ratchet, profit target, elapsed-time rule, signal reversal and liquidity deterioration. Use only supplied or reproducibly derived inputs; no default “recommended” parameter is treated as valid.
## 4. Specify trigger price vs executable fill, bar-close vs intrabar trigger, stop/target precedence, activation delay, ratchet direction, and what happens when both stop and target lie inside one bar

Specify trigger price vs executable fill, bar-close vs intrabar trigger, stop/target precedence, activation delay, ratchet direction, and what happens when both stop and target lie inside one bar. Where sequence is unknown, show adverse and alternate bounds or mark unidentifiable.
## 5. For partial exits, sum planned quantities to no more than the open position; track remaining quantity and recompute stop/target exposure after each modeled fill

For partial exits, sum planned quantities to no more than the open position; track remaining quantity and recompute stop/target exposure after each modeled fill. Do not assume a fill or move a stop to breakeven unless the rule explicitly defines it.
## 6. Replay each variant over the same dated input and cost conventions

Replay each variant over the same dated input and cost conventions. Include gaps, spreads/depth, partial fills, rejected/unavailable exit liquidity, fees, borrow/funding and uncertainty; do not treat a stop trigger as a guaranteed fill price.
## 7. Compare net outcome, worst modeled excursion, time in position and sensitivity across supplied parameters

Compare net outcome, worst modeled excursion, time in position and sensitivity across supplied parameters. Label historical replay as descriptive and avoid causal claims that the rule “would” protect a future position.
## 8. Report unsupported assumptions, relevant owner handoff and what data would distinguish variants

Report unsupported assumptions, relevant owner handoff and what data would distinguish variants. Do not submit, route, modify or activate an order.