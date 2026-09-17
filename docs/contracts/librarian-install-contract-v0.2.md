# Librarian install contract v0.2 (LiNKskills-owned)

**Status:** source contract; not live scheduled.
**Worker pin:** `linkskills-librarian` **0.2.0** / `DomainWorker.version=0.2` / `linkskills-librarian-conformance/0.2`.
**Host:** LiNKplatform `packages/librarian-runner` — **do not edit LiNKplatform from this packet**.

Machine copy: `configs/librarian/install-contract.json`.

## Supervised-first acceptance

1. Host loads this worker by version pin, not latest main.
2. First production passes are dry-run / supervised. `enabledDefault=false`.
3. Prompt-only eval evidence is non-certifying (ADR 0006).
4. Protected branch push proposals are refused by the worker.
5. Cross-domain (Brain) payloads are rejected.
6. Max retries = 3; then dead-letter. Regressions hold `eval_pending`; they are never auto-`usable`.

## Scheduling inputs (names only)

Suggested Asia/Taipei windows `07:30` and `19:30`. Platform owns cron, credentials, and alerts. Skills does not invent GSM project IDs.

## Monitoring / alert contract

Emit job depth, dead-letter count, prompt-only rejects, and regression holds. Alert on dead-letter, prompt-only certification attempts, protected-branch push, and cross-domain payload. Principal briefing is a Platform host route, not a Skills-sent business message.

## Platform handoff after the current identity task

When Platform's OpenClaw identity registration work is finished (concurrent; do not interfere):

1. Integrate worker 0.2 into `librarian-runner` without Skills editing that repo.
2. Keep OpenClaw Lisa/David/Eric/Sara/Jane PACI registration as Platform/Server01-owned.
3. Do not enable unsupervised remainder certification until hosted sealed receipts exist for the 54.
4. Apply `20260915031801_lskills_provider_v2_runtime.sql` only on Server01.

This file does not close Platform issues and does not claim live Librarian.
