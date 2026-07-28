# ADR 0009 — Confined executor network isolation (bounded deviation)

| Field | Value |
|---|---|
| Status | Accepted (bounded) |
| Date | 2026-07-28 |
| Wave | Correction wave 5 |
| Owners | LiNKskills Eval Runner / tool_runtime |

## Context

Codex finding: unrestricted subprocess/bash must be replaced with a fail-closed confined executor including network denial (or fail closed when isolation cannot be proven).

## Decision

1. LiNKskills ships `linkskills_tool_runtime.confined_exec` as the only subprocess path for packaged tools and eval `execute.command` cases.
2. Confinement always includes: allowlisted env, realpath workspace boundary + symlink-escape rejection, argv-only (no shell / no `bash -lc`), and bounded time/CPU/output.
3. Network isolation is attempted via OS wrappers:
   - macOS: `sandbox-exec` network-deny profile
   - Linux: `bwrap --unshare-net` preferred; `unshare --net` fallback
4. Default mode is **fail closed** when no wrapper can prove network denial (`LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=required`).
5. Local unit tests may set `LINKSKILLS_EXECUTOR_NETWORK_ISOLATION=allow_unproven` so suites run without installing bubblewrap. Certification still requires trusted Eval Runner issuer HMAC on receipts.
6. **Out of scope for this wave:** a new containerized executor microservice or paid sandbox dependency. That remains a follow-up if CI/production hosts cannot provide `sandbox-exec`/`bwrap`.

## Consequences

- Production/canary hosts must provide an OS network isolator or refuse live tool/eval command execution.
- ServerAdapter remains explicitly disabled until a remote profile is designed.
- No Platform contract change; this is Skills-local runtime hardening.
