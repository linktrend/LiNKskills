# Error recovery

If evidence is restricted, missing, malformed, or materially uncertain, return
`FAILED` or `PENDING_APPROVAL` with no private payload echoed. Preserve the last
confirmed value and correction history, identify the missing owner/configuration
receipt, and let the consumer decide whether to retry or roll back the draft.
