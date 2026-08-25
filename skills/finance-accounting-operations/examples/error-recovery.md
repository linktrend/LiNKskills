# Example Trace: Contract or Authority Failure

## Synthetic scenario

An operator asks the skill to post an overdue invoice after the consumer
snapshot is stale and the contract lists an unknown write operation.

## Recovery

- The skill does not call Odoo, request credentials, or post the invoice.
- It returns `PENDING_APPROVAL`, identifies the stale digest and unknown
  operation, preserves the source reference, and names the consumer adapter or
  Principal as the owner of the next action.
- No report is presented as a final accounting, tax, audit, or legal result.
