# LiNKtrend Development Standards

This file provides universal guidance for any AI agent or IDE working in this repository.
For full rules, see `.cursor/rules/` (Cursor) or `.agent/` (Antigravity).

## Identity

LiNKtrend is an AI-native venture studio. The Principal is the sole human operator (non-technical).
All other roles are AI agents. See `.cursor/rules/00-identity.mdc` for full context.

## Repository scope

LiNKskills is the studio's **centralized skill catalog**: catalog + mandatory eval-suite +
usage telemetry, curated by the Librarian process. It does **not** own governance or
permission-to-act — no entitlements, leases, kill-switches, financial ledger, or per-tenant
policy. Those live in each Program's own Program Ledger and in
`platform.capabilities` / `platform.capability_grants` (LiNKplatform repo). See
`docs/adr/0001-retire-logic-engine-governance-layer.md`. Authoritative product docs:
`docs/LINKSKILLS-INTENT.md`, `docs/LINKSKILLS-TECHNICAL-PRD.md`,
`docs/LINKSKILLS-OPERATIONS-MANUAL.md`, `docs/OPEN-ISSUES.md`.

## Git Workflow (LiNKdev-aligned)

- **Integration branch:** `development` — all agent and ad-hoc work lands here via PR.
- **Branch prefixes:** `issue/<id>-<slug>` (LiNKdev issues) or `dev/<machine><ide>` (ad-hoc IDE work).
- **Flow:** `issue/*` or `dev/*` → PR to **`development`** → Integrator merges when merge-ready.
- **Promotion:** `development` → `staging` → `main` — **Principal only** (after Release OK).
- No direct pushes to `staging` or `main`.
- Conventional commits: `type(scope): summary`.
- Forks (`link-*`): modify freely, never push upstream. Upstream sync lands in `development`, not `staging`.

## Secrets

- All secrets in Google Secret Manager (GSM)
- Naming: `LINKTREND_[SERVICE]_[ENV]_[RESOURCE]_[IDENTIFIER]`
- Never commit secrets. Use `${ENV_VAR}` placeholders.

## Quality

- TypeScript strict mode. ESLint + Prettier mandatory.
- Tailwind CSS for styling. shadcn/ui for primitives.
- Complete, shippable code only — no placeholders or TODOs.
- All exports require JSDoc.

## Agent Behavior

- **Autonomous execution:** Run terminal commands, tests, and linters yourself; deliver work end-to-end. Do not instruct the Principal to run routine dev commands unless execution is impossible in-session (missing auth, blocked network, policy, or UI-only step). See `.cursor/rules/05-agent-behavior.mdc`.
- Plan before coding (Batch Header: scope, inputs, plan, risks) — then **implement** unless the batch is approval-gated or the user asked for plan-only.
- Small, incremental changes.
- Ask max 3 questions, then proceed with stated assumptions.
- On failure, generate a Briefing Pack (structured 12-section report).
- Communicate in plain English for the non-technical Principal; “next steps” = what you finished + human-only gaps, not a generic todo list for the operator.

## Other LiNKtrend repositories

The canonical **`05-agent-behavior.mdc`** and this **`AGENTS.md`** template are copied across LiNKtrend repos in the operator’s `Projects` tree so Cursor/Codex/Antigravity behave consistently. **New** repos should copy `.cursor/rules/05-agent-behavior.mdc` and `AGENTS.md` from LiNKaios (or any sibling that already has them) before the first agent session.

## Handoff

- Write handoff docs to `docs/handoffs/` when finishing a session.
- Read latest handoff before starting work on a branch.

## Testing

- Unit (Vitest), Integration (Vitest + mock), E2E (Playwright for web).
- Every feature/fix ships with tests. Regression tests for bugs.

## Skills

This repo includes skills in `.cursor/skills/`, `.agent/skills/`, and `.codex/skills/`.
Skills are loaded automatically based on task context.

<!-- BEGIN LINKTREND-IDE-MANAGED -->
## LiNKtrend IDE-managed development system (do not edit between markers)

This section is maintained by LiNKtrend install/sync tooling. Repository-owned guidance may live **outside** these markers.

Installed managed core: **`.ide-development/`** (versioned package; treat as read-only except via the official installer).

### Session entrypoints

- **New coding session:** follow **agentsetup** — create/reuse the GitHub issue and `issue/<n>-<slug>` via `python3 scripts/gitops/create_issue_branch.py`. Never ask humans for issue id/slug.
- **Already-open / wrong branch:** follow **agentcomply** — migrate dirty work onto the correct `issue/*` branch for this repo.
- **Codex / ChatGPT Work Agents:** use this root `AGENTS.md` managed section and physical `.agents/skills/<name>/SKILL.md`. Do **not** require `.cursor` to be loaded.
- **Cursor:** use physical `.cursor/commands/agentsetup.md` / `agentcomply.md` and `.cursor/skills/`.

### Lifecycle

- Work on `issue/<n>-<slug>` (or rare `dev/*`) → push checkpoint → Packager opens draft PR → Integrator merges to `development`.
- Promote: `development` → `staging` → `main` via temporary `promote/*` PRs only.

### Agent rules

- Ship = checkpoint (commit + push). Packager opens PRs. Max 3 ordinary repairs.
- Completion: `python3 scripts/gitops/completion_gate.py` (`checkpoint` | `review-ready` | `blocked` | `status` | `write-evidence`).
- Finished work: run appropriate tests/checks, auto-repair ordinary failures (≤3 cycles), `write-evidence`, then `review-ready`.
- `review-ready` validates evidence then publishes **Linktrend Review Ready** only via the privileged App path (or fails closed with App-backed dispatch diagnostics). Do not call `mark-review-ready.sh` as a pre-gate publisher.
- If completion cannot pass, call `completion_gate.py blocked`.
- Hard stops: no implementer PR, no self-merge, no self-review, no staging/main promotion, no prefer-incoming.

### Deeper doctrine

When needed, open files under `.ide-development/` (and local `docs/` / `scripts/` already installed). Prefer progressive disclosure; do not scan the entire package.
<!-- END LINKTREND-IDE-MANAGED -->
