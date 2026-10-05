# Advanced methods — trading-microstructure-execution-analysis

Use only the branch relevant to the user’s question. These methods are not execution permission and do not set policy thresholds.

## Task-specific analysis

For signed implementation shortfall, set side sign `s=+1` for a buy and `s=-1` for a sell. Per-unit cost is `(fill - arrival benchmark) × s`; multiply by filled units and contract multiplier to get quote-currency cost, then add fees/rebates with explicit FX timing. Report partial/unfilled quantity separately and mark its opportunity cost only at a supplied evaluation horizon.

A book sweep should consume price levels in sequence for the requested size. Distinguish quoted spread, effective spread, price impact, fee/rebate, route/gas, latency and post-trade markout. Do not claim causation from a markout correlation. For MEV, transaction/block order, pre/post state, route and fee/tip evidence are required; a suspicious price reversal alone is a hypothesis.

## Evidence, uncertainty, and recommendations

For every numeric output, retain source identifier, as-of time, units, sign convention, denominator, transformation, and uncertainty. Mark unknown values as unknown instead of zero. Report primary result, strongest credible alternative explanation, and what evidence would reverse the conclusion. If inputs are incomplete, return a partial finding with exact missing fields.

Jane may recommend strategy changes, increase/trim/exit proposals, and target/risk levels when supplied evidence warrants. Present them as proposals. No order, signing, live activation, or policy mutation. Material/live/capital changes require Lisa and Carlos independent two-channel approval for the exact version.
