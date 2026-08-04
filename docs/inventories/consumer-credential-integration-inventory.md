# Consumer, Credential, and Integration Inventory

- **Status:** Phase 0 inventory (accepted for planning baseline)
- **Date:** 2026-07-27
- **Authority:** `docs/CURSOR-GROK-EXECUTION-PROMPT.md` + approved plan hash `31a6cc70bb778ce1dff236819e4bf600b0495dbb06c95bac55bcb2b0b2f5fe88`
- **Plan refs:** §7.2, §7.6, Phase 0 item 7, §21

## Purpose

Inventory every current LiNKskills consumer path, direct PostgREST/database credential surface, checkout dependency, tool dependency, and Librarian integration so Gateway migration and credential tightening have a named baseline.

## 1. Current consumers

| Consumer | Integration shape today | Target shape | Owner of consumer change |
|---|---|---|---|
| Local / Program Python via `lib/skill_runtime` | Filesystem catalog + checked-out skill dirs; optional PostgREST telemetry | Gateway/MCP/API + published bundles; migration wrapper until cutover | LiNKskills |
| Cursor (product canary) | Not integrated as a Skills service; may mount skills via checkout / shared `.cursor` | Project-scoped MCP → `skills_*`; no checkout required | LiNKskills (canary); shared/global Cursor gated |
| Codex Desktop | Not Skills-service integrated | Independently named Skills MCP fragment applied by shared Codex owner | LiNKbrain default shared-config owner; LiNKskills supplies fragment + validates |
| Lisa / OpenClaw Prime | Not Skills-service integrated | Managed MCP + scoped Skills actor credentials; separate from Brain | OpenClaw Prime implementation; LiNKskills contract/fake/conformance |
| LiNKplatform `packages/librarian-runner` | Prompt-oriented Skills scoring against `lskills` via service identity | Versioned Skills domain worker + Eval Runner evidence | LiNKplatform host; LiNKskills domain worker |
| Deploy hosts (`deploy/vps`, `deploy/production`) | Env templates for platform Supabase URL/secret via GSM | Gateway + scoped credentials; no actor-held service-role | LiNKplatform ops for live secrets; LiNKskills defines requirements |

## 2. Checkout dependencies

| Path / pattern | Who depends | Steady-state allowed? |
|---|---|---|
| Pinned LiNKskills Git checkout + `skills/` tree | Current Program/runtime consumers | No — migration only (ADR 0002) |
| `catalog/index.json` / filesystem catalog | `lib/skill_runtime` | Source/build input; published runtime uses registry-derived fragments |
| `tools/` packages | Skills that reference local tool packages | Published via exact tool descriptors/hashes |
| Shared IDE Development `.cursor` symlink | Agent development environment | Not a product consumer; no casual Skills canary edits to shared target |

## 3. Direct PostgREST / credential surfaces

| Surface | Variables / mechanism (names only) | Risk | Disposition |
|---|---|---|---|
| `lib/skill_runtime/telemetry.py` PostgREST writer | `LINKTREND_PLATFORM_{STAGE\|PROD}_SUPABASE_URL` + `*_SECRET_KEY`, or legacy `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`; profiles `lskills` | Broad DB credential on consumer path | Replace with Gateway-mediated telemetry; remove steady-state actor PostgREST credentials after replacement proof |
| Deploy `.env.example` templates | GSM secret *names* for platform Supabase secret keys | Host-held platform secret | Remain ops-only; never distribute to Cursor/Codex/OpenClaw/ordinary consumers |
| Librarian (`svc_lskills_librarian` style) | Platform-issued service identity (host-owned) | Over-broad if reused by actors | Host-only; actors never receive service-role or Librarian credentials |
| Future Gateway actor credentials | Short-lived scoped platform claims | Mis-issuance / wrong scopes | LiNKplatform issues; LiNKskills defines acceptance/rejection (see `docs/contracts/platform-actor-auth-requirements.md`) |

**Rule:** Do not distribute broad database credentials to Cursor, Codex, OpenClaw, or ordinary consumers. Actors never receive Supabase service-role or Librarian credentials.

## 4. Tool dependencies (baseline)

- **19** top-level packages under `tools/` (planning baseline), including wrappers such as `ad-intel`, `asset-filer`, `doc-engine`, `fast-playwright`, `gws`, `ltr`, `memory`, `n8n`, `n8n-bridge`, `playwright-cli`, `research`, `sandbox`, `shopify`, `social-ltr`, `stripe`, `sync-scheduler`, `text-echo`, `usage`, `vault`.
- Skills declare tool needs today with limited typed descriptors; ADR 0005 requires versioned descriptors and exact hash resolution before certification.
- Host-native capabilities (repo/fs/browser) remain host-owned and capability-mapped, not re-homed into LiNKskills governance.

## 5. Librarian integration

| Piece | Location / ownership | Current state | Target |
|---|---|---|---|
| Skill-side workflow instructions | `skills/self-improvement/` (LiNKskills) | Present | Remains doctrinal workflow input |
| Runnable host | `LiNKplatform/packages/librarian-runner` | Prompt-oriented scoring + catalog promotion | Generic host only; no domain-agent edits to shared files |
| Skills domain worker | LiNKskills (to implement) | Not yet versioned as separate package/contract consumer | Own logic/contracts/tests (ADR 0008) |
| Identity | `LiNKplatform/agents/librarian.md` | One identity, Skills + Brain workflows | Same identity; separate domain workers |

## 6. Gaps this inventory does not claim

- Live stage/prod health of applied `lskills` migrations, PostgREST endpoints, GSM-backed secrets, deploy hosts, and Librarian service identities is **unverified** by this document. Presence of SQL under `supabase/migrations/` or env templates under `deploy/` is not live readiness evidence.
- Absence of a Gateway today means “consumer = checkout” is still the operational default until Phase 5+.
- Counts and package lists are planning-baseline (19 `tools/*` packages excluding `tools/README.md`); re-verify before tightening credential access.

## 7. Next inventory actions

1. Keep a migration wrapper for Python checkout consumers until Gateway cutover proof.
2. Enumerate every deploy/runtime that still sets `SUPABASE_SERVICE_ROLE_KEY` / platform secret keys for actor processes.
3. Cut over telemetry writers to Gateway-mediated paths before removing PostgREST actor credentials.
