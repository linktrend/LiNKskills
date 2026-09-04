# Advanced routing

If two routes tie, do not load both automatically. Prefer an explicit user route; otherwise return `AMBIGUOUS` with at most two alternatives. Cross-family precedence is defined by the initial seed routing policy, not by keyword count alone.
