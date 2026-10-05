# Advanced methods — trading-portfolio-exposure-risk

Use only the branch relevant to the user’s question. These methods are not execution permission and do not set policy thresholds.

## Task-specific analysis

Cash exposure can be expressed as signed market value divided by a same-time NAV denominator; derivatives require separately stated gross notional and supported delta-equivalent. Keep currency, multiplier, contract units and FX explicit. Correlations require aligned dated returns and report pair counts/window; they are historical dependence, not forecast.

Drawdown uses an equity path including opening wealth; with external flows, apply one declared flow-adjustment method. Scenario P&L for a supplied linear position is `signed quantity × price change × multiplier`, before currency conversion and costs. Nonlinear repricing requires contract terms and a supported model. Unknown mappings remain unclassified, not diversified.

## Evidence, uncertainty, and recommendations

For every numeric output, retain source identifier, as-of time, units, sign convention, denominator, transformation, and uncertainty. Mark unknown values as unknown instead of zero. Report primary result, strongest credible alternative explanation, and what evidence would reverse the conclusion. If inputs are incomplete, return a partial finding with exact missing fields.

Jane may recommend strategy changes, increase/trim/exit proposals, and target/risk levels when supplied evidence warrants. Present them as proposals. No order, signing, live activation, or policy mutation. Material/live/capital changes require Lisa and Carlos independent two-channel approval for the exact version.
