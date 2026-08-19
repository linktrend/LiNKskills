# Error recovery

When evidence is stale or contradictory, mark the result `awaiting-check-in`,
retain the prior observations, and ask for the smallest fresh report needed.
Never produce a false threshold alert from a guessed rate.
