# Error recovery

If ownership or evidence is missing, return `DRAFT` with explicit uncertainty.
If a caller requests deployment, rollback, isolation, credential rotation,
sending, closure, or mutation, return `BLOCKED` with empty effects. Never echo
private incident text, credentials, customer data, or transport payloads.
