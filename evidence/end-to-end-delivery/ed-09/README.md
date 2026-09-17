# ED-09 evidence framework (templates only)

This directory is the LiNKskills-owned canary evidence surface. It prepares
machine-readable **blank** receipts for the ordered consumers Cursor → Codex →
Lisa/OpenClaw. It does **not** run a canary, contact providers, mutate consumer
configuration, or claim functional or internal-launch acceptance.

## Status of this checkpoint

`FRAMEWORK_ONLY_NOT_ACCEPTED`. Every observational field is unfilled. Later
executors fill these templates in place. No status may become
`FUNCTIONAL_ACCEPTED` or `INTERNAL_LAUNCH_COMPLETE` until **all** required
gates below are independently proven at compatible identities.

## Required gates before any acceptance status

All of the following are blocking. Missing, fabricated, or incompatible
evidence keeps every acceptance field `HOLD` / `false`.

1. **Real ED-08 production PASS** at
   `evidence/end-to-end-delivery/ed-08/deployment-receipt.json` (live `/ready=200`,
   exact image/source identity, rollback rehearsal). Planning PASS is not enough.
2. **Exact identity pins** for repository/ref/commit/tree, provider image/release,
   ED-05 consumer pins/digests, Platform auth audience `lskills-api` / scope
   `lskills`, and the five initial releases only.
3. **Negative-path results** for wrong identity/scope, revoked release,
   tampered or stale cache, provider outage, store outage, and
   consumer-disable, each fail-closed with no unsafe fallback.
4. **48-hour Cursor observation** spanning at least two Asia/Taipei calendar
   dates, with start, midpoint, and end availability/failure/cost/non-disruption
   evidence. Continuous paid activity is not required.
   `INTERNAL_LAUNCH_COMPLETE` stays HOLD until this closes.
5. **OSS continuity evidence** that Server 01 reused the inventory in
   `docs/end-to-end-delivery/OSS-INVENTORY.md` (no extra runtime, database,
   identity, or monitoring stack).
6. **Owner receipts** from the consumer owners (project-scoped Cursor /
   XP-02 only if a shared Cursor mutation is required; XP-03 Codex; XP-04
   Lisa/OpenClaw) bound to the same pins.

## Ordered execution (later, not this checkpoint)

1. Cursor representative flow: discover → retrieve → verify → local execute →
   report, plus one negative case.
2. Codex only after Cursor **functional flow** PASS at compatible identities.
3. Lisa only after Codex functional flow PASS.
4. `FUNCTIONAL_ACCEPTED` only after all three functional flows PASS.
5. `INTERNAL_LAUNCH_COMPLETE` only after functional acceptance **and** the
   48-hour Cursor observation.

This packet records none of those executions.

## Files

| File | Role |
|---|---|
| `framework.json` | Gate contract, order, prohibited actions, fail-closed rules |
| `ed-08-prerequisite.json` | Blank ED-08 production PASS binding |
| `identity-pins.json` | Blank exact identity/pin slots |
| `cursor-canary-receipt.json` | Blank Cursor functional receipt |
| `codex-canary-receipt.json` | Blank Codex functional receipt |
| `lisa-canary-receipt.json` | Blank Lisa/OpenClaw functional receipt |
| `negative-path-matrix.json` | Required negative cases, all `NOT_EXECUTED` |
| `cursor-48h-observation.json` | Blank 48-hour / two-date observation |
| `oss-continuity.json` | Blank OSS reuse/continuity slots |
| `owner-receipts.json` | Blank owner receipt slots |
| `reconciliation.json` | Blank cross-surface proof-class slots |
| `founder-walkthrough.json` | Blank founder walkthrough inputs |
| `final-acceptance.json` | Machine-readable HOLD; not an acceptance claim |

## Prohibited in this packet

Product, Skill, migration, deploy, and `configs/consumer-activation/` edits;
provider contact; live canary; nested workers; implementer PR/merge; secrets;
fabricated PASS/FAIL results.
