# Advanced methods — trading-performance-attribution

Use only the branch relevant to the user’s question. These methods are not execution permission and do not set policy thresholds.

## Task-specific analysis

Reconcile the return series first: opening NAV + external flows + investment P&L/income - costs = ending NAV, with a visible residual. Select and name money-weighted, time-weighted or simple P&L/NAV method; don’t mix their denominators. Closed-trade cohort cumulative performance and dated cash proceeds are separate: a trim realized earlier plus a close now must not double-count proceeds in current-period cash.

A win rate should show all closed trades including breakevens as denominator; a separate non-flat rate may be informative. Profit factor is undefined without losses; singleton sample SD is undefined. CAGR uses compounded beginning/end wealth over exact elapsed time; arithmetic mean is not CAGR. Empirical tails from small samples are descriptive only.

## Evidence, uncertainty, and recommendations

For every numeric output, retain source identifier, as-of time, units, sign convention, denominator, transformation, and uncertainty. Mark unknown values as unknown instead of zero. Report primary result, strongest credible alternative explanation, and what evidence would reverse the conclusion. If inputs are incomplete, return a partial finding with exact missing fields.

Jane may recommend strategy changes, increase/trim/exit proposals, and target/risk levels when supplied evidence warrants. Present them as proposals. No order, signing, live activation, or policy mutation. Material/live/capital changes require Lisa and Carlos independent two-channel approval for the exact version.
