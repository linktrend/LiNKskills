# LiNKskills — Intent

**Status:** Confirmed Intent for the LiNKskills Program itself (this repository), written in the same spirit as LiNKdeveloper's Intent artifact — a plain-English statement of what is being built, why, for whom, and what "done" means. Grounded in what the code and migrations actually deliver today (through the 2026-07-18 catalog/runtime engineering pass), not in aspirational roadmap language.

**Audience:** The Principal (sole human authority) and any agent across any Program that needs to understand *why this library exists* before reading the Technical PRD.

**Companion document:** [`LINKSKILLS-TECHNICAL-PRD.md`](./LINKSKILLS-TECHNICAL-PRD.md) — exhaustive how-it-works reference.

---

## 1. Problem

LiNKtrend is an AI-native venture studio. Every Program (LiNKsites, LiNKdeveloper, LiNKbrain, and future Programs) runs agents that need reusable, progressive-disclosure skills — not one-off prompts pasted into chats.

Without a shared library:

- Each Program reinvents the same skill shapes, validators, and telemetry.
- Quality is self-declared ("this prompt worked once") instead of proven by a baseline eval suite.
- Usage is invisible — failures, HITL friction, and cost outliers never feed a curation loop.
- A previous design attempt bolted a **governance / permission-to-act** plane onto this repo (the retired Logic Engine). That was the wrong home for entitlements, leases, kill-switches, and per-tenant policy.

The problem LiNKskills solves is: **give every studio agent one shared, versioned, quality-gated skill catalog — with mandatory eval proof and usage telemetry — without owning whether any Program may act.**

---

## 2. Who it is for

| Role | Relationship to LiNKskills |
|---|---|
| **Principal (Carlos)** | Sole human authority. Reviews escalated Librarian proposals when auto-promotion criteria are not met. Does not author skills day to day. |
| **Every agent across every Program** | Primary consumer. Loads skill instructions from a git checkout of this repo via `lib/skill_runtime` (or equivalent progressive-disclosure load). |
| **Librarian** | Curation agent. Skill-side instructions live in `skills/self-improvement`; the runnable worker lives in `LiNKplatform/packages/librarian-runner`. |
| **Skill authors (agents)** | Create/refine skills via `skill-architect` / `skill-template`, validated by `validator.py`. |

LiNKskills is **not** a customer-facing product. It is LiNKtrend's internal skill library Program.

---

## 3. What "done" looks like (Program-level)

Studio-level "library done" for the current scope means:

1. Every skill under `skills/` ships the progressive-disclosure shape (`SKILL.md` + supporting folders) and a baseline `references/eval-suite.yaml`.
2. `validator.py --scan-all` passes (structure, frontmatter, eval-suite presence, tool registry).
3. `catalog/index.json` is current (`scripts/build-catalog-index.py --check`).
4. Consumer Programs can resolve and load skills via `lib/skill_runtime`, and record invocations to `execution_ledger.jsonl` (and optionally `lskills.telemetry`).
5. The `lskills` schema (catalog / telemetry / eval_runs) exists as real migrations; certification_state is the Librarian's internal quality gate — not permission-to-act.
6. Governance/permission-to-act is explicitly **out of this repo** (ADR 0001).

**Not the same as "every skill is `usable` in production."** As of 2026-07-19, filesystem catalog entries default to `draft` until the Librarian certifies them against live eval runs. Consumers correctly use `require_usable=False` until that gate is live.

---

## 4. Scope — inputs and outputs

### Inputs (what LiNKskills takes)

- Skill authoring requests (scaffold / reverse-engineer / refine) via `skill-architect`.
- On-disk skill packages under `skills/<skill_id>/`.
- Usage telemetry from consumer invocations (`execution_ledger.jsonl` buffer; optional flush to Supabase).
- Eval-suite results written by the Librarian runner (or future runners) into `lskills.eval_runs`.

### Outputs (what LiNKskills produces)

- A versioned **skill catalog** (files + `catalog/index.json`; DB mirror in `lskills.catalog`).
- **Mandatory eval suites** per skill (YAML under `references/eval-suite.yaml`).
- **Usage telemetry** (local ledger + `lskills.telemetry`).
- **Librarian curation signals** — certification_state transitions (`draft` → `eval_pending` → `usable` / demote / `deprecated`).

### Explicit out of scope (deliberate — not forgotten)

| Out of scope | Why / where it lives instead |
|---|---|
| Entitlements, leases, kill-switches, safe-mode | Each Program's Program Ledger + `platform.capabilities` / `platform.capability_grants` (LiNKplatform) |
| Financial ledger / billing | Not this Program |
| Per-tenant / per-client skill licensing as a gate here | If ever needed: `platform.capability_grants`, not `lskills.catalog` |
| Disclosure tokens / DPR / data-purge control plane | Retired with the Logic Engine (`archive/logic-engine-2026-07-14/`) |
| Deciding whether a Program may *act* | Never LiNKskills' job |
| Long-lived skill-text API server | Skills are git-backed files; see consumer load path |
| Hosting the runnable Librarian worker | `LiNKplatform/packages/librarian-runner` |

---

## 5. Guiding governance principles

1. **Catalog + eval + telemetry only.** Anything that smells like permission-to-act belongs elsewhere (ADR 0001).
2. **Quality before reliance.** `usable` requires a non-empty eval suite and a passing latest eval run (DB-enforced when schema is applied).
3. **Fail closed on structure.** Missing eval suites, vacuous frontmatter, and broken Golden Template shapes fail `validator.py`.
4. **Telemetry is observational.** Recording an invocation never authorizes or denies an action.
5. **Right-sized templates.** `format_profile: simple | heavy` — persistence machinery is required only for heavy skills; eval suites and ledger append remain mandatory for both.
6. **No secrets in repo.** Placeholders only; real secrets in Google Secret Manager (GSM).
7. **Archive before delete.** Superseded subsystems and docs move under archive paths; they are not silently erased.
8. **Promotion is auditable.** `development` → `staging` → `main`; production checkouts pin SHA/tag from `main`.

---

## 6. Success criteria

| Criterion | Evidence that counts |
|---|---|
| Catalog is structurally complete | 34 skills with eval suites; `validator.py --scan-all` green; catalog index `--check` green |
| Consumer load path works | `lib/skill_runtime` unit tests pass; documented load path in Technical PRD |
| Schema exists | Migrations under `supabase/migrations/` for `lskills.catalog` / `telemetry` / `eval_runs` |
| Scope boundary holds | No live Logic Engine deploy path; ADR 0001 accepted |
| Librarian split is clear | Instructions in `skills/self-improvement`; runner in LiNKplatform |
| Live certification of all skills to `usable` | **Not yet a claimed success** — deferred until Librarian runs against applied schema with real eval passes |

---

## 7. Relationship to other documents

| Document | Role |
|---|---|
| [`LINKSKILLS-TECHNICAL-PRD.md`](./LINKSKILLS-TECHNICAL-PRD.md) | Exhaustive technical reference for how the system works. |
| [`LINKSKILLS-OPERATIONS-MANUAL.md`](./LINKSKILLS-OPERATIONS-MANUAL.md) | Plain-English handbook for the Principal. |
| [`OPEN-ISSUES.md`](./OPEN-ISSUES.md) | Append-only build log — what was built, deferred, and limited. |
| [`adr/0001-retire-logic-engine-governance-layer.md`](./adr/0001-retire-logic-engine-governance-layer.md) | Still-live ADR; actively cited. Explains the permanent scope boundary. |
| `docs/archive/*` | Superseded specs and governance notes; **not** authoritative. |
| `archive/logic-engine-2026-07-14/` | Retired governance subsystem (separate archive namespace — do not revive). |

---

## 8. One-sentence Intent

**LiNKskills is LiNKtrend's centralized skill catalog: progressive-disclosure skills with a mandatory eval suite and usage telemetry, curated by the Librarian — and deliberately not a governance or permission-to-act plane.**
