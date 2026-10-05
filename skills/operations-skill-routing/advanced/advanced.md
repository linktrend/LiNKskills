# Operations Skill Routing: detailed procedure and variants

1. Identify the actual requested output and decision: capacity, mapping, vendor, knowledge, procurement, communications, SOP, risk, change or reporting.
2. Separate multiple requested jobs into bounded tasks with dependencies; a shared department label does not make tasks identical.
3. Select the matching admitted skill ID/version from LiNKskills, retrieve its entrypoint and needed support resources, and verify runtime availability.
4. Name Sara or the proper domain owner and route specialist work through exact retained identities; do not add permanent roles.
5. Record task ID, input gaps, handoff and acceptance criteria. If no admitted skill fits, report the gap for the Librarian rather than invent a callable tool.

## Legal routing additions from pinned task routers

Use these routes only when the current LiNKskills catalog contains the exact target pack. The router classifies the requested deliverable and hands off; it does not perform the legal work or treat upstream router text as authority. Source copies, per-skill declarations, and repository notice are retained in `references/upstream/SOURCE-MANIFEST.json`.

| Request shape | Route | Boundary |
| --- | --- | --- |
| Review a supplied commercial agreement against an approved playbook | `legal-commercial-review` | Return the requested contract review draft; a missing playbook does not get invented. |
| Analyze supplied agreement without a company playbook | `general-contract-risk-analysis` | Keep qualitative, evidence-linked issue spotting distinct from organization policy or legal opinion. |
| Evaluate proposed replacement clauses or deal changes | `legal-commercial-review-proposals` | Prepare options and rationale only; do not negotiate, send, or alter the source agreement. |
| Ask what a current statute or regulation means | `legal-borghei-statute-analysis` for statute/regulation interpretation, `legal-lawve-assistant-juridique-christophe-quezel-ambrunaz` for its France-based French/EU research scope, or `legal-lawve-employment-law-research-yue-deng-wu` for employment-law research | Require the relevant jurisdiction and as-of date when material. A dated source is not proof of current law. Route regulatory monitoring requests separately to `legal-regulatory-reg-feed-watcher`. For any other jurisdiction/topic with no exact cataloged research task, report a routing gap. |

If a request combines drafting, review, and legal research, split it into the corresponding deliverables and record their dependencies. Do not draft or interpret inside this router. If no exact admitted task fits, identify the gap and route it to the Librarian; do not substitute a merely related legal skill.

## Source comparison

This source is a router, not a replacement umbrella skill. Its six dependencies are independently preserved.

## Failure recovery

On missing evidence, preserve known answers and isolate the affected conclusion. On conflicting evidence, record both source dates and ask the accountable owner to reconcile. On tool denial, use an authorized Sara-mediated extract or report operation/owner/error; never bypass the boundary. On a failed draft write, inspect the actual write result and readback before retry to avoid duplicates. On an unavailable specialist, retain the assignment and dependencies; Sara may do bounded work within her role but cannot invent the specialist review.
