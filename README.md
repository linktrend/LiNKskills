# LiNKskills

> Production status: the pre-configuration engineering baseline is complete. See [the production-readiness index](docs/PRODUCTION-READINESS.md) for remaining configuration, staging, deployment, and operational acceptance work.

LiNKskills is LiNKtrend's **centralized skill catalog and procedural-capability platform**. It provides progressive-disclosure skills, a mandatory per-skill eval suite executed by a real Eval Runner, published delivery through a `skills_*` MCP/HTTP Gateway, usage telemetry, and Librarian curation — and deliberately does **not** own governance or permission-to-act.

## Start here (source of truth)

These documents are the current, authoritative description of this Program. If anything elsewhere in this repo (including older docs under `docs/archive/`) disagrees with them, **these win**:

- **[`docs/LINKSKILLS-INTENT.md`](docs/LINKSKILLS-INTENT.md)** — why LiNKskills exists, who it's for, scope, and what "done" means.
- **[`docs/LINKSKILLS-TECHNICAL-PRD.md`](docs/LINKSKILLS-TECHNICAL-PRD.md)** — the exhaustive technical reference: architecture, packages, Gateway/MCP, eval, telemetry, compatibility load path, Librarian split, and what is / isn't live.
- **[`docs/LINKSKILLS-OPERATIONS-MANUAL.md`](docs/LINKSKILLS-OPERATIONS-MANUAL.md)** — a plain-English handbook for the Principal: what your role is and what isn't fully live yet.
- **[`docs/OPEN-ISSUES.md`](docs/OPEN-ISSUES.md)** — append-only engineering build log and open/deferred items.
- **[`docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md`](docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md)** — approved internal-launch architecture and phased plan (SHA-256 `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`).

Still-live supporting docs (not archived):

- [`docs/adr/0001-retire-logic-engine-governance-layer.md`](docs/adr/0001-retire-logic-engine-governance-layer.md) through [`docs/adr/0008-librarian-ownership-cross-repo-contract.md`](docs/adr/0008-librarian-ownership-cross-repo-contract.md) — accepted ADRs (scope boundary + launch architecture).
- [`docs/runbooks/PRODUCTION_OPERATIONS.md`](docs/runbooks/PRODUCTION_OPERATIONS.md) — VPS/host checkout bootstrap (compatibility / source hosts).
- [`docs/integrations/`](docs/integrations/) — Cursor project canary notes; Codex/OpenClaw handoff notes.

## Scope boundary (important)

LiNKskills does **not** own governance or permission-to-act. It has no entitlements, leases, kill-switches, financial ledger, or per-tenant policy. Permission-to-act lives in **each Program's own Program Ledger** and in **`platform.capabilities` / `platform.capability_grants`** (LiNKplatform). The earlier Logic Engine control plane is retired — see ADR 0001 and [`archive/logic-engine-2026-07-14/`](archive/logic-engine-2026-07-14/).

LiNKbrain remains a **separate** service (`brain_*`). There is no combined Brain/Skills Gateway.

## Layout

- `skills/` — progressive-disclosure skill packages (`SKILL.md` + `advanced/` / `examples/` / `references/` / `scripts/`). Authoring meta-skills: `skill-architect`, `skill-template`, `tool-architect`. Librarian instructions: `self-improvement`.
- `catalog/index.json` — machine discovery index for source/migration (regenerate with `python3 scripts/build-catalog-index.py`).
- `packages/` — internal-launch domain packages:
  - `contracts` — versioned schemas / fixtures
  - `core` — policies, lifecycle, disclosure, certification rules
  - `publisher` — Git → immutable bundle
  - `eval_runner` — real eval execution (**rejects prompt-only certification**)
  - `tool_runtime` — tool descriptors / invocation adapters
  - `gateway` — stdlib HTTP Gateway (`skills_*` operations)
  - `mcp_server` — `skills_*` MCP adapter over the same service
  - `client` — API client, offline buffer, compatibility wrappers
  - `librarian_domain` — Skills-specific Librarian domain worker
- `lib/skill_runtime/` — **compatibility** consumer Python package (catalog, loader, telemetry) during the migration window — **not** the final sole load path.
- `configs/fragments/` — Cursor project-scoped canary example; Codex/OpenClaw fragments (**handed off, not applied here**).
- `validator.py` — structural Golden Template + eval-suite gate (CI).
- `supabase/migrations/` — `lskills` catalog / telemetry / eval_runs + additive `20260727_000005` registry foundation (**LiNKplatform alone applies live**).
- `tools/` — global CLI tool packages (`gws`, `ltr`, …).
- `docs/archive/` — superseded documentation retained for history (including `docs/archive/legacy-root/` for former root PRD/SOP/operator docs).
- `archive/logic-engine-2026-07-14/` — retired governance subsystem (do not deploy).
- `evidence/` — runtime-consumed certification evidence. It intentionally remains at the repository root because code, tests, and migrations bind to these paths.

## Consumer delivery

**Steady-state (internal launch):** Programs and actors use the in-repo **stdlib** Gateway / `skills_*` MCP surface (Platform auth uses **fakes until Platform publishes**). See Technical PRD §§1, 6, 10.

**Compatibility / migration:** Programs may still load skills from a **git checkout** via `lib/skill_runtime`:

```python
from lib.skill_runtime import load_skill, record_invocation, InvocationEvent

bundle = load_skill("git-safeguard", repo_root="/opt/linkskills", require_usable=False)
# ... use bundle.skill_md ...
record_invocation(InvocationEvent(skill=bundle.skill_id, status="completed", summary="..."), repo_root="/opt/linkskills")
```

Full load-path, Gateway operations, telemetry, and Librarian relationship: Technical PRD §§5–7, 10.

## Core commands

```bash
python3 validator.py --repo-root . --scan-all
python3 scripts/build-catalog-index.py
python3 scripts/build-catalog-index.py --check
./scripts/run-sealed-linux-certify.sh   # sealed local Docker+bwrap certification (not stage)
python3 -m unittest discover -s tests/skill_runtime -v
# Internal-launch packages (pytest discovers tests/; archive/ excluded via pytest.ini):
PYTHONPATH="packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:." \
  python3 -m pytest -q
python3 scripts/flush-telemetry.py
python3 scripts/check-service-ownership.py
```

For a long-lived Gateway host, install `packages/tool_runtime` before
`packages/gateway`; it provides the `skills_tool_invoke` descriptor/invocation
runtime and its PyYAML dependency. Install `packages/client` before
`packages/mcp_server`, which declares the client as a required dependency. The
exact host sequence is in
[`docs/runbooks/PRODUCTION_OPERATIONS.md`](docs/runbooks/PRODUCTION_OPERATIONS.md).

## Status

**Current source state (2026-08-11):** `main`, `staging`, and `development`
contain the same source tree. The Skills Gateway is running on the VPS and the
current Lisa/OpenClaw release reaches it through the native Skills bridge. The
catalog, validator, Gateway/MCP packages, certification paths, and IDE
Development rollout are on the integration branches.

This is real service-integration evidence, but it is not permission to infer a
specific deployed LiNKskills commit from health alone. Record the exact Skills
checkout SHA whenever it is next deployed or audited.

The generic Librarian host remains in
**`LiNKplatform/packages/librarian-runner`**. LiNKskills owns its skill-domain
logic, catalog, contracts, and evidence; LiNKplatform owns live hosting and
migration application.
