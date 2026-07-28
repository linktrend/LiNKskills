# ADR 0009 — Confined executor network + filesystem isolation (bounded deviation)

| Field | Value |
|---|---|
| Status | Accepted (bounded) |
| Date | 2026-07-28 (amended 2026-07-29 wave 7) |
| Wave | Correction waves 5–7 |
| Owners | LiNKskills Eval Runner / tool_runtime |

## Context

Codex finding: unrestricted subprocess/bash must be replaced with a fail-closed confined executor including network denial and real filesystem confidentiality (or fail closed when isolation cannot be proven).

Wave-6 macOS Seatbelt used global `(allow file-read*)` plus a short deny list. That incorrectly stamped `network_isolation="denied"` while secrets under `/var/folders` remained readable.

## Decision

1. LiNKskills ships `linkskills_tool_runtime.confined_exec` as the only subprocess path for packaged tools and eval `execute.command` cases.
2. Confinement always includes: allowlisted env, realpath workspace boundary + symlink-escape rejection, argv-only (no shell / no `bash -lc`), and bounded time/CPU/output.
3. Network + filesystem isolation is attempted via OS wrappers:
   - **Linux:** `bwrap --unshare-net` with `--tmpfs /` and explicit `--ro-bind` of runtime realpaths only — **never** `--ro-bind / /`. This is genuine path-allowlisted confinement and may stamp `denied`.
   - **macOS:** only a **pure path-allowlist** Seatbelt profile (no bare `(allow file-read*)`) may stamp `denied`, and only after a boot probe succeeds. Current macOS dyld/shared-cache typically aborts under pure allowlists; when the probe fails, isolation is `unavailable` / stamped `unproven` — **never** `denied`.
4. Deny-list / global-read Seatbelt profiles are **forbidden** for certifiable receipts. Partial network-deny without proven FS confidentiality must not claim `denied`.
5. Default mode is **fail closed** when no wrapper can prove isolation (`LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=required`).
6. Local unit tests may set `LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven` so suites run without bubblewrap / without a bootable macOS allowlist. Unproven runs stamp `network_isolation="unproven"` on sealed receipts.
7. Certification (`sealed_executor_receipt`) requires `network_isolation == "denied"`. `allow_unproven` must never produce a certifiable receipt.
8. Adversarial coverage must include reads from macOS temporary/cache/system/user locations outside approved roots (`/var/folders`, `~/Library/Caches`, home files, etc.) whenever isolation claims `denied`.
9. **Out of scope for this wave:** a new containerized executor microservice or paid sandbox dependency. That remains a follow-up if CI/production hosts cannot provide bootable allowlist isolation (`bwrap` / container / VM).

## Consequences

- Production/canary hosts that need certifiable receipts must provide proven path-allowlisted isolation (today: Linux `bwrap`, or a future container/VM). macOS `sandbox-exec` without a bootable allowlist cannot certify.
- ServerAdapter remains explicitly disabled until a remote profile is designed.
- No Platform contract change; this is Skills-local runtime hardening.
