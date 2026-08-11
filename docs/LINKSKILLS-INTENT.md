# LiNKskills — Intent

> **Current state, 2026-08-11:** The Skills service and native Lisa bridge are
> live and healthy on the VPS. Repository integration branches include the
> current IDE Development rollout. Exact deployed-source equality still needs
> a SHA receipt whenever the Skills checkout is next audited or deployed.

**Status:** Confirmed Intent for the LiNKskills Program itself (this repository), written in the same spirit as LiNKdeveloper's Intent artifact — a plain-English statement of what is being built, why, for whom, and what "done" means. Grounded in the **approved internal-launch architecture now being implemented** (plan hash below), not only the narrower 2026-07-19 git-checkout catalog surface.

**Audience:** The Principal (sole human authority) and any agent across any Program that needs to understand *why this library exists* before reading the Technical PRD.

**Companion document:** [`LINKSKILLS-TECHNICAL-PRD.md`](./LINKSKILLS-TECHNICAL-PRD.md) — exhaustive how-it-works reference.

**Approved plan (execution authority for architecture):** [`LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md`](./LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md) — SHA-256 `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`. ADRs **0001–0008** are accepted alongside that plan.

---

## 1. Problem

LiNKtrend is an AI-native venture studio. Every Program (LiNKsites, LiNKdeveloper, LiNKbrain, and future Programs) runs agents that need reusable, progressive-disclosure skills — not one-off prompts pasted into chats.

Without a shared library:

- Each Program reinvents the same skill shapes, validators, and telemetry.
- Quality is self-declared ("this prompt worked once") instead of proven by a real eval runner against executed cases.
- Usage is invisible — failures, HITL friction, and cost outliers never feed a curation loop.
- Delivery drifts between "whatever is checked out locally" and a published, certified release.
- A previous design attempt bolted a **governance / permission-to-act** plane onto this repo (the retired Logic Engine). That was the wrong home for entitlements, leases, kill-switches, and per-tenant policy.

The problem LiNKskills solves is: **give every studio agent one shared, versioned, quality-gated skill catalog — published through a LiNKskills Gateway (MCP/HTTP), with mandatory real eval proof and usage telemetry — without owning whether any Program may act.**

---

## 2. Who it is for

| Role | Relationship to LiNKskills |
|---|---|
| **Principal (Carlos)** | Sole human authority. Reviews escalated Librarian proposals when auto-promotion criteria are not met. Does not author skills day to day. |
| **Every agent across every Program** | Primary consumer. Discovers and loads certified skill content through the LiNKskills `skills_*` MCP / HTTP Gateway (and SDK client). Direct `lib/skill_runtime` git-checkout loading remains a **compatibility / migration** path only. |
| **Librarian** | Curation agent. Skill-side instructions live in `skills/self-improvement`; domain worker contracts live in `packages/librarian_domain`; the generic runnable host lives in `LiNKplatform/packages/librarian-runner`. |
| **Skill authors (agents)** | Create/refine skills via `skill-architect` / `skill-template`, validated by `validator.py`, published into immutable bundles. |

LiNKskills is **not** a customer-facing product. It is LiNKtrend's internal skill library Program. **LiNKbrain remains a separate service** (`brain_*`); there is no combined Brain/Skills Gateway.

---

## 3. What "done" looks like (Program-level)

Studio-level "library done" for the **internal-launch** scope means:

1. Editable Skill Packs under `skills/` keep the progressive-disclosure shape and a baseline `references/eval-suite.yaml`.
2. Domain packages under `packages/` implement contracts, core policy, publisher, real Eval Runner, tool runtime, Gateway, MCP server, client, and Librarian domain worker.
3. `validator.py --scan-all` passes; `catalog/index.json` remains current for source discovery during the migration window.
4. Consumers can discover, disclose, run, and record through the in-repo **stdlib** `skills_*` MCP/HTTP Gateway (Platform auth uses **fakes until Platform publishes** real claims).
5. The real Eval Runner **rejects prompt-only certification** — `usable` / certified profiles require executed evidence, not vibes.
6. Additive registry migration `20260727_000005` is **packaged in this repo**; **LiNKplatform alone applies** it live. Prior `lskills` catalog/telemetry/eval_runs migrations remain.
7. Governance/permission-to-act is explicitly **out of this repo** (ADR 0001 — permanent).
8. Cursor product canary is **project-scoped only**; Codex/OpenClaw integration fragments are **handed off**, not applied from this repo.
9. Independent Codex verification of Grok implementation remains required before treating a completion report as final.

**Not the same as "stage/prod live readiness."** Live migration apply, live Platform auth, unsupervised Librarian production passes, and independent Codex verification of this plan execution remain open/blocked outside full LiNKskills ownership — see Operations Manual and OPEN-ISSUES. Do not invent live health claims.

---

## 4. Scope — inputs and outputs

### Inputs (what LiNKskills takes)

- Skill authoring requests (scaffold / reverse-engineer / refine) via `skill-architect`.
- On-disk skill packages under `skills/<skill_id>/` (Git-authoritative editable source).
- Actor/runtime claims from LiNKplatform (fakes in-repo until Platform publishes).
- Usage telemetry and run lifecycle events from Gateway / adapters.
- Eval-suite results from the real Eval Runner into certification evidence / `lskills.eval_runs` (when schema is applied).

### Outputs (what LiNKskills produces)

- A versioned **skill catalog** (Git source + `catalog/index.json`; published operational state in `lskills` on LiNKplatform).
- **Immutable published bundles** (publisher) and progressive-disclosure fragments served by the Gateway.
- **Mandatory eval suites** per skill, executed by the real Eval Runner (prompt-only scoring cannot certify).
- **Usage telemetry** (local ledger / client buffer + Gateway-observed events + `lskills.telemetry` when connected).
- **Librarian curation signals** — certification_state / profile certification transitions with real evidence.
- **Integration fragments** for Cursor (project canary), Codex, and OpenClaw — ownership of applying shared host config stays outside this repo where the plan assigns it.

### Explicit out of scope (deliberate — not forgotten)

| Out of scope | Why / where it lives instead |
|---|---|
| Entitlements, leases, kill-switches, safe-mode | Each Program's Program Ledger + `platform.capabilities` / `platform.capability_grants` (LiNKplatform) |
| Financial ledger / billing | Not this Program |
| Per-tenant / per-client skill licensing as a gate here | If ever needed: `platform.capability_grants`, not `lskills` |
| Disclosure tokens / DPR / data-purge control plane | Retired with the Logic Engine (`archive/logic-engine-2026-07-14/`) |
| Deciding whether a Program may *act* | Never LiNKskills' job (ADR 0001) |
| Live apply of shared Supabase migrations | **LiNKplatform alone** reviews, sequences, and applies |
| Hosting the generic institutional Librarian runner | `LiNKplatform/packages/librarian-runner` |
| LiNKbrain knowledge / memory / `brain_*` tools | Separate LiNKbrain service |
| Applying shared Codex host config or OpenClaw internals | Handed-off fragments + owning repos; not applied here |
| Global Cursor IDE configuration | Out of scope; Cursor product canary is project-scoped only |

---

## 5. Guiding governance principles

1. **Catalog + eval + telemetry + published delivery only.** Anything that smells like permission-to-act belongs elsewhere (ADR 0001).
2. **Git owns editable source; Platform owns published operational state** (ADR 0002). No dual steady-state truth.
3. **Quality before reliance.** Certification requires real executed eval evidence; prompt-only paths are rejected.
4. **Fail closed on structure and certification gates.** Missing eval suites, vacuous frontmatter, broken Golden Template shapes, and fake/prompt-only judges fail closed.
5. **Telemetry is observational.** Recording an invocation / run event never authorizes or denies an action.
6. **Protocol-independent core.** MCP is the primary agent interface; HTTP/API and SDK call the same domain operations (ADR 0003).
7. **Brain and Skills stay separate services.** Independently named tools, credentials, caches, and failure states.
8. **No secrets in repo.** Placeholders only; real secrets in Google Secret Manager (GSM).
9. **Archive before delete.** Superseded subsystems and docs move under archive paths; they are not silently erased.
10. **Promotion is auditable.** `development` → `staging` → `main` for source; published release channels for operational delivery.

---

## 6. Success criteria

| Criterion | Evidence that counts |
|---|---|
| Catalog is structurally complete | 34 skills with eval suites; `validator.py --scan-all` green; catalog index `--check` green |
| Internal-launch packages exist in-repo | `packages/{contracts,core,publisher,eval_runner,tool_runtime,gateway,mcp_server,client,librarian_domain}` |
| Gateway / MCP surface exists | stdlib HTTP Gateway + `skills_*` MCP server in-repo (auth fakes until Platform publishes) |
| Real Eval Runner rejects prompt-only | Certification path refuses prompt-only / fake judges |
| Registry migration packaged | `20260727_000005_lskills_registry_foundation.sql` + manifest; live apply owned by LiNKplatform |
| Compatibility path retained | `lib/skill_runtime` still available during migration; not claimed as the sole final load path |
| Scope boundary holds | No live Logic Engine deploy path; ADR 0001 accepted; ADRs 0002–0008 accepted |
| Librarian split is clear | Instructions here; domain worker package here; generic host in LiNKplatform |
| Actor integrations correctly scoped | Cursor project canary only; Codex/OpenClaw fragments handed off |
| Live stage/prod readiness | **Not yet a claimed success** — W20 **BLOCKED**; blocked on Platform apply, live PACI, supervised ops, Codex verification |

---

## 7. Relationship to other documents

| Document | Role |
|---|---|
| [`LINKSKILLS-TECHNICAL-PRD.md`](./LINKSKILLS-TECHNICAL-PRD.md) | Exhaustive technical reference for how the system works. |
| [`LINKSKILLS-OPERATIONS-MANUAL.md`](./LINKSKILLS-OPERATIONS-MANUAL.md) | Plain-English handbook for the Principal. |
| [`LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md`](./LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md) | Approved architecture and phased execution plan (hash above). |
| [`OPEN-ISSUES.md`](./OPEN-ISSUES.md) | Append-only build log — what was built, deferred, and limited. |
| [`adr/0001-…`](./adr/0001-retire-logic-engine-governance-layer.md) through [`adr/0008-…`](./adr/0008-librarian-ownership-cross-repo-contract.md) | Accepted ADRs for permanent scope and launch architecture. |
| `docs/archive/*` (incl. `legacy-root/`) | Superseded specs, former root PRD/SOP/operator docs, and governance notes; **not** authoritative. |
| `archive/logic-engine-2026-07-14/` | Retired governance subsystem (separate archive namespace — do not revive). |

---

## 8. One-sentence Intent

**LiNKskills is LiNKtrend's centralized skill catalog and procedural-capability platform: progressive-disclosure skills with mandatory real eval proof, published delivery through a skills Gateway, and usage telemetry, curated by the Librarian — and deliberately not a governance or permission-to-act plane.**
