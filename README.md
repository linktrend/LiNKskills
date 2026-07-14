# LiNKskills Library

LiNKskills is the Venture Studio's **centralized skill catalog**. It is scoped to three
things and one curation process:

1. **Catalog** — the library of progressive-disclosure skills (`SKILL.md` + `advanced/` +
   `examples/` + `references/` + `scripts/`), authored via the `skill-architect` /
   `skill-template` pattern and validated by `validator.py`.
2. **Mandatory eval suite** — every skill ships a baseline eval suite before it is
   `usable` (quality proof, not just an I/O contract).
3. **Usage telemetry** — every real skill invocation is recorded (see
   `execution_ledger.jsonl` and `global_evaluator.py`).
4. **Librarian curation** — the `self-improvement` skill (being promoted to the
   "Librarian") reads telemetry + eval runs and proposes versioned upgrades.

> **Scope boundary (important).** LiNKskills does **not** own governance or
> permission-to-act. It has no entitlements, leases, kill-switches, financial ledger, or
> per-tenant policy. Permission-to-act lives in **each Program's own Program Ledger** and
> in **`platform.capabilities` / `platform.capability_grants`** (the LiNKplatform repo).
> The earlier "Logic Engine" control-plane that added that machinery here has been retired
> — see [`docs/adr/0001-retire-logic-engine-governance-layer.md`](./docs/adr/0001-retire-logic-engine-governance-layer.md)
> and the archived subsystem under [`archive/logic-engine-2026-07-14/`](./archive/logic-engine-2026-07-14/).

## Source of Truth Documents

- Catalog / eval / telemetry design: [`docs/specs/catalog-eval-telemetry-spec.md`](./docs/specs/catalog-eval-telemetry-spec.md)
- Shared foundation (cross-Program substrate): `LiNKplatform/docs/specs/shared-foundation-spec.md` (§3, §7)
- ADR — retiring the Logic Engine: [`docs/adr/0001-retire-logic-engine-governance-layer.md`](./docs/adr/0001-retire-logic-engine-governance-layer.md)
- Original PRD (MVO): [`260319 LiNKskills PRD.md`](./260319%20LiNKskills%20PRD.md)
- Master SOP: [`SOP.md`](./SOP.md)

## Skill Catalog

- Catalogue index: [`SKILLS_CATALOGUE.md`](./SKILLS_CATALOGUE.md)
- Manifest: [`manifest.json`](./manifest.json)
- Skills live under [`skills/`](./skills); authoring meta-skills:
  [`skill-architect`](./skills/skill-architect), [`skill-template`](./skills/skill-template),
  [`tool-architect`](./skills/tool-architect).
- Curation precursor: [`self-improvement`](./skills/self-improvement).

## Google CLI Operating Model (Launch)

- `gws` is the primary Workspace CLI (pinned runtime in [`tools/gws`](./tools/gws)).
- `ltr` replaces legacy `gw` for non-Workspace Google, non-Google, and local runtime controls (in [`tools/ltr`](./tools/ltr)).
- Service ownership source of truth: [`configs/service_ownership.json`](./configs/service_ownership.json).
- Ownership validation gate: `python3 scripts/check-service-ownership.py`.

## Core Commands

- Full repo validation:
  - `python3 validator.py --repo-root . --scan-all`
- Frontmatter immutability check:
  - `bash scripts/ci-check-frontmatter.sh`
- Telemetry aggregation:
  - `python3 global_evaluator.py`

## Documentation Map

- [Docs Index](./docs/README.md)
- [Branching and Deployment Policy](./docs/BRANCHING_AND_DEPLOYMENT_POLICY.md)
- [Documentation Governance](./docs/DOCUMENTATION_GOVERNANCE.md)
- [Architecture Decision Records](./docs/adr/)
- [Archive](./archive/) — retired subsystems retained for traceability
