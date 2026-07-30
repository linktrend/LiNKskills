# Provisional Implementation Handoff — LiNKskills Internal Launch Plan

**Status:** Provisional Grok execution report. **Not** independently verified. Ask the Principal to return this to the LiNKskills Codex verifier.

**Date:** 2026-07-27
**Executor:** Cursor Local Agent (Grok 4.5 High)
**Issue:** https://github.com/linktrend/LiNKskills/issues/21
**Branch:** `issue/21-linkskillsdevelopmentplan01`
**Repo:** `/Users/linktrend/Projects/LiNKskills`
**Session:** `docs/agent-sessions/active/20260727-cursor-grok-issue21-linkskillsdevelopmentplan01.md`

## Contract hashes consumed

| Artifact | SHA-256 |
|---|---|
| Approved plan `docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md` | `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88` (verified match at start) |
| Execution prompt | `9492e4ef8232d1f4d8fe3752092fe04e636c7e8a1f575feafe3014a00681985e` |
| Planning handoff | `9261fbcaafd459678d63956669ccea196f19d6702c0bc58a3ca44a1d85e6d141` |
| Migration `20260727_000005_lskills_registry_foundation.sql` | `aff99da2751ab26fd96a13ed03880bea674e5955533c0df4fae8b418de7ab623` |
| Canary suite profile (CLI) | see `evidence/phase3/canary-echo-cli.txt` (`profile_hash` `70b6cc98…053d`) |

Schema file hashes: compute via `shasum -a 256 packages/contracts/schemas/*.json` (recorded in executor session; verifier should recompute).

## Phases claimed (LiNKskills-owned)

| Phase | Classification | Notes |
|---|---|---|
| 0 ADRs + SoT + inventories + gates | implemented and proven (docs/local) | ADRs 0002–0008; inventories; contracts; SoT updated |
| 1 Skill Pack/eval schemas + audits | implemented and proven (local) | 12 schemas; suite/tool audits; canary set of 10 |
| 2 Publisher + migration package | implemented but not proven live | Bundle publisher + additive SQL + manifest; **not applied** |
| 3 Eval Runner + tool runtime | implemented and proven (local/deterministic) | Prompt-only reject proven; canary-echo certified |
| 4 Gateway + MCP + client | implemented and proven (local/fake auth) | HTTP/MCP parity tests; fake Platform claims |
| 5 Telemetry/feedback/trace | partially implemented | Offline buffer + redaction smoke; full live spine not stage-proven |
| 6 Librarian domain worker | implemented and proven (local conformance) | Worker + policies; host integration is LiNKplatform |
| 7 Cursor canary | partially implemented | Stage 1 fake/contract only; **no global Cursor mutation** |
| 8 Codex fragment | implemented differently / blocked on owner | Fragment + handoff docs only; shared config is LiNKbrain |
| 9 OpenClaw fragment | implemented differently / blocked on owner | Fragment + handoff docs only; no OpenClaw edits |
| 10 General launch closeout | partially implemented | Classification draft only; no live usable promotions |
| 11 Independent verification | outside ownership | Codex verifier must run |

## Intentionally untouched ownership boundaries

- LiNKplatform shared Supabase live apply / credentials / generic `librarian-runner` shared files
- LiNKbrain shared Codex `config.toml` / common hooks
- openclaw_prime / Lisa profile, plugins, managed MCP
- Global Cursor user settings / shared `.cursor` symlink targets
- Production promotion (`staging`/`main`)

## Commands / tests actually run

```bash
export PYTHONPATH="packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:."
.venv/bin/python -m pytest tests/contracts tests/core tests/publisher tests/eval_runner tests/tool_runtime tests/gateway tests/mcp_server tests/client tests/librarian_domain tests/skill_runtime -q
# Result: 60 passed

python3 validator.py --repo-root . --scan-all   # passed (legacy ledger retention warnings only)
python3 scripts/build-catalog-index.py --check  # current (34 skills)
python3 scripts/audit-skill-suites.py
python3 scripts/audit-tool-packages.py
.venv/bin/python -m linkskills_eval_runner run evidence/phase3/fixtures/canary-echo/eval-suite.yaml
# certified=true
```

## Evidence index (for Codex verifier)

- `docs/adr/0002` … `0008`
- `docs/inventories/*`
- `docs/contracts/*`
- `docs/migrations/MANIFEST-20260727-lskills-registry-v0.1.md`
- `docs/integrations/{cursor,codex,openclaw}/`
- `configs/fragments/*`
- `evidence/phase1/suite-audit.json`, `tool-audit.json`, `canary-set.json`
- `evidence/phase3/fixtures/canary-echo/`, `canary-echo-cli.txt`
- `evidence/phase5/event-spine-smoke.json`, `offline-buffer-smoke.jsonl`
- `evidence/phase7/cursor-canary-status.json`
- `evidence/phase10/skill-classification-draft.json`
- Package sources under `packages/*` and tests under `tests/*`

## Live actions performed

| Action | Operator | Result |
|---|---|---|
| Create GitHub issue #21 | LiNKskills Grok executor | Done |
| Create/push branch `issue/21-linkskillsdevelopmentplan01` | LiNKskills Grok executor | Done |
| Apply shared live migrations | — | **Not performed** (Platform gate) |
| Mutate global Cursor / Codex / Lisa | — | **Not performed** |
| Promote to staging/main | — | **Not performed** |

## Blockers / handoffs required

1. **Identity gate:** Platform must publish canonical actor/auth contract; replace fakes.
2. **Migration gate:** Platform reviews/applies `MANIFEST-20260727-lskills-registry-v0.1.md`.
3. **Librarian gate:** Platform integrates `packages/librarian_domain` / `docs/contracts/librarian-domain-worker-v0.1.md`.
4. **Codex gate:** LiNKbrain applies `configs/fragments/codex-skills.config.toml.fragment` after Skills readiness.
5. **OpenClaw gate:** OpenClaw Prime implements from `configs/fragments/openclaw-skills.mcp.json.fragment` + handoff.
6. **Cursor stages 3–8:** need stage environment + maintenance window if any global change becomes unavoidable.
7. **Verification gate:** LiNKskills Codex verifier must classify every plan item independently.

## Reproduction

```bash
git checkout issue/21-linkskillsdevelopmentplan01
export PYTHONPATH="packages/contracts:packages/core:packages/publisher:packages/eval_runner:packages/tool_runtime:packages/gateway:packages/mcp_server:packages/client:packages/librarian_domain:."
.venv/bin/python -m pytest tests/contracts tests/core tests/publisher tests/eval_runner tests/tool_runtime tests/gateway tests/mcp_server tests/client tests/librarian_domain tests/skill_runtime -q
python3 validator.py --repo-root . --scan-all
.venv/bin/python -m linkskills_eval_runner run evidence/phase3/fixtures/canary-echo/eval-suite.yaml
```

## Rollback

- Discard/revert the issue branch PR; packages are additive.
- Do not apply migration `000005` if not yet applied; if applied, Platform owns down-migration per manifest.
- Remove project-scoped Cursor fragment only (none was installed globally by this session).

## Residual risks / omissions

- Most of the 34 suites remain prompt-oriented; only canary-echo proves full deterministic certification path.
- Gateway uses fake auth and in-memory/catalog-backed state — not production hosting.
- Skill Pack v0.1 schemas exist; bulk migration of all 34 skills’ frontmatter to typed deps is not complete (audit + helpers only).
- CI workflow may still emphasize legacy skill_runtime tests; verifier should confirm CI includes new package tests or file a follow-up.
- This report is provisional.

## Ask of Principal

Return to the **LiNKskills Codex planning/verifier agent** for independent verification. Do not declare the four-repository program complete from this handoff alone.

---

## Amendment 2026-07-28 — certification path withdrawn / replaced

**Supersession:** The Phase 3 canary certification claim in this handoff (`profile_hash` `70b6cc98…053d`, suite-authored `observed_output` as evidence, Gateway `live_echo`) is **invalid and withdrawn**.

See correction handoff: `docs/handoffs/2026-07-28-grok-certification-path-correction.md`.

Replacement canary (executor receipts required):
- `suite_hash` `a564173690b0745271d34991c69c8234039305501a4fccedaadf0954ac71a50a`
- `profile_hash` `67f17eb8a5c2301b709385c5897fca0367e290d4d6327508c1acd52527668a32`
- receipts `121d8ef6…bcc8a1`, `fbb425a5…8009a`

Do not begin the multi-day Cursor canary until certification + Platform gates pass independent Codex re-verification.

## Amendment 2026-07-28 — wave 2 / wave 3

Wave-1 replacement profile/receipts above were **again withdrawn** in wave 2 (non-deterministic profile / unset release). Current sealed canary identity is in `docs/handoffs/2026-07-28-grok-certification-correction-wave2.md`.

Wave 3 (`docs/handoffs/2026-07-28-grok-certification-correction-wave3.md`) addresses all remaining actionable PR #22 review threads (buffer/flush, librarian/core receipt-bound cert, MCP identity, run-start gates, fragments, README). Still provisional — return to Codex; do not merge PR #22; do not start multi-day Cursor canary.

## Amendment 2026-07-28 — wave 4

Unsigned production verifier path withdrawn. See `docs/handoffs/2026-07-28-grok-certification-correction-wave4.md`. Still provisional for Codex; do not merge/deploy/canary.
