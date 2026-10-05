# Queued Service Capacity Sizing: detailed procedure and variants

1. Confirm this is queued service work rather than roadmap/commitment allocation. Select one compatible service class; separate priority classes and shared-provider constraints. Record observed period, timestamp/data quality, arrival distribution and accepted completion definition.
2. Measure arrival rate lambda and per-active-worker service rate mu in the same time unit. Show P50/P90/P99 observed demand separately; disclose forecast-derived demand when history is missing. Unknown demand distribution limits waiting-risk claims rather than justifying guessed certainty.
3. Calculate effective active service capacity after actual availability/shrinkage, separately from roster count. For AI workers use observed accepted completion rate, failures/rework, provider limits and concurrency; human hiring/ramp assumptions apply only to human capacity. Never apply a default human utilization threshold as an agent rule.
4. Use Erlang-C only when a steady-state M/M/s approximation is justified: stationary arrivals, exponential service approximation, interchangeable parallel workers and a pooled compatible queue. Compute offered load a=lambda/mu and rho=lambda/(s*mu). If rho>=1 report an unstable steady-state queue; do not report a finite steady-state wait.
5. For rho<1 compute C=(a^s/(s!*(1-rho)))/(sum(k=0..s-1,a^k/k!)+a^s/(s!*(1-rho))). Then P(wait>t)=C*exp(-(s*mu-lambda)*t) for a queue-wait objective t in the same units. Keep formula-model predictions distinct from measured breach rates and end-to-end service objectives.
6. Compare observed demand scenarios and active worker counts with wait, utilization, effective throughput, costs and assumptions. If distribution, priority or burstiness invalidates M/M/s, report the limitation and use observed queue/wait data for a bounded empirical recommendation; do not relabel it Erlang-C proof.
7. Where additional capacity is proposed, sequence ramp/availability and any human attrition evidence over the planning horizon. Return decision owner, source register, monitoring triggers and no-change alternative; no provisioning, hiring or spend enacted.

## Source comparison

Preserved separately: queued-service arrival/wait-risk sizing differs from project/commitment cut-line allocation even though both involve capacity.

## Failure recovery

On missing evidence, preserve known answers and isolate the affected conclusion. On conflicting evidence, record both source dates and ask the accountable owner to reconcile. On tool denial, use an authorized Sara-mediated extract or report operation/owner/error; never bypass the boundary. On a failed draft write, inspect the actual write result and readback before retry to avoid duplicates. On an unavailable specialist, retain the assignment and dependencies; Sara may do bounded work within her role but cannot invent the specialist review.
