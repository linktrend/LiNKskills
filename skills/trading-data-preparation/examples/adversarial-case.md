# Proposed adversarial cases

These fixtures are proposed and not run.

- **dst-session:** Input: Bars span DST transition and session close. Expected: Use source timezone/calendar; expose duplicate/nonexistent local times and incomplete session.
- **coarse-split:** Input: Only hourly OHLCV provided but five-minute bars requested. Expected: Refuse fabricated fine bars.
- **futures-adjustment:** Input: Adjusted futures series requested for executable fill price. Expected: Keep adjusted analytic series distinct; use raw contract marks for fills.
