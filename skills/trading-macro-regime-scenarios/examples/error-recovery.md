# Missing-input recovery

When a required field in `trading-macro-regime-scenarios` is absent, do not infer it from a ticker, screenshot, stale cache, or another source. Return `completion_status: insufficient_input` when the task cannot be meaningfully answered, or `partial` when independent fields still support a bounded result. Name the exact missing fields and keep unaffected analysis separate.

Example: for the fixture schema, removing a required as-of date must not cause the skill to imply that values are current. Report that the as-of date is missing and omit time-sensitive conclusions. This recovery description is a proposed acceptance criterion; no behavioral pass is claimed.
