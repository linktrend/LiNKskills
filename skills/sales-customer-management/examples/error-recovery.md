# Safe error recovery example

For a synthetic pipeline request, the owning integration receipt is absent. The skill returns `PENDING_APPROVAL` (or `FAILED` when the request is malformed), labels the capability as `blocked`, records the receipt reference as unavailable, and names the owner as the next action. It does not guess a stage, retry a write, call Odoo, or send a follow-up. Rollback discards the unapproved draft and points to the prior qualified release.
