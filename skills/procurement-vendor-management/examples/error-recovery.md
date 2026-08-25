# Error recovery

If an owner capability receipt is missing or expired, return `PENDING_APPROVAL` or
`FAILED`, identify the missing receipt without guessing supplier state, preserve only
synthetic evidence references, and discard the unapproved draft on rollback.
