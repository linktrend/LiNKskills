# Operational Runbook: detailed procedure and variants

1. Name the scenario, entry symptoms, severity/impact criteria, current baseline and response owner.
2. List safe verification steps before action. Check actual tool contracts and required access; unavailable tools become an explicit readiness gap.
3. Draft ordered response steps with actor, command or business action, expected observation, stop condition and authorized consequence.
4. Include escalation, communication, fallback and recovery with rollback triggers; no production commands are executed while authoring.
5. Simulate the normal and failed response using fictional observations. Record recovery verification and improvements needed before approval.

## Source comparison

Preserved separately from general SOP writing: a runbook responds to a specific operational scenario.

## Failure recovery

On missing evidence, preserve known answers and isolate the affected conclusion. On conflicting evidence, record both source dates and ask the accountable owner to reconcile. On tool denial, use an authorized Sara-mediated extract or report operation/owner/error; never bypass the boundary. On a failed draft write, inspect the actual write result and readback before retry to avoid duplicates. On an unavailable specialist, retain the assignment and dependencies; Sara may do bounded work within her role but cannot invent the specialist review.
