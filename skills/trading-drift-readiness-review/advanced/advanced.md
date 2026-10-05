# Advanced methods — trading-drift-readiness-review

Use only the branch relevant to the user’s question. These methods are not execution permission and do not set policy thresholds.

## Task-specific analysis

Freeze baseline/current windows and point-in-time version before comparing features, predictions, net outcome, execution cost and operational data quality. Show window lengths, sample counts, missingness, out-of-range records and revision/freshness. Distribution statistics such as PSI depend on fixed reference bins, sample size and binning; expose those choices and treat the result as a diagnostic rather than a trigger.

Deterioration is a hypothesis. Test competing causes such as market regime, universe composition, data revisions, higher costs/capacity, model changes and sample noise. Readiness is an evidence matrix across lineage, freshness, reconciliation, monitoring, recovery, rollback and governance; an unobserved control is not verified. Eric owns technical controls and current adapter contracts.

## Evidence, uncertainty, and recommendations

For every numeric output, retain source identifier, as-of time, units, sign convention, denominator, transformation, and uncertainty. Mark unknown values as unknown instead of zero. Report primary result, strongest credible alternative explanation, and what evidence would reverse the conclusion. If inputs are incomplete, return a partial finding with exact missing fields.

Jane may recommend strategy changes, increase/trim/exit proposals, and target/risk levels when supplied evidence warrants. Present them as proposals. No order, signing, live activation, or policy mutation. Material/live/capital changes require Lisa and Carlos independent two-channel approval for the exact version.
