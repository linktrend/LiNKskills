# Method-specific extension

## Applied method

1. Define whether the task is prediction, estimation, clustering, anomaly detection, or forecasting and identify the target/horizon.
2. Inspect provenance, missingness, label quality, class balance, duplicates, time/order/group relations, and feature availability at prediction time.
3. Create a simple baseline and select a validation split that matches deployment (temporal for future prediction; grouped when entities repeat).
4. Fit preprocessing inside the training pipeline; tune only within training data and keep a final holdout untouched.
5. Compare relevant models using decision-appropriate metrics, calibration/error analysis, subgroup behavior, and uncertainty.
6. Check leakage, drift, failure costs, and robustness; report limitations and what further data would change the recommendation.
7. State explicitly whether an output is a research prototype or deployable model; do not deploy or connect to trading execution.

## Scope guard

Treat model outputs as predictive or descriptive unless a causal design supports causality. No live trading or business action.

If the requested method cannot be completed with available evidence or tools, return a bounded partial deliverable and name the precise gap. Do not replace a missing input with an invented value.
