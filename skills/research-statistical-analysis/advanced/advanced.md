# Method-specific extension

## Applied method

1. Define the estimand, unit of analysis, target population, design, and decision before choosing a test.
2. Inspect data shape, missingness, duplicates, outliers, dependence, group structure, temporal ordering, and measurement quality; do not silently drop observations.
3. Choose a method suited to outcome type, design, assumptions, and sample; consider robust, nonparametric, clustered, longitudinal, or Bayesian alternatives when warranted.
4. Check assumptions and diagnostics; make planned transformations, exclusions, and multiplicity treatment explicit.
5. Report estimate, effect size, interval or other uncertainty measure, sample counts, and practical relevance; distinguish statistical from practical importance.
6. For power/sample size, expose the assumed effect, variance, alpha, power, design, and sensitivity; do not present an unsupported point estimate as a guarantee.
7. Separate observed association from causal claim; state the strongest plausible alternative explanation and analysis limits.

## Scope guard

Report computations and assumptions only when actual input data and an available method support them. Never invent a p-value, effect, interval, or confidence score.

If the requested method cannot be completed with available evidence or tools, return a bounded partial deliverable and name the precise gap. Do not replace a missing input with an invented value.
