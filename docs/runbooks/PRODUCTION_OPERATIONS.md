# LiNKskills VPS / host deploy (post–Logic Engine)

Owner: LiNKtrend Platform  
Last updated: 2026-07-18

## What runs where

LiNKskills is **not** a long-lived API service. After ADR 0001:

| Component | Where it lives | Notes |
|---|---|---|
| Skill files (`skills/`, `catalog/index.json`) | Git checkout on agent host / VPS | Consumer Programs sync a pinned SHA |
| `lskills.*` tables | Shared Supabase (`linkplatform-stage` / `linkplatform-prod`) | Catalog certification, telemetry, eval runs |
| Librarian agent | `LiNKplatform/packages/librarian-runner` | Nightly systemd timer (or cron); not this compose file |
| Local telemetry buffer | `execution_ledger.jsonl` on the host | Flushed via `scripts/flush-telemetry.py` |

The retired Logic Engine FastAPI stack under `services/logic-engine/` is archived
and must **not** be started.

## Host bootstrap

1. Clone `linktrend/LiNKskills` and check out a pinned tag/SHA from `main`.
2. Install Python 3.11+.
3. Copy `deploy/vps/.env.example` → `deploy/vps/.env` and fill non-secret values +
   GSM secret *names* only.
4. Render runtime secrets (optional, when GSM available):

```bash
./deploy/vps/render-env-from-gsm.sh
set -a && source deploy/vps/.env.runtime && set +a
```

5. Validate the catalog:

```bash
python3 validator.py --repo-root . --scan-all
python3 scripts/build-catalog-index.py --check
python3 -m unittest discover -s tests/skill_runtime -v
```

6. Point consumer Programs at this checkout (`LINKSKILLS_REPO_PATH` /
   `repo_root=` in `lib.skill_runtime`). See
   [`docs/CONSUMER-SKILL-LOAD-PATH.md`](../docs/CONSUMER-SKILL-LOAD-PATH.md).

## Optional: scheduled telemetry flush

```bash
# Example crontab — every 15 minutes
*/15 * * * * cd /opt/LiNKskills && set -a && . deploy/vps/.env.runtime && set +a && python3 scripts/flush-telemetry.py >> /var/log/linkskills-telemetry.flush.log 2>&1
```

## Librarian (skills half)

Deploy and schedule from **LiNKplatform**, not this repo:

- Package: `LiNKplatform/packages/librarian-runner`
- Units: `packages/librarian-runner/ops/librarian.{service,timer}`
- Set `LINKSKILLS_REPO_PATH` to this checkout
- Prefer `LIBRARIAN_DRY_RUN=true` for the first supervised pass

## Health checks

- `python3 validator.py --repo-root . --scan-all` exits 0
- `catalog/index.json` present and `--check` clean
- Supabase: `select count(*) from lskills.catalog;` ≥ 34 on the target env
- After real invocations: rows appear in `lskills.telemetry`
