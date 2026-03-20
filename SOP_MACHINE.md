# SOP_MACHINE

Machine-facing operating protocol for AI-to-AI orchestration in the LiNKskills Library.

## 1. Mission
- Maintain deterministic, auditable, and resumable multi-agent execution.
- Enforce protocol consistency across skills and tools.
- Protect secrets and data integrity under Fortress constraints.

## 2. AI-to-AI Orchestration Protocol
- Source of routing truth:
  - `manifest.json` for registry membership.
  - `configs/service_ownership.json` for `gws` vs `ltr` service ownership.
  - Skill `SKILL.md` frontmatter for engine/tooling/persistence policies.
- Mandatory execution lifecycle:
  1. Ingestion & checkpointing.
  2. Logic & reasoning.
  3. Drafting and async gate.
  4. Finalization.
  5. Self-correction and audit.
- Resumability contract:
  - Use `.workdir/tasks/{{task_id}}/state.jsonl` per skill.
  - Preserve trace logs in task folders.

## 3. 08:00 Executive Sync Ritual
- Local time standard: Asia/Taipei.
- Daily sync flow:
  - 06:00: Start data collection from department lead artifacts.
  - 06:00-07:30: Consolidate wins, blockers, and financial status.
  - 07:30-07:55: Apply compliance and quality checks.
  - 08:00: Publish executive briefing package.
- Required sections:
  - Wins
  - Blockers
  - Financial Health

## 4. Database Access Protocols
- Primary schemas:
  - `lsl_finance` for financial transactions and rollups.
  - `lsl_memory` for notes, audit logs, and asset metadata.
- Write requirements:
  - All finance transaction records must be canonical and traceable.
  - Asset metadata must include source/path/time identifiers.
- Read requirements:
  - Prefer narrow queries and seek-based retrieval.
  - Avoid full-table context loading unless explicitly required.

## 5. Vault Access Protocols
- Secret source: Vault only (`tools/vault` or `ltr vault ...`).
- Master key requirement:
  - `LSL_MASTER_KEY` must be set before secret operations.
- Logging policy:
  - Never print raw secrets to logs or outputs.
  - Log only secret key names and operation status.

## 6. Compliance & Safety Controls
- Do not execute write actions before contract checks pass.
- Do not bypass disclosure/safety gates for channel/content outputs.
- For unresolved high-risk states, set `PENDING_APPROVAL` and stop.

## 7. Failure Handling
- On tool failure:
  - Emit deterministic JSON error payload.
  - Preserve checkpoint and trace artifacts.
  - Provide minimal retry/remediation directive.
- On missing critical context:
  - Fail fast, request exact missing fields, and avoid speculative execution.

## 8. Validation Gate
- Registry conformance command:
  - `python3 validator.py --repo-root . --scan-all`
- Expected outcome:
  - Zero validation errors before release or handoff.
