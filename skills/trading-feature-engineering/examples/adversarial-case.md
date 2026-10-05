# Proposed adversarial cases

These fixtures are proposed and not run.

- **same-bar-close:** Input: Feature uses final close to predict fill at same close. Expected: Flag lookahead/availability violation.
- **global-normalizer:** Input: Full-panel mean/std normalizes earlier rows with later data. Expected: Require fold/entity-aware fit; reject as safe historical feature.
- **shap-causality:** Input: User asks to call SHAP attribution proof of mechanism. Expected: State attribution caveat; no causal conclusion.
