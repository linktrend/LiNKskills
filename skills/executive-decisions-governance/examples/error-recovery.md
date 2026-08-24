# Synthetic fail-closed patterns

- Missing evidence returns `BLOCKED`; the helper does not invent support.
- A choice set without `Other — specify` returns `BLOCKED` unless explicitly
  marked exhaustive by the owner.
- An approval record can be captured only with a named owner and choice; it
  remains inactive and emits no effects.
- Activation, enforcement, sending, scheduling, task creation, or unknown
  actions return `BLOCKED` and empty effects.
- Private identifiers, credentials, customer records, and confidential input
  are rejected without echoing the supplied value.
