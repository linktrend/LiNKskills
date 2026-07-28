# ADR 0009 — Confined executor network + filesystem isolation (bounded deviation)

| Field | Value |
|---|---|
| Status | Accepted (bounded) |
| Date | 2026-07-28 |
| Wave | Correction waves 5–6 |
| Owners | LiNKskills Eval Runner / tool_runtime |

## Context

Codex finding: unrestricted subprocess/bash must be replaced with a fail-closed confined executor including network denial and real filesystem confidentiality (or fail closed when isolation cannot be proven).

## Decision

1. LiNKskills ships `linkskills_tool_runtime.confined_exec` as the only subprocess path for packaged tools and eval `execute.command` cases.
2. Confinement always includes: allowlisted env, realpath workspace boundary + symlink-escape rejection, argv-only (no shell / no `bash -lc`), and bounded time/CPU/output.
3. Network + filesystem isolation is attempted via OS wrappers:
   - macOS: `sandbox-exec` network-deny profile with **path-scoped** `file-read*` (canonical realpaths for workspace + runtime deps only — no global host file-read)
   - Linux: `bwrap --unshare-net` with `--tmpfs /` and explicit `--ro-bind` of runtime realpaths only — **never** `--ro-bind / /`
4. Default mode is **fail closed** when no wrapper can prove isolation (`LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=required`).
5. Local unit tests may set `LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven` so suites run without installing bubblewrap. Unproven runs stamp `network_isolation="unproven"` on sealed receipts.
6. Certification (`sealed_executor_receipt`) requires `network_isolation == "denied"`. `allow_unproven` must never produce a certifiable receipt.
7. macOS note: Apple dyld/shared-cache cannot boot under a pure path allowlist (process aborts before Python starts). Confidentiality is enforced by denying `/Users`, `/home`, `/Volumes`, and `/private/var/root`, then re-allowing only the workspace realpath and explicit `LINKSKILLS_EXECUTOR_EXTRA_RO_PATHS`. Linux uses a true allowlist via `bwrap --tmpfs /` + explicit `--ro-bind` roots (never `--ro-bind / /`).
8. **Out of scope for this wave:** a new containerized executor microservice or paid sandbox dependency. That remains a follow-up if CI/production hosts cannot provide `sandbox-exec`/`bwrap`.

## Consequences

- Production/canary hosts must provide an OS isolator or refuse live tool/eval command execution.
- ServerAdapter remains explicitly disabled until a remote profile is designed.
- No Platform contract change; this is Skills-local runtime hardening.
