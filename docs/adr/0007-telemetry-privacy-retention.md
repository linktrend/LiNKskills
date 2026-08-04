# ADR 0007 — Telemetry Privacy and Retention

- **Status:** Accepted
- **Date:** 2026-07-27
- **Decided by:** Principal, authorized via `docs/CURSOR-GROK-EXECUTION-PROMPT.md` and approved plan SHA-256 `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88` (`docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md` §17, §20.3)
- **Context source:** Plan §17 (telemetry/feedback/trace-to-eval), §5.3 / §19.4 (Brain correlation limits), ADR 0001 (telemetry in LiNKskills scope)

## Context

Current invocation telemetry records useful summaries but not the lifecycle needed for improvement, and cooperative JSONL/PostgREST writes can become a privacy hazard if Brain conversations, credentials, or large sensitive payloads are ingested. LiNKbrain owns private conversation memory; LiNKskills must not become a second memory store.

## Decision

**1. Canonical observable event spine (initial types):**

- `skill.requested`
- `skill.candidates_returned`
- `skill.selected` / `skill.not_selected`
- `skill.fragment_disclosed`
- `skill.run_started`
- `tool.resolved` / `tool.called` / `tool.completed` / `tool.failed`
- `artifact.produced`
- `verification.completed` / `verification.failed`
- `skill.run_completed` / `skill.run_failed` / `skill.run_abandoned`
- `feedback.submitted`
- `eval.candidate_created` / `eval.executed`
- `release.promoted` / `release.demoted` / `release.rolled_back`

**2. Event envelope includes:** event/schema version and event ID; actor, runtime, session, Program, repository, Issue/Run references where available; skill release and execution-profile hashes; tool release/hash where relevant; timestamp and sequence; outcome/failure classification; duration, token, tool, and cost metrics; safe artifact/evidence references; sensitivity/redaction classification; idempotency and correlation IDs.

**3. Retain by default:** identifiers, versions, lifecycle events, metrics, validations, error categories, artifact references/hashes, and explicit feedback.

**4. Do not retain by default:** hidden reasoning; credentials or authentication material; complete private conversations; unnecessarily large prompts/tool outputs; sensitive artifact bodies when a reference/hash is sufficient.

**5. No raw Brain conversations or private memory.** LiNKskills telemetry must never ingest raw LiNKbrain conversations, private Brain memory, checkpoints, or handoff content. Cross-service correlation uses opaque Brain task/activity IDs and approved outcome references only. LiNKbrain may record certified skill release/profile references; it must not copy Skill Packs, eval artifacts, or certification evidence into Skills telemetry paths.

**6. Buffering, cost, and redaction.** Batch ordinary events; flush on run close/failure when practical; use idempotent receipts and sequence cursors; cache catalog/fragments by hash; track payload bytes, rows, model calls, and estimated cost. Secrets and private content are redacted before evidence persistence. Trace-to-eval candidates store redacted minimal reproductions; the Librarian must not silently add contaminated/private raw content to eval fixtures.

## Consequences

- Gateway/adapters own lifecycle capture for operations they observe; cooperative-only telemetry is insufficient for launch.
- Privacy/redaction rules are part of Skill Pack declarations and schema enforcement, not optional consumer courtesy.
- Retention jobs and feature flags stay Skills-local and separate from Brain retention.
- Broad database credentials must not be distributed to ordinary consumers to “make telemetry work.”
