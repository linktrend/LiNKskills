# Sealed Linux evaluation gap (honest)

**Packet:** SKILLS-W20-STAGE-READINESS  
**Lane:** B  
**Evaluated host:** macOS Darwin (agent worktree `skills-w20-stage-readiness-cli`)  
**Date:** 2026-08-01

## Claim under test

Can this host produce certifiable executor receipts with `network_isolation=denied`?

## Result

**NO.** This macOS host **cannot** claim sealed `network_isolation=denied` certification.

## Evidence

1. Default confinement (`LINKSKILLS_EXECUTOR_NETWORK_ISOLATION` unset / `required`):
   - `run_confined([...])` raises `ConfinedExecutionError` — isolation unavailable; execution refused.
2. Soft local mode (`LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven`):
   - Probe stamps `network_isolation=unproven` (not certifiable).
3. Implementation contract (`confined_exec.py`):
   - Certifiable `denied` on Linux requires path-scoped `bwrap --unshare-net` (no host-wide `/` bind).
   - Darwin `sandbox-exec` path-allowlist often fails to boot (dyld/shared-cache); unavailable → never stamp `denied` for certification.
4. Classification honesty (`evidence/phase10/CLASSIFICATION-HONESTY.md`):
   - `macos_certifiable: false`; Linux `bwrap` required for usable/certified promotions.

## What would clear the gap

- A **non-paid-blocked** certifiable Linux (or already approved container/VM) evaluation host with proven `bwrap` path-scoped isolation, **or**
- Platform-supplied sealed receipt evidence from such a host.

This packet does **not** provision a paid Linux host and does **not** invent sealed receipts.

## Non-claims

- Do not treat unit tests that mint synthetic `network_isolation="denied"` as live sealed certification.
- Do not treat ephemeral Postgres migration proofs as isolation certification.
- Do not claim stage/prod sealed evaluation from this macOS lane run.
