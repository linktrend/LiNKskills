# Agent production operations cards

## Assignment boundary

Use only for an already-built agent whose owner requests operational monitoring or a draft runtime-control plan. This task consumes readiness, evaluation and incident evidence; it does not build the agent, run eval design, define company-wide SLOs or security controls, execute a rollout, grant authority, disable runtime, or replace incident-learning (which owns postmortem/verified closure). Sara may analyze approved operational evidence and prepare proposals. Eric owns technical interfaces, reliability instrumentation, runtime controls and any execution.

## 1. Establish operating contract

Record agent/version/model and release identity; use case and user population; autonomy class (read-only, internal side-effect capable, customer-facing); exact delegated action/resource/data scope; approved source of authority; data sensitivity; owner/on-call/escalation contact; tools and their read/write effects; approved fallback; current readiness/evaluation evidence; known user-impact constraints. Treat an attempted out-of-scope action as an incident signal. Unknown contract fields remain explicit blockers—do not infer authority.

## 2. Baseline quality and service conditions

Use a named evaluation/release baseline and measurement window. Inventory available evidence for task success/correctness, policy/authority breaches, abstention/handoff, tool call success and error classes, p50/p95 latency, completion time, cost per run and total spend. For each metric record definition, numerator/denominator, cohort, exclusions, data source, sample size, freshness and owner-approved threshold. Separate sampled traces from population metrics. If quality labels or consented human review are absent, report quality as unmeasured rather than infer it from latency or tool completion. Avoid sensitive content in telemetry; minimize/redact identifiers as policy requires.

## 3. Staged change plan

Compare candidate and current version by exact immutable identity, change scope, impact/risk, prior task-specific eval, canary population and time window. Define who may approve each stage, allowed authority at each stage, observable stop conditions, fallback route, rollback owner, and evidence required to expand. Use only thresholds recorded in approved owner policy or the release contract; do not copy numeric values from the upstream example table as LiNK policy. If no rollout/rollback interface is available, return a plan and capability gap, do not attempt traffic changes.

## 4. Monitor and interpret evidence

For the declared period/cohort, compare observed metrics with approved baselines and thresholds. Check trend, sample size and measurement comparability; identify outages, tool/schema failures, quality regressions, authority attempts, privacy/security signals, escalations, cost/latency deviations and fallback use. Separate event facts from causal hypotheses. For a material finding capture exact record/trace refs, observed window, metric definition, affected cohort, user/business impact, confidence, and missing evidence. Do not claim a trend from insufficient samples.

## 5. Escalation and fallback recommendation

Map each observed condition to the named owner and pre-agreed response. Business-quality or user-impact issue -> Sara/operator for disposition; runtime/controller, instrumentation, security, deployment or provider issue -> Eric/technical owner; legal/privacy/regulatory issue -> Carlos/counsel as named. A draft recommendation may be hold expansion, route to read-only, reduce scope, pause, or rollback only where owner policy provides that action. The skill cannot enforce or send the escalation. If there is immediate user safety/security impact, provide exact evidence and urgent owner route available in the current interface.

## 6. Trace-to-evaluation learning loop

Select a minimized, authorized trace or incident record; link the observed failure mode to a task/eval case proposal, expected behavior, severity rationale and regression condition. Retain enough non-sensitive context to reproduce without retaining raw private data unnecessarily. Report candidate eval additions to the owner of the approved eval suite. Production traces are evidence, not automatically valid labels, permission grants or evaluation data. Incident investigation and postmortem closure remain with `incident-learning`.

## 7. Operational status report

Return: agent/version/cohort/window; approved baseline and source; per-metric observed vs threshold (or `unavailable`); quality evidence and sample caveats; tool health; authority/fallback signals; issues with records; distinction of fact/hypothesis; risk and impact; recommended owner action; rollout stage recommendation; exact approval and capability gaps. Explicitly state whether any change was actually performed (normally none).

## Source method integration

The retained source defines a runtime-control plane across autonomy profiles, authority contracts, release stages, cost/latency/tool-health budgets, fallback/disablement and trace-to-evaluation feedback. The active procedure keeps that cross-domain operating shape, adds explicit metric definition/sample caveats, evidence provenance and role ownership, and removes fixed thresholds as defaults. It routes incident postmortem to `incident-learning`, technical instrumentation/control execution to Eric, eval-suite ownership to the Librarian/authorized evaluator, and rollout readiness to the designated release owner. Source scripts/commands/control actions are reference content only, never callable Lisa interfaces.
