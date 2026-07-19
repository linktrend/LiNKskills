# LiNKskills Operations Manual

**Who this is for:** you — LiNKtrend’s Principal. You make strategic decisions and review escalations. You do not write skills, run validators, or manage servers day to day.

**What this is:** a plain-English handbook for what LiNKskills is *today*, and what your role in it is. It is not a technical design document.

**Honesty rule:** everything below describes what is actually built right now. Where something is planned but not fully live yet, it is labeled under [Current status](#current-status-what-is-not-fully-live-yet).

---

## What LiNKskills is

LiNKskills is the studio’s shared **skill library**. Think of it as a carefully curated bookshelf of reusable AI work instructions that every Program’s agents can pull from — market research, git safety checks, QA patterns, skill-authoring templates, and dozens more.

Each skill is a folder of instructions and supporting files (not a mysterious cloud API). Agents load those files from a pinned copy of this library. Every skill is supposed to prove its quality with a baseline test suite, and every real use is recorded so the library can improve over time.

**What it is not:** LiNKskills does **not** decide whether a Program is allowed to send an email, charge a card, deploy something, or act on a customer’s behalf. That permission lives in each Program’s own ledger and in LiNKplatform’s capability registry. An earlier attempt to put that control plane here was retired on purpose.

---

## Your role today

### Day to day

Most of the time you do **not** need to touch this repository. Agents author and refine skills; automated checks catch broken structure; consumer Programs load what they need.

### Moments when a human decision may be required

| When | What you are asked | What happens if you say no / wait |
| --- | --- | --- |
| Librarian escalation | Review a proposed skill upgrade when the automatic “this version is clearly better” bar is not met | The candidate stays uncertified (`eval_pending`); agents can still load draft instructions if Programs allow it, but it is not marked `usable` |
| Release promotion | Approve promoting library changes `development` → `staging` → `main` when release owners route that through you | Production checkouts stay on the previous pinned version |
| Exceptional failure | Briefing when validation, telemetry, or curation is stuck beyond agent repair | Technical helpers investigate; you decide direction, not commands |

### What you do **not** need to do

- Write or edit `SKILL.md` files
- Run Python validators or unit tests
- Manage Supabase or VPS day to day
- Approve every skill invocation across Programs
- Revive or operate the retired Logic Engine

---

## The four jobs of this library (plain names)

| # | Plain-English job | What it means |
| --- | --- | --- |
| 1 | Keep the catalog | A versioned set of skills with a clear folder shape and a machine index so Programs can find them |
| 2 | Require a quality test | Every skill ships a baseline eval suite before it can be treated as certified/`usable` |
| 3 | Record real usage | When a skill is used, that fact is logged (locally always; into the shared database when connected) |
| 4 | Curate over time | The Librarian reads usage + eval results and proposes versioned upgrades — automatically when the evidence is clean, escalated to you when it is not |

---

## Walkthrough: how a skill gets used (as things work today)

### 1. A Program needs a capability

An agent in LiNKsites, LiNKdeveloper, or another Program decides it needs a skill (for example, a pre-push git safety checklist).

### 2. It loads instructions from a checkout

The Program host keeps a copy of this repository (or the `skills/` + `catalog/` parts), pinned to a known version from `main`. It reads the skill’s instructions from files. There is no “call LiNKskills API for the prompt text” step.

### 3. It does the work under its own Program rules

Whether the agent is *allowed* to push, send, or deploy is decided by that Program’s own gates — not by LiNKskills.

### 4. It records that the skill ran

A short usage record is appended (skill name, status, summary, optional timing/cost notes). That feeds later curation. Recording usage is **observation**, not approval.

### 5. The Librarian improves the shelf (on a schedule)

On a schedule (not in the middle of your other work), the Librarian reviews noisy/failing/high-cost skills, re-runs quality suites, and either promotes a better version or queues a short review for you when the evidence is ambiguous.

---

## Walkthrough: how a new or improved skill lands

1. An authoring agent uses the skill-architect / skill-template pattern to create or refine a skill folder.
2. Automated validation checks structure, required files, and the baseline eval suite file.
3. The machine catalog index is regenerated so consumers can discover the skill.
4. Changes merge through the normal studio branch path into `development`, then promote to `staging` and `main`.
5. Production hosts that pin `main` pick up the new SHA/tag on their next sync.

You are not asked to click through each of those engineering steps. You care that releases are deliberate and that broken skills do not silently become “certified.”

---

## What happens when something goes wrong

The system is designed to **stop** rather than pretend:

- Broken skill structure fails the validator — it should not merge cleanly through CI.
- A skill missing its baseline eval suite fails validation.
- If someone asks a consumer to hard-require `usable` certification before the Librarian has certified anything, loads fail closed instead of inventing a pass.
- Telemetry write failures to the database do not erase the local usage log — the local buffer remains.
- The Librarian does not auto-promote on vibes; weak or regressing evidence stays pending or demotes a previously usable version.
- The retired Logic Engine paths are archived and must not be started.

So a failure is usually: “checks failed, usage was still recorded locally, certification did not advance” — not “the library silently granted permission to act.”

---

## Current status (what is not fully live yet)

| Topic | Status today |
| --- | --- |
| Shared skill catalog on disk + validator + CI | **Built.** Dozens of skills, each with a baseline eval suite file. |
| Consumer load helper (`lib/skill_runtime`) | **Built** and unit-tested. |
| Database schema for catalog / telemetry / eval runs | **Written** as migrations. Confirm applied on each environment with your technical helpers. |
| Every skill marked certified/`usable` | **Not yet.** Catalog index still treats skills as draft until Librarian certification against real eval runs. Programs load instructions with the soft gate today. |
| Librarian automatic nightly curation in production | **Runner exists in LiNKplatform**; treat first live passes as supervised (`dry run` first). |
| Phone dashboard for skill approvals | **Not built.** Escalations come as briefings / queued review items. |

---

## FAQ

**Do I need to understand Python or git to use this?**  
No. Your role is direction and escalated judgment. Technical helpers and agents handle the mechanics.

**Does LiNKskills control what my Programs are allowed to do?**  
No. That was tried earlier and reversed. Permission-to-act lives in each Program’s ledger and LiNKplatform’s capability grants.

**How do I know the library is healthy?**  
Ask for the latest CI status on `main`, whether validators pass, and whether usage/telemetry and Librarian passes are flowing. Prefer short status briefings over raw logs.

**What if I don’t like a proposed skill upgrade?**  
Leave it uncertified / reject the escalation. Agents should not treat it as `usable` until a clean pass lands.

**Is the old Logic Engine still running?**  
No. It is archived for history and must not be deployed.

**Where do the “official” explanations live now?**  
Three documents plus the open-issues log: Intent, Technical PRD, this Operations Manual, and `docs/OPEN-ISSUES.md`. Older scattered docs under `docs/archive/` are history only.

---

## One-page reminder

1. LiNKskills is the shared skill bookshelf for every Program’s agents.  
2. Skills are files + quality suites + usage logs — not a permission system.  
3. Programs load pinned copies; they do not depend on a LiNKskills “action API.”  
4. The Librarian improves the shelf on a schedule and escalates ambiguous upgrades to you.  
5. You do not need to run technical commands; you decide direction and escalations.  
6. Certification of every skill to `usable` and fully unsupervised production Librarian passes are still ahead — the handbook above already says so honestly.
