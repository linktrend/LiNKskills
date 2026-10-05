# Advanced methods — trading-defi-liquidity-yield

Use only the branch relevant to the user’s question. These methods are not execution permission and do not set policy thresholds.

## Task-specific analysis

Pool comparison is size-specific. For CPMM, do not silently combine fee and invariant: first calculate invariant output from the supplied reserves and gross input using the venue’s documented fee convention, then present fee and effective fill separately. For CLMM and bins, active liquidity changes by price interval; only tick/bin data or a contemporaneous quote ladder supports depth.

For a matched full-range CPMM position, relative-price IL is `2√r/(1+r)-1`, where `r=(quote/base)_end/(quote/base)_start`; show the matched hold value and token inventory. Do not apply this closed form to a concentrated range. A range position requires opening inventory, boundaries, traversed price path, fee accrual by active interval, rebalance and exit assumptions.

Net LP result is ending position value + actually accrued/valued fees + valued rewards - transaction/rebalance/exit costs - matched hold value. Keep gross fee yield distinct from net excess return. Report arithmetic APR or compounded APY only with dated observations, explicit day count, compounding/reinvestment and stable-volume assumptions. A displayed APR or annualized one-day volume is a scenario, never a forecast.

## Evidence, uncertainty, and recommendations

For every numeric output, retain source identifier, as-of time, units, sign convention, denominator, transformation, and uncertainty. Mark unknown values as unknown instead of zero. Report primary result, strongest credible alternative explanation, and what evidence would reverse the conclusion. If inputs are incomplete, return a partial finding with exact missing fields.

Jane may recommend strategy changes, increase/trim/exit proposals, and target/risk levels when supplied evidence warrants. Present them as proposals. No order, signing, live activation, or policy mutation. Material/live/capital changes require Lisa and Carlos independent two-channel approval for the exact version.
