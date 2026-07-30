# LiNKskills OWNER_COUNTERSIGNED — OpenClaw Skills fixtures (AuthClaims 1.1.0 / wave 8)

**Status:** `OWNER_COUNTERSIGNED`
**Scope:** Domain-owner fixture countersign review only. **Not** independent Codex certification. **Not** merge authority for LiNKskills PR #22 or OpenClaw PRs. **Not** canary / deploy / Phase 14 authorization.
**Date / time:** 2026-07-30 07:05 Asia/Taipei

## Reviewer / session identity

| Field | Value |
|---|---|
| Role | LiNKskills domain owner (fixture countersign) |
| Agent type | Cursor Local Agent |
| Model | Grok 4.5 High (`cursor-grok-4.5-high`) |
| Reviewer signature | LiNKskills Cursor Grok 4.5 High — original issue/21 implementation owner |
| LiNKskills branch | `issue/21-linkskillsdevelopmentplan01` |
| LiNKskills PR | https://github.com/linktrend/LiNKskills/pull/22 (**do not merge from this handoff**) |
| Request packet | OpenClaw `docs/execution/openclawdevelopmentplan01/COUNTERSIGN-REQUEST-WAVE8-AUTHCLAIMS-1.1.md` |

## Exact trees attested

| Tree | Exact SHA |
|---|---|
| OpenClaw immutable inspection tip | `005c9454f1bd3f7427936704131ffe5faa95ef0f` |
| OpenClaw branch (observed) | `issue/ocp-openclawdevelopmentplan01` (tip recorded in request; review used `git archive` only — OpenClaw tree not modified) |
| LiNKskills reference HEAD | `ad3613df9295d4be13dfe03effc55706fb9e8f47` |
| Platform source HEAD | `6861a376aae5fa4e12c1b68a808d7b04e7bbfb5b` |
| OpenClaw plan SHA-256 | `17203ee586a3fb2b1281bcddd8b17ae350075ebce537689f3c4bfcbbd14914f7` |
| Sign-off process | `docs/execution/openclawdevelopmentplan01/FIXTURE-OWNER-SIGNOFF.md` (OpenClaw tree) |

## Fixture aggregate (independently recomputed)

Method (from FIXTURE-OWNER-SIGNOFF.md / COUNTERSIGN-REQUEST):

```text
find <fixtures-root> -type f -name '*.json' | sed 's|^\./||' | sort \
  | while read f; do shasum -a 256 "$f" | awk -v f="$f" '{print $1 "  " f}'; done \
  | shasum -a 256
```

| Field | Value |
|---|---|
| Package root | `extensions/linkskills/fixtures` |
| JSON file count | 71 |
| **Recomputed aggregate SHA-256** | `203163711b5db17b8a07d3956e41596384cbd08f0c110bd9f21abfc5c7e5e19a` |
| Expected aggregate | `203163711b5db17b8a07d3956e41596384cbd08f0c110bd9f21abfc5c7e5e19a` |
| Match | **YES** |

## Alignment review vs current LiNKskills authority (`ad3613d…`)

| Check | Verdict |
|---|---|
| Exact `skills_*` surface: 15 tool dirs match `OPERATIONS` in `packages/gateway/linkskills_gateway/service.py`; each has `request.json` / `response.json` / `error.json` | **PASS** |
| `CONTRACT_VERSION` / API label `skills.api.v0.1` with envelope `schema_version`/`contract_version` `0.1` | **PASS** |
| `platform.auth-claims/1.1.0` on positive identity/auth fixtures; `@linktrend/platform-contracts@0.2.2`; Platform HEAD `6861a376…`; schema SHA-256 `c2e8bc68b3feb9a3dacc497f5a5d497b466c400804fb4f9e41734c10772ddfa1`; contentHash `fb518834be897c32574df5f7235704fdb0de708bd3da1b48fc448246e3eca567` (OpenClaw tip schema bytes identical to Platform source) | **PASS** |
| Legacy `platform.auth-claims/1.0.0` retained only as explicit rejection evidence (`identity/legacy-1.0.0-reject.json`) | **PASS** |
| Immutable skill-release / certified-profile semantics (`release_hash`, `execution_profile_hash`, `immutable: true` on release get); withdrawn `live_echo` / `observed_output` path not endorsed on positive fixtures | **PASS** |
| Authentication reject fixtures (expired / revoked / wrong-audience / wrong-scope) under 1.1.0 | **PASS** |
| Structured telemetry privacy boundary; no conversation-bearing payload keys on non-prohibited fixtures | **PASS** |
| Prohibited fixtures hard-reject conversation / prompt / reasoning / message-body / raw tool args-results / brain-findings | **PASS** |
| Validation / failure envelopes present (retryable, terminal, throttled, authentication) | **PASS** |

**Overall:** `OWNER_COUNTERSIGNED`

## Certification-path awareness

LiNKskills continues to require sealed executor receipts, immutable `skill_release_hash`, deterministic execution-profile hashing, and Platform AuthClaims 1.1.0 for live certification work. This countersign accepts the OpenClaw **consumer fixture package** at tip `005c9454…` as aligned with that authority for integration-test / fake-MCP use.

This countersign does **not** independently certify LiNKskills canaries, declare Phase 1 complete, or close LiNKskills Codex re-verification of PR #22 implementation waves.

## Non-blocking notes

1. Fixture `MANIFEST.md` still labels status `PENDING_OWNER_COUNTERSIGN` (wave-8 text). OpenClaw should update `FIXTURE-OWNER-SIGNOFF.md` after recording this owner countersign; LiNKskills did not edit OpenClaw.
2. MANIFEST pins historical Skills HEAD `f16103f…`; this review’s LiNKskills reference HEAD is `ad3613d…`. `OPERATIONS` + `skills.api.v0.1` are unchanged for the inspected surface.
3. MANIFEST layout table says auth “wrong-service”; on-disk file is `wrong-scope.json` (content correctly rejects wrong service scopes). Cosmetic docs drift only.
4. Prior CLOSED countersign of aggregate `8586d89a…` at tip `429a7818…` / prior Skills handoffs remains **historical only** (AuthClaims 1.0.0 positive path superseded).

## Ask of OpenClaw

1. Update `FIXTURE-OWNER-SIGNOFF.md` Skills block to `OWNER_COUNTERSIGNED`, citing this handoff path and the LiNKskills commit SHA that lands it.
2. Do not ask LiNKskills to edit OpenClaw internals.
3. Keep fake-tier usage honest until live issuer / stage gates are separately proven.
4. Brain owner countersign of aggregate `4493f714…` remains a separate owner action.

## Explicit non-claims

- Not a merge approval for https://github.com/linktrend/LiNKskills/pull/22
- Not authorization to start the multi-day Cursor canary
- Not independent Codex certification of LiNKskills implementation
- Not Brain fixture countersign
- OpenClaw tree was **not** modified by this review
- Did not poll hosted CI/Bugbot, deploy, or migrate
