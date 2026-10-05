# Advanced methods — trading-prediction-market-strategy

Use only the branch relevant to the user’s question. These methods are not execution permission and do not set policy thresholds.

## Task-specific analysis

For binary contracts, map all states and terms before pricing. Under payout 1 unit on success, a long bought at ask `a` with success probability `p` has gross expected value per contract `p-a`; subtract fee and other evidenced costs in payout currency. The fee-adjusted break-even probability is the price plus per-contract costs converted to the same units. For other payoff shapes, use the state-payoff sum `Σ probability(state) × net_payoff(state)`; do not force binary logic.

Weather probability requires event window, station, local timezone, observation and rounding rules to match. Crypto/index requires the exact index constituents and settlement averaging/print rule. Forecast error/calibration and market probability are separate evidence. Arbitrage requires every mutually exclusive settlement state, fee, size, collateral, timing and failure path.

## Evidence, uncertainty, and recommendations

For every numeric output, retain source identifier, as-of time, units, sign convention, denominator, transformation, and uncertainty. Mark unknown values as unknown instead of zero. Report primary result, strongest credible alternative explanation, and what evidence would reverse the conclusion. If inputs are incomplete, return a partial finding with exact missing fields.

Jane may recommend strategy changes, increase/trim/exit proposals, and target/risk levels when supplied evidence warrants. Present them as proposals. No order, signing, live activation, or policy mutation. Material/live/capital changes require Lisa and Carlos independent two-channel approval for the exact version.
