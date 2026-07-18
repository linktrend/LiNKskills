# LiNKskills — how consumer Programs load skills

Owner: LiNKtrend Platform  
Last updated: 2026-07-18  
Status: Implemented (`lib/skill_runtime`, `catalog/index.json`)

## Decision

Consumers do **not** call a long-lived LiNKskills API for skill text. Skills are
**git-backed progressive-disclosure packages**. The shared Supabase `lskills`
schema holds certification + telemetry + eval runs; it does not replace the
files.

```
Consumer Program
  │
  ├─ 1. Sync LiNKskills checkout (full or sparse: skills/ + catalog/)
  ├─ 2. Read catalog/index.json  → discover skill_id, version, paths
  ├─ 3. Optional: overlay certification_state from lskills.catalog (usable filter)
  ├─ 4. Load skills/<id>/SKILL.md (+ advanced/examples/references/scripts as needed)
  └─ 5. After run: lib.skill_runtime.record_invocation → local ledger + lskills.telemetry
```

## Why not an API server?

ADR 0001 retired the Logic Engine control plane. Skill *instructions* are
versioned files; hosting them behind an API would add a chokepoint without
adding permission-to-act (which belongs in each Program Ledger +
`platform.capability_grants`).

## Integration steps for a Program

1. **Pin a SHA** of `linktrend/LiNKskills` (prefer `main` after promotion).
2. On the VPS / agent host, keep a checkout (or CI-synced sparse tree).
3. Set `PYTHONPATH` to include the repo root (or vendor `lib/skill_runtime`).
4. Resolve skills:

```python
from lib.skill_runtime import load_skill, record_invocation, InvocationEvent

bundle = load_skill("git-safeguard", repo_root="/opt/linkskills", require_usable=False)
instructions = bundle.skill_md.read_text()

record_invocation(
    InvocationEvent(
        skill=bundle.skill_id,
        skill_version=bundle.version,
        status="completed",
        summary="Ran pre-push checklist",
        task_id="20260718-1700-GITSAFE-123456",
        agent_id="sites-worker",
        program_ref="lsites",
    ),
    repo_root="/opt/linkskills",
)
```

5. Until the Librarian certifies skills, `require_usable=False` is correct —
   certification_state in DB is still `draft` for the seeded catalog. When you
   want the hard quality gate, set `require_usable=True` (or filter
   `list_skills(..., usable_only=True)`).

## Regenerating the index

```bash
python3 scripts/build-catalog-index.py
python3 scripts/build-catalog-index.py --check   # CI freshness gate
```

## Telemetry flush

Local `execution_ledger.jsonl` is always written. When
`LINKTREND_PLATFORM_STAGE_SUPABASE_URL` + secret key (or prod pair) are set,
`record_invocation` also inserts into `lskills.telemetry`. To drain a buffer:

```bash
python3 scripts/flush-telemetry.py
```

## What this is not

- Not a lease / entitlement check
- Not a substitute for Program Ledger gates
- Not the Librarian itself (that lives in `LiNKplatform/packages/librarian-runner`)
