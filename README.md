# LiNKskills Library

LiNKskills is the Venture Studio's governed skill-and-tool operating layer and now includes the Phase 0-3 Logic Engine control-plane implementation for PRD v4.0 MVO Class A.

## Source of Truth Documents
- PRD v4.0 (MVO): [`260319 LiNKskills PRD.md`](./260319%20LiNKskills%20PRD.md)
- Legacy/earlier PRD draft: [`PRD_LINKSKILLS_LOGIC_ENGINE.md`](./PRD_LINKSKILLS_LOGIC_ENGINE.md)
- Master SOP (original): [`SOP.md`](./SOP.md)
- Master SOP (updated after implementation): [`SOP_MVO_CLASS_A.md`](./SOP_MVO_CLASS_A.md)

## Updated Operating Documents (Do Not Replace Originals)
- Operator briefing (original): [`OPERATOR_BRIEFING.md`](./OPERATOR_BRIEFING.md)
- Operator briefing (updated): [`OPERATOR_BRIEFING_MVO_CLASS_A.md`](./OPERATOR_BRIEFING_MVO_CLASS_A.md)
- Human SOP (original): [`SOP_HUMAN.md`](./SOP_HUMAN.md)
- Human SOP (updated): [`SOP_HUMAN_MVO_CLASS_A.md`](./SOP_HUMAN_MVO_CLASS_A.md)
- Machine SOP (original): [`SOP_MACHINE.md`](./SOP_MACHINE.md)
- Machine SOP (updated): [`SOP_MACHINE_MVO_CLASS_A.md`](./SOP_MACHINE_MVO_CLASS_A.md)

## Comprehensive Delivery Record
- Full implementation dossier (Phase 0-3): [`LiNKskills PRD v4.0 Implementation Dossier (Phase 0-3).md`](./LiNKskills%20PRD%20v4.0%20Implementation%20Dossier%20(Phase%200-3).md)

## Logic Engine Service
- Service root: [`services/logic-engine`](./services/logic-engine)
- Service README: [`services/logic-engine/README.md`](./services/logic-engine/README.md)

## Core Commands
- Full repo validation:
  - `python3 validator.py --repo-root . --scan-all`
- Frontmatter immutability check:
  - `bash scripts/ci-check-frontmatter.sh`
- Build Logic Engine catalog:
  - `python3 services/logic-engine/scripts/build_registry.py --repo-root . --output services/logic-engine/generated/catalog.json --packages services/logic-engine/config/packages.json`
- Run Logic Engine API:
  - `python3 services/logic-engine/scripts/run_api.py`
- Run retention worker:
  - `python3 services/logic-engine/scripts/run_retention_worker.py`

## Security Prerequisite
- `export LSL_MASTER_KEY="<your-master-key>"`
