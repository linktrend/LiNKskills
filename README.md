# LiNKskills Library

LiNKskills Library is a local-first system for building, operating, and governing production-grade AI skills.

It standardizes how skills are created, migrated, validated, improved, and audited so capabilities do not drift over time.

## What This Repository Is

This repository is a skill registry and governance runtime.

It combines:
- a Golden Template for skill structure,
- a meta-skill (`skill-architect`) that creates and improves skills,
- a validator (`validator.py`) that enforces quality rules,
- a global evaluator (`global_evaluator.py`) that reports cross-skill health,
- persistent execution data (`.workdir/` and `execution_ledger.jsonl`),
- anti-drift controls (`old-patterns.md` and `global_blacklist.md`).
- intelligence-floor controls (`engine` frontmatter + `global_config.yaml` tier mapping).
- a global tools registry (`/tools`) and tool creation meta-skill (`/skills/tool-architect`).
- a Multi-Agent Sync (MAS) control plane (`manifest.json`, `configs/activation.json`, and `scripts/lsl-*` automation).
- an internalized Google Workspace gateway source at `tools/gw/src/` for cross-machine portability.

## Current Maturity (2026-02-20)

This codebase is in a bootstrap operational stage.

Current core skills:
- `/skills/skill-template` (baseline structure and conventions)
- `/skills/skill-architect` (scaffold, reverse-engineer, and refiner workflows)
- `/skills/tool-architect` (global tool wrapper and registry builder)

Expected scaling path:
- use `skill-architect` to generate or migrate additional skills into this registry.

## Why LiNKskills Exists

The system is designed to solve common AI operations problems:
- inconsistent prompts and behavior drift,
- no durable state across sessions,
- weak contract validation,
- no reliable audit trail,
- no systematic feedback loop from failures to better versions.

LiNKskills addresses this with explicit workflow phases, durable checkpoints, contract schemas, and versioned skill evolution.

## Root Files and Their Roles

- `AGENT.md`: system-wide operating conventions.
- `global_config.yaml`: global validator/evaluator controls (strict mode, permissions, Task ID regex, ledger path).
- `execution_ledger.jsonl`: centralized run history and status tracking.
- `validator.py`: per-skill quality gate and structural compliance checks.
- `global_evaluator.py`: cross-skill analytics (failure/HITL signals, coverage, flags).
- `global_blacklist.md`: studio-wide prohibited patterns.
- `manifest.json`: MAS master catalog of registered skills and tools.
- `configs/activation.json`: environment activation toggles (`active_uid_list`, startup behavior).
- `configs/activation.example.json`: baseline activation template for new environments.
- `OPERATOR_BRIEFING.md`: non-technical usage guide for operators.
- `scripts/lsl-update.sh`: standardized branch/create/commit/push automation.
- `scripts/lsl-review.py`: standardized remote `dev-*` branch validation and merge readiness reporting.
- `scripts/lsl-deploy.sh`: standardized validated deployment to production remote with audit logging.
- `skills/`: all skills live here (`/skills/[skill-name]`).
- `tools/`: global CLI tools registry (`/tools/[tool-name]`).

## Multi-Agent Sync (MAS)

MAS is the distributed collaboration and deployment system for this repository.

Core MAS artifacts:
- `manifest.json`: canonical registry of installed skills/tools with `uid`, `type`, `path`, `version`, and `description`.
- `configs/activation.json`: environment-level activation list (`active_uid_list`) and startup behavior (`auto_load_on_startup`).
- `configs/activation.example.json`: starter template for creating environment-specific activation files.
- `scripts/lsl-update.sh`: creates branch names in `dev-[machine]-[taipei-timestamp]`, stages, auto-summarizes, commits, and pushes.
- `scripts/lsl-review.py`: fetches remote `dev-*` branches, validates each branch with `validator.py`, and emits a Sync Report JSON.
- `scripts/lsl-deploy.sh`: fast-forwards local `main`, validates registry, pushes to the deployment remote, and writes `~/.lsl/audit.jsonl`.

Standard MAS flow:
1. Save and publish work branch:
```bash
./scripts/lsl-update.sh
```
2. Run governance review and generate report:
```bash
python3 scripts/lsl-review.py --repo-root . --remote origin --output reports/sync-report.json
```
3. Optionally merge safe branches into local `main`:
```bash
python3 scripts/lsl-review.py --repo-root . --remote origin --merge-safe
```
4. Deploy validated `main`:
```bash
./scripts/lsl-deploy.sh
```

Enforcement rule:
- Repository interaction is expected to go through MAS scripts (`lsl-update`, `lsl-review`, `lsl-deploy`) rather than manual ad-hoc git flows, except explicit break-glass recovery.

## Internalized GW Gateway (v1.1.0)

`gw` now runs from internal source code in this repository:
- Source: `tools/gw/src/cli.py`
- Service modules: `tools/gw/src/services/`
- Utility modules: `tools/gw/src/utils/`
- Wrapper entrypoint: `tools/gw/bin/gw` (relative path, VPS/Mac/Linux friendly)

Identity isolation:
- Local identity artifacts are excluded from git:
  - `tools/gw/src/credentials.json`
  - `tools/gw/src/token.json`
  - `tools/gw/src/__pycache__/`
  - `tools/gw/src/*.log`

First-time setup for new clones:
1. Create and activate a local GW virtual environment:
```bash
cd tools/gw/src
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
```
2. Install dependencies inside that environment:
```bash
pip install -r requirements.txt
```
3. Place machine-local identity files in `tools/gw/src/` if missing (these are excluded from git):
```bash
cp /path/to/credentials.json tools/gw/src/credentials.json
cp /path/to/token.json tools/gw/src/token.json
```
4. Run initial GW authentication (required when token is absent, expired, or rotated):
```bash
tools/gw/bin/gw setup --config tools/gw/src/credentials.json
```

Daily operations:
- Pull and sync code changes with MAS scripts; GW logic updates are distributed through GitHub.
- Keep machine identity local (credentials + token) and out of git.
- Use `tools/gw/bin/gw ...` for Google Workspace actions; source updates in `tools/gw/src/` are automatically consumed by the wrapper.
- Keep the `tools/gw/src/venv` environment local to each machine so runtime behavior is portable while account identity remains isolated.

## Golden Skill Template

Each skill in `/skills/[skill-name]/` is expected to include:

```text
skill-folder/
├── SKILL.md
├── advanced/advanced.md
├── examples/
├── references/
│   ├── schemas.json
│   ├── api-specs.md
│   ├── old-patterns.md
│   └── changelog.md
├── scripts/
└── .workdir/tasks/
```

## Core Operating Model

Each skill follows:
1. Fail-fast Decision Tree checks before execution.
2. Persistent Task ID checkpoints in `.workdir/tasks/{{task_id}}/state.jsonl`.
3. Five-phase workflow:
   - Phase 1: ingestion and checkpointing
   - Phase 2: logic and reasoning
   - Phase 3: drafting and asynchronous gates
   - Phase 4: finalization/resume
   - Phase 5: self-correction and auditing
4. Learning loop via `references/old-patterns.md`.
5. Intelligence floor via `engine.min_reasoning_tier`, `engine.preferred_model`, and `engine.context_required`.
6. CLI-first tooling protocol with strict API/MCP exception handling.
7. Versioned updates via `version`, `release_tag`, and `references/changelog.md`.

Task ID convention:
- `YYYYMMDD-HHMM-<SKILLNAME>-<SHORTUNIX>`

## Skill Architect: 3 Modes

`skill-architect` is the lifecycle engine for skills in `/skills`.

1. `SCAFFOLD`
- Create a new skill from plain-English requirements.

2. `REVERSE_ENGINEER`
- Convert third-party prompts/skills into LiNKskills-compliant structure.
- Includes structural audit: tool extraction, 5-phase mapping, Decision Tree injection, failure-mode seeding.

3. `REFINER`
- Improve existing skills using:
  - execution ledger patterns,
  - `old-patterns.md` lessons,
  - user-requested feature upgrades,
  - tool/API changes.

## Engine and Capability Policy

Every skill must define an `engine` frontmatter block:

```yaml
engine:
  min_reasoning_tier: high
  preferred_model: gpt-5
  context_required: 128000
```

Global policy lives in `global_config.yaml`:
- `engine.tier_order`: portability tiers (for example `fast`, `balanced`, `high`)
- `engine.model_map`: provider/model mapping per tier
- `engine.environment`: current runtime capability (tier + context window)

This enables:
- cost-aware routing for simpler skills,
- fail-fast prevention when runtime is below required intelligence floor,
- portability when model providers change.

## Global Tooling & Persistence Protocol

All skills generated/migrated/refined in LiNKskills follow:
1. Level 1 - Native CLI first.
2. Level 2 - Wrapper scripts in `scripts/` as default logic path.
3. Level 3 - Direct API only for approved exceptions (high-frequency LLM reasoning, high-serialization DB queries, real-time streaming).
4. Level 4 - MCP only for persistent background/session services.

Persistence pattern:
- phase checkpoints in `state.jsonl`,
- optional flat-file artifacts for heavy payloads,
- seek-based reads in later phases to reduce context loading.

Smart JIT loading:
- activate only when profile is `Generalist` or tool count is greater than 10,
- require capability summaries in SKILL docs,
- require `get_tool_details` and local schema caching when JIT is active.

Required frontmatter for this policy:

```yaml
tooling:
  policy: cli-first
  jit_enabled_if: generalist_or_gt10_tools
  jit_tool_threshold: 10
  require_get_tool_details: true
```

## Validation and Health Analytics

Validate a skill:

```bash
python3 validator.py --path skills/<skill-name> --repo-root .
```

Generate global health report:

```bash
python3 global_evaluator.py --root .
```

Validate all skills and tools recursively:

```bash
python3 validator.py --repo-root . --scan-all
```

`validator.py` enforces:
- schema-based frontmatter checks (`version`, `release_tag`, `engine`, `tooling`, permissions, persistence),
- required files/directories (including resumability paths),
- contract pointer integrity (`#/definitions/...`),
- state and trace artifact checks (`state.jsonl`/`state.json`, `trace.log`),
- intelligence-floor checks against `global_config.yaml` runtime tier/context,
- tooling protocol checks (`cli-first`, JIT threshold, `get_tool_details` policy),
- ledger format and Task ID convention consistency,
- recursive compliance checks for `/skills` and `/tools`.

Global tools policy:
- Skills must prioritize tools from `/tools`.
- If a required tool is missing, use `/skills/tool-architect` to create it before execution.

`global_evaluator.py` reports:
- run volume per skill,
- failure and HITL pause rates,
- missing changelog/coverage flags,
- priority candidates for refinement.

## Operator vs Developer Paths

Non-technical operator:
- start at `OPERATOR_BRIEFING.md`,
- request work through `skill-architect` mode prompts.

Developer/maintainer:
- update skill files and contracts directly,
- run validator and evaluator before accepting changes.

## Security and Governance

- Local-first data model (`.workdir/` and logs remain local).
- Permission controls are defined in `global_config.yaml`.
- Drift prevention through:
  - skill-local `references/old-patterns.md`,
  - root `global_blacklist.md`,
  - mandatory validation checkpoints.
