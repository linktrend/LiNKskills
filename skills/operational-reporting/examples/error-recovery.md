# Error recovery

If a required source is unavailable, mark the report incomplete or
`PENDING_APPROVAL`, identify the missing source, and do not fill the gap with
inference. If delivery fails, preserve the report and retry only under the
consumer's retry policy.
