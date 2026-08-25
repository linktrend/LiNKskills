# Error recovery

If the purpose, owner, evidence, privacy class, or authority is missing, return
`PENDING_APPROVAL` and preserve the exact question. If raw transcript content is
present, fail closed without echoing it. Never infer a decision from silence or
send extracted minutes to a destination.
