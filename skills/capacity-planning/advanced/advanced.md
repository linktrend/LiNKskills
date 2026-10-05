# Capacity Planning: detailed procedure and variants

1. Establish project/commitment scope, comparable deliverable units, horizon and approved priorities. Use actual role/skills, shared agent concurrency/provider quotas, human availability and observed throughput; do not sum incompatible units or reuse the same shared pool twice.
2. Calculate supply before fitting demand. For human capacity show gross period hours minus booked absence/on-call/overhead and ramp factors; for agent capacity show observed accepted throughput, quota/concurrency and availability. Mark proposed factors and never substitute upstream benchmark percentages for measured/company-approved inputs.
3. List each commitment with accountable owner, required discipline/capability, estimate/uncertainty, priority, dependencies and externally-promised status. Verify whether risk adjustment or reserve is already included; apply each at most once.
4. Allocate whole commitments in approved priority/dependency order against independently established effective capacity. Publish the exact cut line, unscheduled commitments, remaining capacity and skill bottlenecks. Split work only if the owner permits a divisible deliverable; an aggregate shortfall is not permission to partly execute an atomic commitment.
5. Escalate an externally promised commitment that does not fit with evidence, owner and decision deadline. Do not silently assume extra workers, quota, new hires or acceptable late delivery.
6. For below-the-line work compare defer, reallocation, contracted or added capacity by time to relief, verified recurring/one-time cost, ramp, reversibility and knowledge continuity. Distinguish measured gains from projections and include the no-change alternative.
7. Return current allocation table, cut-line report and scenario recommendation with sources, uncertainty, owner approvals, monitoring and replan triggers. Eric retains engineering execution priority; Sara supplies operating capacity advice.

## Source comparison

Same project/commitment capacity task: Borghei effective-capacity -> priority cut-line -> hire/contract/defer is the base; incorporate Anthropic project horizon, people/budget/time constraints and comparative scenarios. Alireza queued service sizing is a separate task.

## Failure recovery

On missing evidence, preserve known answers and isolate the affected conclusion. On conflicting evidence, record both source dates and ask the accountable owner to reconcile. On tool denial, use an authorized Sara-mediated extract or report operation/owner/error; never bypass the boundary. On a failed draft write, inspect the actual write result and readback before retry to avoid duplicates. On an unavailable specialist, retain the assignment and dependencies; Sara may do bounded work within her role but cannot invent the specialist review.
