# Success pattern

For a synthetic outage with a confirmed incident reference, responder, Platform
owner, observed impact, proposed restore option, and draft internal update,
return `READY_FOR_OWNER`. Preserve each evidence reference, keep `sent` false,
keep all effects empty, and leave deployment and Program Ledger mutation to the
owning authorities.
