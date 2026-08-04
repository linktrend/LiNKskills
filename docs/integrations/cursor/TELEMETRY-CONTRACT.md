# Cursor Canary Telemetry Contract (Future Stage)

- **Date:** 2026-08-01
- **Owner:** LiNKskills (Lane C — project-scoped Cursor canary)
- **Status:** Documentation + contract tests only — **not** live stage telemetry
- **Live canary:** **false**
- **Global Cursor mutation:** **false**
- **Evidence tier:** contract / local-fake
- **Platform pin (read-only):** `421a35e97bc302be0f5e1f196d0a5e8d132f6fd8` (**certified candidate ≠ live**)
- **Envelope:** Frozen `platform.auth-token-envelope/0.1.0` (**not** `0.1.3-draft`)
- **Authoritative privacy ADR:** `docs/adr/0007-telemetry-privacy-retention.md`
- **Local buffer smoke:** `evidence/phase5/event-spine-smoke.json` (local/mock only)

## Purpose

Define what a **future** Platform-gated stage Cursor canary (Stages 4–8) must emit, redact, and idempotently deliver — without claiming live flush, stage PACI, or production telemetry today.

This packet expands readiness paperwork only. Stages 3–8 remain **blocked** on Platform stage PACI issuer + Skills credential.

## Scope boundaries

| In scope (docs/contract) | Out of scope (this packet) |
|---|---|
| Event names, envelope fields, privacy/redaction rules | Live Gateway telemetry flush |
| Idempotency-Key / event_id expectations | Supabase mutation / `lskills.telemetry` writes |
| Offline `LocalEventBuffer` recovery contract | Editing `~/.cursor/mcp.json` or global Cursor settings |
| Representative 10-skill set correlation IDs | Starting multi-day Stage 8 canary |

## Expected event spine (future stage canary)

Canonical observable types (ADR 0007), mapped to Gateway/MCP operations when live:

| Observable event | Typical Gateway / client path | Stage gate |
|---|---|---|
| `skill.requested` / `skill.candidates_returned` | `skills_search` / discovery | Stage 3+ (blocked) |
| `skill.selected` / `skill.not_selected` | consumer selection after discovery | Stage 3+ (blocked) |
| `skill.fragment_disclosed` | `skills_fragment_get` / `skills_describe` | Stage 3+ (blocked) |
| `skill.run_started` | `skills_run_start` | Stage 4+ (blocked) |
| `tool.resolved` / `tool.called` / `tool.completed` / `tool.failed` | `skills_tool_resolve` / `skills_tool_invoke` | Stage 5+ (blocked) |
| `artifact.produced` | run update / artifact refs only | Stage 5+ (blocked) |
| `verification.completed` / `verification.failed` | validate ops / eval runner receipts | Stage 5+ (blocked) |
| `skill.run_completed` / `skill.run_failed` / `skill.run_abandoned` | `skills_run_complete` / `skills_run_fail` / abandon | Stage 4+ (blocked) |
| `feedback.submitted` | `skills_feedback_submit` | Stage 4+ (blocked) |
| `eval.candidate_created` / `eval.executed` | `skills_trace_candidate_submit` / eval path | Stage 7+ (blocked) |

Local/fake buffer smoke uses shortened type names (`run_started`, `feedback_submitted`, …) in `evidence/phase5/` — those are **not** live stage receipts.

## Event envelope (required fields when live)

Every buffered or flushed canary event MUST carry:

1. `event_id` — UUID; stable across offline buffer rewrite and flush retries
2. `event_type` — from the spine above (or Gateway operation name for deferred flush)
3. `schema_version` / contract pin when persisted to stage stores
4. Actor / runtime / session identifiers (opaque; never bearer tokens)
5. Skill release / execution-profile hashes where available
6. Timestamp + sequence or correlation (`run_id`, `task_id`, Issue/Run refs)
7. Outcome / failure classification (category codes, not raw stack dumps with secrets)
8. Duration / cost metrics when measured (aggregates OK)
9. Sensitivity / redaction classification
10. Idempotency / correlation IDs (see below)

## Privacy / redaction (non-negotiable)

**Retain by default:** identifiers, versions, lifecycle events, metrics, validation outcomes, error categories, artifact references/hashes, explicit feedback ratings.

**Never retain / never emit:**

- Credentials, PACI private keys, access tokens, `Authorization` headers, SecretRef PEM bodies
- Raw LiNKbrain conversations, private memory, checkpoints, or handoff transcript bodies
- Unnecessarily large prompts / tool outputs when a hash or evidence path suffices
- Hidden model reasoning chains

**Redaction markers:** Sensitive fields MUST be replaced with `[REDACTED]` (or equivalent) before local buffer persistence and before any future stage flush. Proven locally via `evidence/phase5/event-spine-smoke.json` (`redaction_proven: true`, `brain_transcript_redacted: true`).

**Cross-service correlation:** Opaque Brain task/activity IDs and approved outcome references only — Skills must not become a second Brain memory store.

**Consumers:** Broad database credentials must not be distributed to Cursor/MCP just to “make telemetry work.” Canary path uses PACI-minted short-lived access tokens via `paci_stdio_proxy` only when Platform stage PACI exists.

## Offline buffer + flush expectations

| Path | Contract |
|---|---|
| Buffer | `packages/client` `LocalEventBuffer` → append-only JSONL (default `.linkskills_event_buffer.jsonl`) |
| Append | Each line: `event_id`, `event_type`, `payload`, `created_at`, `attempts` |
| Flush | Deferred `skills_feedback_submit` (and related ops) when Gateway reachable; batch ordinary events; prefer flush on run close/failure |
| Failure | Increment `attempts`; retain unsent lines; never drop silently without operator-visible status |
| Live status today | **Not live-proven** — Stage 4 telemetry remains blocked |

## Idempotency expectations (future stage)

1. **Client `event_id`:** Unique per logical observation; retries MUST reuse the same `event_id` for the same observation.
2. **HTTP `Idempotency-Key`:** Gateway mutating calls (`skills_run_*`, `skills_feedback_submit`, tool invoke, etc.) MUST send a stable key for retries; same key + same payload → replay/receipt; same key + different payload → conflict (`idempotency_conflict`).
3. **Downstream keys:** Tool invoke paths that mint downstream idempotency keys MUST remain stable across crash/retry (Gateway wave-9 contract).
4. **Sequence cursors:** When flushing buffered events, preserve order by `created_at` / sequence; do not invent duplicate lifecycle transitions for the same `run_id` without an explicit new run.
5. **No double-count:** Replayed receipts must not inflate Stage 8 multi-day metrics; evidence writers must prefer receipt IDs over raw attempt counts.

## Project-scoped canary binding

- Fragment: `configs/fragments/cursor-skills-canary.mcp.json.example`
- Apply steps: `docs/integrations/cursor/PACI-CLIENT-APPLICATION-HANDOFF.md` (project MCP only)
- Representative skill set: `evidence/phase1/canary-set.json` (10 skills; `live_canary: false`)
- Honesty status: `evidence/phase7/cursor-canary-status.json`
- Readiness summary: `evidence/stage-readiness/cursor-canary-readiness.json`
- Rollback: `docs/integrations/cursor/ROLLBACK.md` (project-scoped disable + git revert only)

## Honesty markers

- `live_canary: false` — this contract does not start Stage 4–8 telemetry
- `global_cursor_mutation: false` — no `~/.cursor/mcp.json` edits
- Certified Platform candidate pin ≠ live PACI / hosting / credentials
- Envelope remains `platform.auth-token-envelope/0.1.0` (do not advertise `0.1.3-draft` as live)
- Local buffer smoke ≠ stage telemetry ≠ production telemetry
