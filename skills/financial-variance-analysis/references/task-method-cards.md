# Financial variance analysis cards

These are task methods preserved from the pinned Anthropic finance variance-analysis and financial-services variance-commentary sources. Exact source paths/pins are in `references/source-selection.md`; originals are retained under `references/upstream/`. Source example thresholds are not company policy.

## Card A — Comparable basis and variance arithmetic

Align account/category, entity, time window, units, currency, sign convention and actual/comparator basis. For each row compute `delta = actual - comparator`; compute percentage variance as `delta / abs(comparator)` only when a nonzero denominator is meaningful. When comparator is zero or sign changes, show amount delta and label percentage `n/a` or explain the selected convention. For margin/rate metrics show percentage-point or basis-point change, not a mislabeled percent growth.

## Card B — Revenue price/volume/mix bridge

Where both actual and comparator quantity and rate exist, compute `volume effect = (actual volume - comparator volume) × comparator rate`, `price effect = (actual rate - comparator rate) × actual volume`, and `interaction/mix residual = total revenue delta - volume effect - price effect` if units/products mix make the two-factor decomposition incomplete. Verify the bridge components sum to the actual revenue delta. Label the method used; do not double-count a residual as a driver.

## Card C — Headcount and spend drivers

For payroll/people cost, request headcount and compensation by period; decompose only supported headcount, rate, role/department mix, hire/exit timing and attrition/backfill effects. For operating expense, inspect source transactions and classify evidenced movement into people-driven, volume-driven, discretionary, fixed/contractual, one-time or timing categories. These are investigation lenses; do not infer business causation from account name or variance sign.

## Card D — Flags and investigation priority

Apply only a company-supplied dollar/percentage/materiality threshold or always-comment list. If absent, show computed deltas and rank by absolute amount, relative movement (when valid), unexpected direction, newness and repeated/cumulative movement without declaring a formal materiality finding. Keep controller-set flags separate from analyst-priority suggestions.

## Card E — Driver evidence and narrative

Build a bridge from starting to ending value where driver amounts can be quantified, and verify `starting value + signed drivers = ending value`. For each flagged row, show current/comparator values, amount and percent/pp changes, favorable/unfavorable only where sign interpretation is supported, sourced driver or `driver unclear — owner follow-up`, timing/trend uncertainty and next evidence question. A narrative explains a cause only when underlying journal-source, vendor, headcount, volume, rate or other activity evidence supports it; do not restate the delta as a cause or invent an outlook.
