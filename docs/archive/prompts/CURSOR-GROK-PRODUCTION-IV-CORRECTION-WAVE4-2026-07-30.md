# Cursor Grok 4.5 High — LiNKskills Production IV Correction Wave 4 / Evidence Gate

Continue the existing LiNKskills branch from exact clean HEAD `4c8fd17267c45e2c0139d52d5317044ae6668628`. Use Cursor Grok 4.5 High and only Grok 4.5 High subagents.

Skills-owned Wave 3 functionality passed independent verification: bound identity now controls review-queue RLS, forgery is rejected, GUCs do not leak, and trusted mint-client configuration is present and distinct from the resource-server assertion identity.

## Required now

- Remove trailing whitespace in `docs/contracts/LANE-C-PACKAGED-INTEROP-PREP-2026-07-30.md` and make `git diff --check origin/development...HEAD` pass.
- Correct the Wave-3 handoff through a dated amendment/new handoff so the exact clean HEAD is `4c8fd17267c45e2c0139d52d5317044ae6668628`, not an earlier implementation/docs tip.
- Re-run the focused identity/config and ephemeral Postgres tests; run the full supported-Python suite if practical without CI/Bugbot.
- Platform `ca027417…` failed independent verification. Do not repin to it. Record `AWAITING_CODEX_CERTIFIED_PLATFORM_REPIN`.
- Prepare to resume after a certified Platform descendant is supplied. The continuation must repin exact Platform head/package/tarball/schema/fixtures and run packaged Platform↔Skills interoperability before stage.

No functional code churn unless verification discovers a direct regression. No live migration, deploy, canary, sibling/global Cursor edit, CI/Bugbot polling, PR readiness, merge, promotion, or self-certification.

Return a clean pushed HEAD, changed files, exact tests, corrected evidence, repin state, and provisional handoff for Skills Codex re-verification. Stop there.
