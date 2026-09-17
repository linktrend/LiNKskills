# Repository Ownership Matrix

- **Status:** Accepted (Phase 0; adapted from plan §29.2)
- **Date:** 2026-07-27
- **Authority:** `docs/CURSOR-GROK-EXECUTION-PROMPT.md` + approved plan hash `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`
- **Plan refs:** §29.1–29.2, ADR 0001, ADR 0008

## Ownership principles (summary)

1. Domain defines and implements its domain.
2. LiNKplatform owns shared foundations and live operations.
3. Consumer repository owns its internals.
4. Contract producer validates the consumer.
5. No casual cross-repository editing without a named work packet.
6. Plans control execution; deviations stop and escalate.
7. Verification is independent (Codex); Grok reports are provisional.

## Matrix

| Work or mutation surface | LiNKskills agent | LiNKplatform agent | LiNKbrain agent | OpenClaw Prime agent |
|---|---|---|---|---|
| Skill Pack / tool / eval / certification contracts and implementation | **Own/implement** | Consume/host support | No change | Consume |
| LiNKskills Gateway, `skills_*` MCP/API, client, tests | **Own/implement** | Auth/infrastructure support | Separate Brain service | Consume adapter contract |
| Canonical actor identity, organisations, shared token/credential issuer | Supply claim requirements/tests | **Own/implement/operate** | Supply Brain requirements/tests | Consume |
| LiNKskills actor/runtime/run bindings | **Own; reference platform actor ID** | Supply canonical ID | No change | Supply runtime context |
| `lskills` migrations and policies | **Author/test/package** | **Review/sequence/apply/operate live** | No change | No change |
| Shared stage/production migration execution | Must not apply independently | **Sole live owner** | Must not apply independently | No change |
| Published bundle storage conventions/operation | Define bundle and publication behavior | Provide/operate approved storage | Separate Brain storage | Consume |
| Real Eval Runner | **Own/implement** | Hosting/credential support if approved | No change | Runtime-profile fixtures |
| LiNKskills Librarian domain worker | **Own logic/contracts/tests** | Integrate/host/schedule | Own separate Brain worker | No change |
| Generic Librarian host and existing `packages/librarian-runner` shared files | Consume via versioned contract | **Sole integration/implementation owner** | Consume via versioned contract | No change |
| Cursor LiNKskills product canary | **Own, prefer project scope** | Identity/credentials | No Brain Phase 1 production rollout | No change |
| Shared/global Cursor environment used by all Grok agents | No change except approved maintenance-gated canary mutation | No change | No change | No change |
| Shared Codex host configuration for this rollout | Supply separate Skills fragment/tests; validate | Identity/credentials | **Default integration owner** | No change |
| OpenClaw/Lisa MCP, plugins/modules, hooks, buffers, mapping, profile, tests, rollout | Contract/fragment/fake/conformance/validation only | Identity/credentials/hosting | Separate Brain contract/validation | **Sole implementation/live owner** |
| Program permission, Issues, Runs, gates, deployments | Never | Capability foundation only | Never | Respect Program/host authority |

## Explicit non-ownership (LiNKskills)

- Program leases, entitlements, kill-switches, financial ledgers, disclosure tokens (ADR 0001).
- Live shared migration application.
- Shared Codex host configuration edits.
- OpenClaw/Lisa internals and Lisa’s authoritative profile.
- Competing organisation-wide actor identity authority.
- Independent edits to `LiNKplatform/packages/librarian-runner` shared files.
