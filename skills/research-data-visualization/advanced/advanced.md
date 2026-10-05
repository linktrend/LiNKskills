# Method-specific extension

## Applied method

1. Clarify the analytic question and audience; identify the comparison, distribution, trend, or relationship to show.
2. Validate data grain, missingness, units, time basis, denominator, and transformations.
3. Select chart form that answers the question without misleading axes or aggregation; use small multiples/table when too many series.
4. Make labels, units, uncertainty, source date, colors, and accessibility explicit; keep scales comparable across panels.
5. Check the rendered visual for clipped text, overlapping elements, unreadable legends, and unsupported annotations.
6. Explain what the figure can and cannot establish; for trading charts, separate descriptive backtest metrics from live performance.

## Focused support: chart choice

Choose the visual for the comparison, not for decoration: use a line or time-indexed points for ordered time; dots or intervals for estimates and uncertainty; bars for categorical magnitudes with a meaningful zero baseline; histograms or empirical distributions for spread; and scatterplots for paired relationships. Use a table when exact values or many categories matter more than pattern recognition. Use stacked parts only when the categories and denominator are defined and the total is meaningful.

Show units, denominator, period, source date, missingness, and uncertainty. Keep axes and scales comparable across panels; do not truncate an axis in a way that exaggerates differences. Distinguish observed values from modeled or illustrative values and never use chart shape alone to imply a causal mechanism. For trading data, label backtest and live observations separately and preserve price, return, and volume units.

## Scope guard

Visualize observed data accurately; label synthetic or illustrative values and do not imply causality from a chart.

If the requested method cannot be completed with available evidence or tools, return a bounded partial deliverable and name the precise gap. Do not replace a missing input with an invented value.
