# Proposed adversarial cases

These fixtures are proposed and not run.

- **same-close-fill:** Input: Final close used as signal and fill without intrabar timestamp. Expected: Move fill to first eligible subsequent observation or explicitly model known-at path.
- **holdout-reuse:** Input: Tune parameters after repeated holdout inspection. Expected: Mark holdout contaminated; require new untouched period.
- **cost-units:** Input: Spread bps added to dollar P&L as raw decimal. Expected: Reject dimensional mismatch and retain partial status.
