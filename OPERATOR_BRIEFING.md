# LiNKskills Library Operator Briefing

## Audience
This document is for non-technical operators who need to request, migrate, or improve skills without editing code.

## What This System Does
LiNKskills Library is a controlled system for AI skills.  
Each skill is built with:
- clear operating instructions (`SKILL.md`),
- persistent task memory (`.workdir/tasks/...`),
- validation contracts (`references/schemas.json`),
- learning logs (`references/old-patterns.md`),
- execution history (`execution_ledger.jsonl`).

The goal is reliability: fewer broken runs, easier handoffs, and repeatable behavior.

Registry layout:
- Skills live in `/skills/[skill-name]`.
- Global CLI tools live in `/tools/[tool-name]`.

## What You Need To Know First
- A "skill" is a reusable capability (for example: email drafting, web extraction, report generation).
- `skill-architect` is the skill that creates, converts, and improves other skills.
- The repository now uses a Multi-Agent Sync (MAS) system for all branch/review/deploy actions.

## MAS System (How Sync and Deployment Work)
MAS is the standardized control layer for distributed collaboration.

Key files:
- `manifest.json`: master list of registered skills/tools and their versions.
- `configs/activation.json`: which capabilities are active in your environment (`active_uid_list`).
- `configs/activation.example.json`: starter template when setting up a new machine/environment.

Required automation scripts:
- `scripts/lsl-update.sh`: saves work to a unique `dev-*` branch and pushes it.
- `scripts/lsl-review.py`: checks all remote `dev-*` branches with validator and outputs a Sync Report JSON.
- `scripts/lsl-deploy.sh`: validates and deploys `main` to the production GitHub remote; writes audit logs to `~/.lsl/audit.jsonl`.

Important policy:
- Do not use manual ad-hoc git workflows for normal operations.
- Use MAS scripts as the default path for save, review, merge, and deploy.

## MAS Daily Runbook
1. Save and publish your current work:
```bash
./scripts/lsl-update.sh
```
2. Review all incoming `dev-*` branches and generate a report:
```bash
python3 scripts/lsl-review.py --repo-root . --remote origin --output reports/sync-report.json
```
3. If authorized, merge all safe branches:
```bash
python3 scripts/lsl-review.py --repo-root . --remote origin --merge-safe
```
4. Deploy validated `main`:
```bash
./scripts/lsl-deploy.sh
```

## Internalized GW Gateway: First-Time Setup
The Google Workspace gateway (`gw`) is now internal to this repository under `tools/gw/src/`.

For a new clone or new machine:
1. Create and activate the local GW virtual environment:
```bash
cd tools/gw/src
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
```
2. Install dependencies inside that virtual environment:
```bash
pip install -r requirements.txt
```
3. Manually place local identity files in `tools/gw/src/` if they are not already present:
```bash
cp /path/to/credentials.json tools/gw/src/credentials.json
cp /path/to/token.json tools/gw/src/token.json
```
4. Run initial authentication (required when token is missing, expired, or replaced):
```bash
tools/gw/bin/gw setup --config tools/gw/src/credentials.json
```

Identity behavior:
- `credentials.json` and local token files are machine-specific and excluded from Git.
- The local `tools/gw/src/venv` plus local identity files keep the gateway machine-independent in code while preserving strict per-machine account isolation.

## Internalized GW Gateway: Daily Operations
- Use `tools/gw/bin/gw` for Gmail/Drive/Docs/Sheets/Calendar/Chat operations.
- Sync code changes through MAS (`lsl-update`, `lsl-review`, `lsl-deploy`).
- Do not commit credentials/tokens; only code in `tools/gw/src/` should travel through GitHub.

## When To Use Skill Architect
Use `skill-architect` in one of 3 modes:

1. `SCAFFOLD`
- Use when you want a brand-new skill from plain English requirements.
- Result: a full new skill folder built to LiNKskills standards.

2. `REVERSE_ENGINEER`
- Use when you have a third-party prompt/skill and want it converted to LiNKskills standards.
- Result: a migrated skill with Decision Tree, persistence, contracts, and audit files.

3. `REFINER`
- Use when an existing skill must be improved.
- Drivers can include:
  - failures from `execution_ledger.jsonl`,
  - lessons from `references/old-patterns.md`,
  - new user-requested features,
  - tool or API changes.

## Intelligence Floor (Engine Block)
Each skill includes an `engine` block in YAML frontmatter.  
This defines the minimum LLM capability needed to run the skill safely.

Example:

```yaml
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5
  context_required: 128000
```

Why this matters:
- Cost control: simpler skills can declare `fast` and run cheaper.
- Failure prevention: complex skills can fail-fast if runtime is too weak.
- Portability: global tier-to-model mapping is controlled in `global_config.yaml`.

## Global Tooling & Persistence Protocol
All scaffolded, migrated, and refined skills follow this operating order:
1. Native CLI first (for example `git`, `grep`, `rg`).
2. CLI wrapper scripts in `scripts/` as default logic layer.
3. Direct API only for explicit exceptions (high-frequency LLM reasoning, high-serialization DB queries, real-time streaming).
4. MCP only for persistent background/session services.

Persistence defaults:
- phase records in `.workdir/tasks/{{task_id}}/state.jsonl`,
- optional flat files for large artifacts,
- downstream phases should seek specific data points instead of loading full context.

Tool sourcing rule:
- Skills must prioritize global `/tools`.
- If a needed tool does not exist, request `tool-architect` to create it first.

## How To Request Work (Copy/Paste Templates)

### A) Create a New Skill (SCAFFOLD)
Use the skill-architect in SCAFFOLD mode.
Skill name: `customer-onboarding`
Description: Drafts and validates onboarding responses for new customers.
Usage trigger: Use when a user asks to create or update customer onboarding communications.
Tools: `read_file`, `write_file`, `mcp-email`
Required output: full LiNKskills structure with contracts and changelog.
Engine floor: include `min_reasoning_tier`, `preferred_model`, and `context_required`.

### B) Convert a Third-Party Skill (REVERSE_ENGINEER)
Use the skill-architect in REVERSE_ENGINEER mode.
Target skill name: `web-research-ops`
Source input: [paste third-party prompt/skill text here]
Required behavior:
- extract tool requirements,
- map into 5-phase workflow,
- inject Decision Tree and task_id persistence,
- inject `engine` intelligence-floor requirements,
- generate old-patterns entries for likely failure modes.

### C) Improve an Existing Skill (REFINER)
Use the skill-architect in REFINER mode for `email-responder`.
Improve it using:
- recent ledger issues,
- known-bad entries in old-patterns,
- this new feature request: validate attachments before draft generation.
Also:
- tighten input schema if needed,
- update Decision Tree checks,
- update the `engine` block if complexity/context needs changed,
- increment version and update references/changelog.md.

## What Good Output Looks Like
After a successful request, you should see:
- updated or new skill folder,
- `SKILL.md` with fail-fast Decision Tree and 5-phase workflow,
- `references/schemas.json` with valid contracts,
- `references/changelog.md` with version notes,
- `engine` block aligned with expected runtime capability,
- consistent Task ID usage,
- successful validation output.

## Operator Quality Checklist
Before approving final delivery, check:
1. Was the correct mode used (`SCAFFOLD`, `REVERSE_ENGINEER`, `REFINER`)?
2. Is the skill structure complete (advanced/examples/references/scripts/.workdir)?
3. Did version and changelog get updated?
4. Is CLI-first tooling policy present and are API/MCP exceptions clearly constrained?
5. Is the `engine` intelligence floor defined and appropriate for task complexity?
6. Were failures or lessons captured in `old-patterns.md` when relevant?
7. Did validation pass?
8. Was MAS followed (`lsl-update` -> `lsl-review` -> `lsl-deploy`) without manual ad-hoc git steps?

## Escalation Rules
Escalate to a technical owner if:
- validation repeatedly fails,
- contract schemas are unclear,
- external tool requirements are missing,
- migration source is incomplete or contradictory.

## Current Scope Reminder
As of 2026-02-22, this repository is in a bootstrap stage with core skills:
- `skill-template`
- `skill-architect`
- `tool-architect`

Additional production skills are expected to be generated or migrated through `skill-architect`.
