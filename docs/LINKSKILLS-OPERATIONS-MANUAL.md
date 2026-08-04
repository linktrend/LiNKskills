# LiNKskills Operations Manual

**Who this is for:** you — LiNKtrend’s Principal. You make strategic decisions and review escalations. You do not write skills, run validators, or manage servers day to day.

**What this is:** a plain-English handbook for what LiNKskills is *today*, and what your role in it is. It is not a technical design document.

**Honesty rule:** everything below describes what is actually built or packaged right now under the **approved internal-launch plan**. Where something is planned but not fully live yet, it is labeled under [Current status](#current-status-what-is-not-fully-live-yet). This handbook does **not** claim stage/production health.

**Approved plan:** `docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md` (SHA-256 `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`). ADRs 0001–0008 accepted.

---

## What LiNKskills is

LiNKskills is the studio’s shared **skill library and procedural-capability platform**. Think of it as a carefully curated bookshelf of reusable AI work instructions that every Program’s agents can pull from — market research, git safety checks, QA patterns, skill-authoring templates, and dozens more.

Each skill is a folder of instructions and supporting files in Git. For ordinary use, agents are meant to discover and load **published, certified** versions through a LiNKskills Gateway (the same way you would ask a librarian for the current approved procedure — not rummage through the author’s desk drafts). Every skill is supposed to prove its quality with a real baseline eval run, and every real use is recorded so the library can improve over time.

**What it is not:** LiNKskills does **not** decide whether a Program is allowed to send an email, charge a card, deploy something, or act on a customer’s behalf. That permission lives in each Program’s own ledger and in LiNKplatform’s capability registry. An earlier attempt to put that control plane here was retired on purpose (ADR 0001 — permanent).

**Separate from LiNKbrain:** Brain stores institutional knowledge and memory. Skills stores procedures. They stay separate services.

---

## Your role today

### Day to day

Most of the time you do **not** need to touch this repository. Agents author and refine skills; automated checks catch broken structure; consumer Programs load what they need through the Gateway (or, during migration, from a pinned library checkout).

### Moments when a human decision may be required

| When | What you are asked | What happens if you say no / wait |
| --- | --- | --- |
| Librarian escalation | Review a proposed skill upgrade when the automatic “this version is clearly better” bar is not met | The candidate stays uncertified (`eval_pending`); agents can still load draft/compatibility instructions if Programs allow it, but it is not marked certified/`usable` |
| Release promotion | Approve promoting library changes `development` → `staging` → `main` when release owners route that through you | Production source pins stay on the previous version |
| Cross-repo launch gates | Confirm direction when Platform migration apply, real auth, or actor integrations are blocked outside this repo’s ownership | Work waits on the owning repository; Skills does not seize shared surfaces |
| Exceptional failure | Briefing when validation, telemetry, or curation is stuck beyond agent repair | Technical helpers investigate; you decide direction, not commands |

### What you do **not** need to do

- Write or edit `SKILL.md` files
- Run Python validators or unit tests
- Apply shared Supabase migrations yourself (LiNKplatform owns live apply)
- Manage VPS day to day
- Approve every skill invocation across Programs
- Revive or operate the retired Logic Engine
- Apply Codex/OpenClaw host configuration from this repo (fragments are handed off to the owners)

---

## The jobs of this library (plain names)

| # | Plain-English job | What it means |
| --- | --- | --- |
| 1 | Keep the catalog | A versioned set of skills with a clear folder shape and a machine index so Programs can find them |
| 2 | Require a quality test | Every skill ships a baseline eval suite; a **real** eval runner must execute evidence before certification — prompt-only scoring does not count |
| 3 | Publish safely | Git holds editable drafts; published releases are immutable bundles served through the Gateway |
| 4 | Record real usage | When a skill is used, that fact is logged (locally always during migration; through the Gateway and shared database when connected) |
| 5 | Curate over time | The Librarian reads usage + eval results and proposes versioned upgrades — automatically when the evidence is clean, escalated to you when it is not |

---

## Walkthrough: how a skill gets used (target path)

### 1. A Program or actor needs a capability

An agent in Cursor, Codex, OpenClaw/Lisa, LiNKsites, or another Program decides it needs a skill (for example, a pre-push git safety checklist).

### 2. It asks the LiNKskills Gateway

The actor uses the `skills_*` tools (MCP) or the HTTP API to search, describe, and load progressive fragments of a **published** skill — not a free-form “dump the whole library into context” call.

### 3. It does the work under its own Program rules

Whether the agent is *allowed* to push, send, or deploy is decided by that Program’s own gates — not by LiNKskills.

### 4. It records that the skill ran

Run lifecycle and feedback are observed by the Gateway (plus local buffers if offline). Recording usage is **observation**, not approval.

### 5. The Librarian improves the shelf (on a schedule)

On a schedule (not in the middle of your other work), the Librarian reviews noisy/failing/high-cost skills, requires real eval evidence, and either promotes a better version or queues a short review for you when the evidence is ambiguous.

---

## Walkthrough: compatibility path still in use during migration

Some Programs still load skill files from a **pinned checkout** of this repository (the older helper path). That still works and is supported on purpose while consumers migrate. It is **not** the final sole way the studio is meant to load skills. Think of it as reading last week’s printed copy while the new published shelf comes online.

---

## Walkthrough: how a new or improved skill lands

1. An authoring agent uses the skill-architect / skill-template pattern to create or refine a skill folder in Git.
2. Automated validation checks structure, required files, and the baseline eval suite file.
3. The publisher builds an immutable bundle; the real eval runner must produce executable evidence before certification.
4. The machine catalog index stays current for source discovery; published registry rows are advanced when Platform-backed publication runs.
5. Changes merge through the normal studio branch path into `development`, then promote to `staging` and `main`.
6. Actors on the Gateway pick up published releases; checkout-based hosts pick up the new SHA/tag on their next sync.

You are not asked to click through each of those engineering steps. You care that releases are deliberate and that broken or “prompt-only” skills do not silently become “certified.”

---

## What happens when something goes wrong

The system is designed to **stop** rather than pretend:

- Broken skill structure fails the validator — it should not merge cleanly through CI.
- A skill missing its baseline eval suite fails validation.
- Prompt-only or fake-judge “evals” are rejected for certification.
- If someone asks a consumer to hard-require `usable` certification before anything is certified, loads fail closed instead of inventing a pass.
- Telemetry write failures to the database do not erase local usage logs — buffers remain.
- The Librarian does not auto-promote on vibes; weak or regressing evidence stays pending or demotes a previously usable version.
- The retired Logic Engine paths are archived and must not be started.
- This repo does not apply live shared database migrations; if apply is blocked, that is a Platform-owned gate — not a Skills override.

So a failure is usually: “checks failed, usage was still recorded locally, certification did not advance” — not “the library silently granted permission to act.”

---

## Current status (what is not fully live yet)

| Topic | Status today |
| --- | --- |
| Shared skill catalog on disk + validator + CI | **Built.** Dozens of skills, each with a baseline eval suite file. |
| Internal-launch domain packages (`packages/*`) | **In-repo** under the approved plan (contracts, core, publisher, eval runner, tool runtime, gateway, MCP, client, librarian domain). |
| `skills_*` MCP / HTTP Gateway (stdlib) | **Exists in-repo.** Local process health endpoints are not a claim of studio stage/prod readiness. |
| Platform auth / PACI consumer pins | **Local/fake only.** AuthClaims `1.1.0` / contracts `0.2.2`; PACI envelope contracts `0.3.0`; Skills-pinned to certified Platform candidate `421a35e97bc302be0f5e1f196d0a5e8d132f6fd8`. **Not** proven against a live Platform PACI issuer. |
| Real Eval Runner rejecting prompt-only certification | **Built in-repo.** |
| Additive registry migrations (incl. `20260727_000005`) | **Packaged** here. **LiNKplatform alone applies** live. |
| Compatibility load helper (`lib/skill_runtime`) | **Still present** for migration; not the final sole load path. |
| Every skill marked certified/`usable` | **Not yet.** One sealed local canary (`canary-echo`) is `usable`; other catalog skills remain draft until sealed executable evidence. |

| Cursor product canary | **Project-scoped only** (example fragment + notes). No global live canary. |
| Codex / OpenClaw wiring | **Fragments handed off** — not applied from this repo. |
| Librarian automatic nightly curation in production | **Host exists in LiNKplatform**; domain worker package in Skills; treat first live passes as supervised. |
| Independent Codex verification of this plan’s implementation | **Still required / open** — Grok reports are provisional until checked. |
| W20 stage readiness | **BLOCKED** (2026-08-01). Candidate docs/schemas/tests shipped; live stage PACI, stage apply receipt, and sealed Linux evidence remain absent. See `docs/handoffs/2026-08-01-linkskills-w20-stage-readiness.md`. |
| Live stage/prod internal-launch readiness | **Not claimed.** Blocked on Platform apply, live PACI, supervised ops, and verification outside full Skills ownership. |
| Phone dashboard for skill approvals | **Not built.** Escalations come as briefings / queued review items. |

---

## FAQ

**Do I need to understand Python or git to use this?**
No. Your role is direction and escalated judgment. Technical helpers and agents handle the mechanics.

**Does LiNKskills control what my Programs are allowed to do?**
No. That was tried earlier and reversed. Permission-to-act lives in each Program’s ledger and LiNKplatform’s capability grants.

**Is this the same system as LiNKbrain?**
No. Brain = knowledge/memory. Skills = procedures. Separate services on purpose.

**How do I know the library is healthy?**
Ask for a short status briefing covering: CI on `main`, whether validators pass, whether the registry migration was applied by Platform, whether real auth replaced fakes, whether Gateway consumers are on published releases, and whether Librarian passes are flowing under supervision. Prefer briefings over raw logs. Do not treat a developer laptop `/health` check as production readiness.

**What if I don’t like a proposed skill upgrade?**
Leave it uncertified / reject the escalation. Agents should not treat it as certified/`usable` until a clean pass lands.

**Is the old Logic Engine still running?**
No. It is archived for history and must not be deployed.

**Where do the “official” explanations live now?**
Intent, Technical PRD, this Operations Manual, OPEN-ISSUES, the approved internal-launch plan, and ADRs 0001–0008. Older scattered docs under `docs/archive/` are history only.

---

## One-page reminder

1. LiNKskills is the shared skill bookshelf and procedure platform for every Program’s agents.
2. Skills are files + real quality suites + published releases + usage logs — not a permission system.
3. Steady-state delivery is the Gateway (`skills_*`); git checkout loading is a migration bridge.
4. The Librarian improves the shelf on a schedule and escalates ambiguous upgrades to you.
5. You do not need to run technical commands; you decide direction and escalations.
6. Live stage/prod readiness is still ahead (W20 **BLOCKED**); live migration apply, live Platform PACI, and independent Codex verification remain open — and this handbook says so honestly.
