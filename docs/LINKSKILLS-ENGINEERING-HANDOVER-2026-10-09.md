# LiNKskills — Engineering handover

Assessment: **9 October 2026, Asia/Taipei**. Live read-only observation: **19:45–19:47 Taipei / 11:45–11:47 UTC**. Repository: [linktrend/LiNKskills](https://github.com/linktrend/LiNKskills). Companion: [business handover](LINKSKILLS-BUSINESS-HANDOVER-2026-10-09.md). This is a continuation handover, not the new PRD. The business agent supplements the business report, forwards both, and the engineering agent preserves this report unchanged while creating the PRD.

## 1. Operational baseline and interpretation

**The application is deployed to LiNKserver 01.** Fresh read-only inspection confirmed a running healthy container, HTTP 200 `/health` and `/ready`, configured production authentication, loaded catalog and reachable store. Preserve it, its data, installed integrations and rollback material. Lack of coverage below means **unverified**, not missing or broken.

Use five separate states: implemented source, protected integration, passing tests, deployed bytes, and demonstrated operating behavior. A source card, a publication row, a ready probe or a historical receipt cannot substitute for the other states. The 15 September “12/12, 100%” result was an initial five-release acceptance, not completion of later catalog/consumer/Librarian scope.

## 2. Exact repository and deployment identities

GitHub and `git ls-remote` were refreshed during assessment. Protected refs have **different commit IDs but the same tree**:

| Ref | Commit | Tree |
|---|---|---|
| development | `8d9ebe4b5fdc0f3d743a12577c7d6574bed4c5bd` | `dcf82c8c52e3fad343456b61f21239ce9b4218a2` |
| staging | `eba3e6a7b9ec93ce951b1664fda3d19513d84a04` | `dcf82c8c52e3fad343456b61f21239ce9b4218a2` |
| main | `2b07493903a9a40fcce0f66763668421ccbbdd7d` | `dcf82c8c52e3fad343456b61f21239ce9b4218a2` |
| v1.0.0 tag, peeled commit | `28334c4d409dc74a680bf4e09fa2dab22726e229` | `3038dfc1f24c256f9c7547f906a988ce222e2044` |

The original Codex checkout `/Users/linktrend/.codex/worktrees/ae3f/LiNKskills` remains on the older main/tag identity. Do not rely on its tracking refs as current remote truth. Reports were prepared on issue [#423](https://github.com/linktrend/LiNKskills/issues/423), branch `issue/423-create-production-business-and-engineering-hando`, isolated worktree `/Users/linktrend/Projects/LiNKskills/.git/linktrend-worktrees/issue-423-create-production-business-and-engineering-hando`, starting at current development `8d9ebe4…`. No unrelated edits or worktrees were reset.

| Running deployment field | Observed value |
|---|---|
| Host / container | LiNKserver 01 / `linktrend-linkskills`, short ID `5a944b196069` |
| Status / start | Healthy, up three days; started `2026-10-06T01:43:09Z` |
| Image tag | `linkskills-runtime:david-founder-installed-package-20261006` |
| Image configuration ID and locally reported digest | `sha256:2292e8e7e4b95f5c5acbf7441a20a4a39ef2e446ecbea37a7a14540938942582` |
| Source labels | Commit `28334c4d409dc74a680bf4e09fa2dab22726e229`; tree `3038dfc1f24c256f9c7547f906a988ce222e2044` |
| Deployment labels | Container `production-canary`; image `candidate-not-live`; retained packet `ED-06` |
| Port / network | `127.0.0.1:18798` → container `8787`; `linktrend-core-services_default` |
| Actual Compose path | `/srv/linktrend/deploy/compose/linkskills-production.compose.json` |
| Secret mount | `/etc/linktrend/runtime-secrets/linkskills/secrets` → `/etc/linkskills/secrets`, read-only |
| State mount | `/srv/linktrend/runtime/linkskills` → `/var/lib/linkskills`, writable |
| Live catalog index | `/opt/linkskills/catalog/index.json`; 85 entries; embedded source `1b4e55e416af16bc1ec75569a8cfa530a3c89c82` |
| Readiness | HTTP 200; production-auth configured; store reachable; catalog/v2-catalog ready; `skill_count=85`; body `contract_version=skills.api.v0.1` |

The digest is a local image identity; no signed named-registry provenance was verified. The older source labels do **not** prove the running filesystem equals that Git commit. Readiness body version conflicts with the `skills.api.v0.2` deployment label; inspect version reporting and negotiated operation behavior before classifying compatibility defects.

Read-only installed-file hashing produced this evidence:

| Module | Current protected tree SHA-256 | Installed SHA-256 | Match |
|---|---|---|---|
| gateway `production_v2.py` | `3614c57ccf3104de69af17d0fdc5b4da669563c366aef1943657200249b51931` | `bd5ccb3832cd6748555f3edb999116a1e7d81aba54fdd617f94fddd99d801203` | No |
| core `provider_v2.py` | `5ddb734c34bf6df37f3738a6c4ca41f51f02b7eb101b744aac729ab46c57d158` | `4f9dc8975a5ba44ae2688377aee5d6cf2fa8c41005c24115faad448d76f0dc89` | No |
| core `release_v2.py` | `ffbec0d865f184e2c587a0322372a656e86e38fc8381283f2b3918df653f7d2e` | Same | Yes |
| publisher `release_v2.py` | `5bd9ecbe27a07333dfbf4e0d744bcb85f7e3c6a1018215d513ec2180e1d816c2` | Same | Yes |

The first two also differ from the old labeled commit where compared. This is a **verified source/deployment mismatch**, not proof of malfunction. The protected index reports 348 entries, generated `2026-10-05T07:36Z`, embedded source `7d17a9e5881951c1ea9b0725fcde0edb4ced989b`. Embedded source can validly name an ancestor of an index-embedding commit; a different SHA alone does not prove staleness. The embedded commit is an ancestor, but `scripts/build-catalog-index.py --check` actually failed: stored governed-input digest `a27ceb697f4cb06a452df1bc8574210cf18968e46c186d7b5d4f5056a09336fa` differs from current `6df0f27195f0da2cb0922e518143eacc303e654af9e28621202308e932d2d245`. All 348 source cards declare `certification_state=draft`; this is source metadata, not a production release verdict. The live 85-entry index and protected 348-entry index are distinct snapshots, and neither count proves publication/qualification.

## 3. Architecture, source entrypoints and boundaries

LiNKskills is Python-first, Python >=3.11, with setuptools packages. HTTP is standard-library `ThreadingHTTPServer`, not the retired FastAPI service. Core/publisher/eval/tool runtime/Gateway/MCP/client packages are independently versioned `0.1.0`; Librarian domain is `0.2.0`. Product label 1.0 does not automatically bump frozen API/PACI/package contracts. PostgreSQL support uses psycopg; YAML suites use PyYAML; PACI JWT verification uses cryptography. Docker/Linux and a confined evaluator are deployment/evaluation tools. The universal AGENTS TypeScript/UI boilerplate does not describe this Python service.

Pinned source references below use the assessed main commit, so future branch movement does not change their meaning:

| Component | Source / important behavior |
|---|---|
| Editable catalog | `skills/<id>/SKILL.md`, `references/eval-suite.yaml`, supporting references/examples/scripts; [catalog index](https://github.com/linktrend/LiNKskills/blob/2b07493903a9a40fcce0f66763668421ccbbdd7d/catalog/index.json), `validator.py`, `scripts/build-catalog-index.py` |
| Core provider and policy | [provider_v2.py](https://github.com/linktrend/LiNKskills/blob/2b07493903a9a40fcce0f66763668421ccbbdd7d/packages/core/linkskills_core/provider_v2.py), `release_v2.py`, `mcp_v2.py`; exact release/resource integrity, progressive disclosure, selectability and profile gates |
| Production persistence/provider | [production_v2.py](https://github.com/linktrend/LiNKskills/blob/2b07493903a9a40fcce0f66763668421ccbbdd7d/packages/gateway/linkskills_gateway/production_v2.py#L407); `PostgresProviderStore`, `ProductionV2Provider.handle`, `decode_split_release`, metadata-only and bounded resource fetches |
| HTTP | `packages/gateway/linkskills_gateway/server.py`, entrypoint `linkskills-gateway`; `/v2/{operation}` JSON operations plus retained `/v1` compatibility, health/readiness/metrics/drain |
| MCP | `packages/mcp_server/linkskills_mcp/v2_stdio.py`, entrypoint `linkskills-mcp-v2`; provider resource reads and bounded tool calls, shared domain rules |
| Client / bridge | `packages/client/linkskills_client/http_v2.py`, `HttpV2Client.call/read_exact`; buffers/adapters; legacy `lib/skill_runtime` checkout loader retained for migration |
| Publisher and eval | `packages/publisher/linkskills_publisher/`, `scripts/provider_release.py`; `packages/eval_runner/linkskills_eval_runner/{cli,executor}.py`; executed evidence, qualification package, immutable publication |
| Domain Librarian | `packages/librarian_domain/`; [install contract v0.2](https://github.com/linktrend/LiNKskills/blob/2b07493903a9a40fcce0f66763668421ccbbdd7d/docs/contracts/librarian-install-contract-v0.2.md); generic host is in LiNKplatform |

Git is editable source authority. Platform’s shared PostgreSQL `lskills` schema is operational publication/state authority. Catalog → exact release manifest/resource descriptors → verified content → consumer execution → bounded use/feedback receipts → Librarian diagnosis/candidate → new evaluation/publication is the intended flow. The consumer’s tools and approval rules govern actual execution. The provider-v2 legacy `skills_run_*` and `skills_tool_*` routes are denied; do not re-enable them because old prose says “run through the Gateway.”

LiNKbrain remains a separate service/schema/MCP namespace with separate credentials and private memory. LiNKskills telemetry must not ingest raw Brain content, prompts, reasoning, credentials, customer records, trading records, attachments or raw tool output. Cross-service links are opaque references. See [privacy ADR 0007](https://github.com/linktrend/LiNKskills/blob/2b07493903a9a40fcce0f66763668421ccbbdd7d/docs/adr/0007-telemetry-privacy-retention.md) and [ownership ADR 0008](https://github.com/linktrend/LiNKskills/blob/2b07493903a9a40fcce0f66763668421ccbbdd7d/docs/adr/0008-librarian-ownership-cross-repo-contract.md).

## 4. Interface and storage contracts

Provider v2 declares `skills.api.v0.2`: 13 read resources and six bounded tools. Important read operations are `skills_capabilities_get`, `skills_catalog_list/search`, `skills_release_list/describe`, `skills_qualification_get`, `skills_release_entrypoint_get`, `skills_release_sections_list/section_get`, and `skills_release_resources_list/resource_get/content_get/package_get`. Tools are `skills_release_verify`, use-report submit/status, feedback submit/status, and `skills_librarian_status_get`. HTTP uses POST `/v2/<operation>`; MCP adapts the same rules. Do not run these production POSTs in a reporting session without checking their side effects and authorization.

`ExactResource` descriptors bind resource/release/skill/version IDs, URI, kind, media type, byte size, content digest, immutability, disclosure level, provenance, licence and trust boundary. Verify exact expected bytes; no implicit latest, similar-name, native or stale fallback. Separate `platform_technical_eligibility`, `skills_release_selectability`, `consumer_profile_activation` and `consumer_tool_authority`. Readiness does not substitute for these gates.

The production provider verifies PACI identity, looks up `provider_bindings` by exact `(org_id, actor_id, runtime_binding_id, enabled)`, then uses its `runtime_profile` and `release_ids` allowlist. A runtime-binding UUID is not an execution-profile tag. Previously read Jane binding uses `cursor-macos`; do not invent `jane-openclaw` or rename it based on agent names. Main/specialist sharing intent remains a consumer/Platform decision, not something inferred from native session IDs.

The [v2 runtime migration](https://github.com/linktrend/LiNKskills/blob/2b07493903a9a40fcce0f66763668421ccbbdd7d/supabase/migrations/20260915031801_lskills_provider_v2_runtime.sql) defines:

- `provider_releases`: exact text release ID, JSON manifest and manifest/qualification hashes, lifecycle and publication timestamp. Lifecycle includes qualified/revoked/quarantined.
- `provider_bindings`: text org/actor/runtime identifiers, profile string, exact release-ID array, disabled default; identity tuple primary key.
- `provider_receipts`: org/actor/kind/receipt identity primary key, request hash, bounded JSON record, timestamp. Actor/org RLS; identical retry replays, conflicting payload must be denied.

Integrated additive [migration 000014](https://github.com/linktrend/LiNKskills/blob/2b07493903a9a40fcce0f66763668421ccbbdd7d/supabase/migrations/20261005_000014_lskills_provider_resource_rows.sql) adds `provider_release_resources(release_id, resource_id, content_digest, media_type, content bytea)`, keyed by `(release_id,resource_id)`. Runtime SELECT and Librarian SELECT/INSERT are scoped through RLS. New `resource_storage='separate_rows_v1'` releases fail closed if required table/rows are absent; old embedded manifests retain compatibility. Metadata retrieval avoids loading all bytes; requested rows must match manifest hashes/media/size. Its current live application was not verified.

The historical database publication receipt identifies `linkplatform-prod` Supabase PostgreSQL 17.6, schema `lskills`. Fresh readiness proved reachability but this investigation did not read DSNs or query live database identity/roles/schema; current database project identity is therefore historical, not freshly confirmed. Host bind storage was confirmed; no separate object-store identity was established.

## 5. Capability assessment and evidence

| Workflow | Actual implementation / evidence | Assessment and next gap |
|---|---|---|
| Catalog discovery | Core/Gateway taxonomy and progressive listing integrated; runtime readiness says 85 entries; protected source index 348 | Operating catalog load verified; new authenticated search/list and exact inventory comparison unverified. |
| Exact entrypoint/resources | Digest-bound core plus resource-row support integrated; September acceptance and October Sara/Eric retrieval receipts | Historical production retrieval demonstrated; current release/resource behavior, all intended consumers and tamper/revocation negatives need fresh evidence. |
| Consumer identity/activation | PACI + enabled tuple binding + profile/release allowlist | Platform identity completion is Principal-reported; Jane admin row is dated evidence; actual caller RLS and specialist sharing not proven by it. |
| Receipt intake/status/retry | Durable PostgreSQL actor/org records, idempotency and conflict rules | September production PASS; no new write/readback/restart proof on current installed image. |
| Evaluation/qualification | Executable suites and sealed evidence; prompt-only judgments cannot certify; current source tests | Original five releases historically qualified. Original remaining 54 and larger role catalogs not established complete by this investigation. Native evaluator additions exist in separate source candidates. |
| Immutable publication/withdrawal | Publisher manifests/hashes/lifecycle; publication independent of activation | Five historical releases evidenced. Exact current admitted inventory and publisher incident clearance unverified. Never overwrite same ID/version with new bytes. |
| Librarian | Domain worker 0.2; versioned host contract, retries/dead-letter and supervised-first behavior | No matching Librarian Docker container or systemd name found. Alternative scheduler/package invocation not exhaustively checked; sustained operation unverified. |
| Codex/Cursor/Autowork | Disabled owner packets/config fragments and clients exist | Application of host configuration and live authenticated adoption unverified. These are conditional Principal requirements. |
| Service operation/recovery | Live healthy container/readiness; prior restart, backup restore, rollback evidence | Current signed source mapping, monitoring/alert coverage, restart persistence, backup age/restore and rollback identities need server-owner verification. |

Historical evidence re-read and hashed in this assessment (Mac-local sources are not automatically available to cloud agents; obtain redacted exports from their owners):

| Evidence | Exact finding / checksum |
|---|---|
| [September live acceptance receipt](/Users/linktrend/Documents/Codex/2026-09-15/server01-production-owner/outputs/LINKSKILLS-LIVE-ACCEPTANCE-RECOVERY-RECEIPT-2026-09-15.json) | SHA-256 `6f455bfbceda068aa40540d29cb9a12fb4129d20d4d3d9b212c429c957cbbed4`; source `805bc9f9f91e540cc817dc05d86345c119544f05`, tree `a511c5a167c238cc01295ce910ec753bd0ed411b`, image `sha256:ee6f159cfb707c57842da33cfc7d47cb46812b65f1c7e7292ef40da836506564`; five profiles/28 cases; retrieval, safe local procedure, durable receipts, replay/conflict, restart, isolated PG17 restore (20 tables/2 sequences/RLS on 20), rollback to v0.1 and forward recovery PASS. It is not a current-image receipt. |
| [September database publication receipt](/Users/linktrend/Documents/Codex/2026-09-15/server01-production-owner/outputs/LINKSKILLS-PRODUCTION-DATABASE-PUBLICATION-RECEIPT-2026-09-15.json) | SHA-256 `0d31287e70f101718c2fd3261ca37e8299b3bf74248eb3a258d3c21dd7731b6a`; releases git-safeguard@1.1.0, persistent-qa@1.0.0, repository-manager@1.0.0, skill-template@1.2.0, tool-architect@1.0.0. Runtime migration hash `1262ad8200130d7127407d659fc0d9ddfdc5aacba164aab9fd8ad64ccdd914e1`. Publication alone did not activate consumers. |
| [Sara native retrieval receipt](/Users/linktrend/.codex/reports/2026-10-04-sara-native-skills-operator-verification.json) | SHA-256 `7463aae08074db24976d763b2bb046cfaa2ff0e48400412e51b87484f37397e6`; 34 operator retrieval/qualification-status checks, all passed, 12 main releases and five specialist contexts. No model turns or semantic/business acceptance. Historical profile label `lisa-openclaw` is not authority for current binding tags. |
| [Eric native retrieval receipt](/Users/linktrend/.codex/reports/2026-10-04-eric-planning-skills-native-verification.json) | SHA-256 `ebbda475e298472a07ed499f715a4c78e1f413d0015275a8d3ab742db7287fe5`; five planning skill entrypoints retrievable, previous six retained. No full business task execution. |
| [Jane scoped binding readback](/Users/linktrend/.codex/reports/2026-10-05-jane-scoped-provider-binding-readback.json) | Prior read-only admin metadata: enabled `cursor-macos`, 291 release IDs. Explicitly not caller authorization/RLS or four retained specialist mapping proof. Keep private identity tuples out of public reports. |
| [85-entry catalog compatibility handoff](/Users/linktrend/.codex/reports/2026-10-05-live-skills-catalog-compatibility-handoff.json) | SHA-256 `30b2c17501df040a42809cd4b37d46b2813aece13737e2ba647d3e3f0be8fdc0`; source `1b4e55e…` on `dev/cloudcursor/hybrid-merged-skills-7db5`, explicitly not protected main. Current index metadata still points there. |

## 6. Open work, source candidates and relevant failed approaches

Current open PRs observed: [#403](https://github.com/linktrend/LiNKskills/pull/403) hybrid draft cards (targets main), [#404](https://github.com/linktrend/LiNKskills/pull/404) hosted remainder qualification entrypoint, [#405](https://github.com/linktrend/LiNKskills/pull/405) cursor-macos declaration. Their existence is not protected integration; do not merge broadly to obtain one needed file.

Issue [#416](https://github.com/linktrend/LiNKskills/issues/416) has a separate candidate `9e2668f455384e7ac03eff67c23803b60df0200e`, tree `7de6e74c1cf5521f47ae687a96a42194cb136ca7`, publisher registry + `20261005_000015_lskills_registry_quarantine.sql` + tests, outside protected main. This registry quarantine layer is distinct from already-existing provider lifecycle quarantine. Shared schema validation/apply belongs to Platform; isolation/proof and current ownership must be refreshed before integration.

Issue [#409](https://github.com/linktrend/LiNKskills/issues/409) is open; its GitHub branch lookup returned 404. Dirty adapter work was historically retained under `/Users/linktrend/Projects/LiNKskills/.git/linktrend-worktrees/issue-409-add-native-openclaw-evaluator-adapter-with-redac`; do not discard it as empty based on branch HEAD. Protected source lacks the native-evaluator modules. Newer local native-lifecycle work exists at `/Users/linktrend/Documents/Codex/2026-10-05/david-implementation/linkskills-native-lifecycle-successor`, observed commit `41e462ad0157fa76a1ed975ebd909cb442bf9342`, tree `fcfbd002c5babfebf5577bdb5e3140c9e4be0f1e`. Its [10/06 handoff](/Users/linktrend/Documents/Codex/2026-10-05/david-implementation/linkskills-native-lifecycle-successor/docs/handoffs/2026-10-06-native-qualification-runner-integration.md) describes operator registry/launcher, exact input/fixture/profile/release/output/transcript bindings and semantic-review interfaces. Earlier local #418–420 refs are superseded examples, not current protected releases. Reconcile active owner/edit leases with David/Eric before touching these candidates; this assessment did not establish present edit locks or operational launcher/admission status.

Sara/Jane/David role-source packets, correction versions and large frozen suites are related candidate inventories; do not count their structural tests or owner coordination claims as live qualification. The business agent must confirm any scope beyond the original 59 before converting these into final acceptance obligations.

Prior approaches that must not be repeated: trusting labels over file hashes; treating a database admin query as caller RLS proof; inventing profile tags from actor names; equating source acceptance with usable/publication; overwriting an already-published version; treating provider-network egress as `network_isolation=denied`; and running the workstation privileged Docker certification script as a production path. [ADR 0009](https://github.com/linktrend/LiNKskills/blob/2b07493903a9a40fcce0f66763668421ccbbdd7d/docs/adr/0009-confined-executor-network-isolation.md) requires real confinement evidence. Signed native/model receipts need the approved issuer/route/profile/evidence contract, not fake or replayed golden outputs.

A prior credential-exposure concern and publisher incident gate appear in owner records. This task did not inspect raw credentials, determine incident closure or rotate anything. Publication must use Platform’s current cleared credential reference/version and scoped role; do not assume an older successful publisher receipt proves nonexposure.

## 7. Confirmed additions and affected components

The Principal requested all original remaining 54 skill qualifications/publications, all five OpenClaw agents working with Platform/Skills, production Librarian scheduling, and conditional Codex/Cursor/AI-autowork consumers. They also requested release/docs/branch consolidation and a GitHub-contained engineering handoff to Server01. These affect skill suites/profile certifications and publisher; PACI/bindings/consumer adapters; domain worker plus Platform runner; owner config fragments/client buffering; and repository docs/release metadata respectively.

No unlimited catalog denominator, conditional consumer budget, specialist sharing design, service targets, observation period, retention duration, or exact Librarian schedule has been confirmed. Resolve these through the business report before PRD finalization. Original suggested 07:30/19:30 Librarian times are not approved production scheduling. Older blanket approvals/Founder Bootstrap instructions do not bypass this task’s ordinary publication protections or authorize production actions here.

## 8. Validation actually performed and limitations

Fresh investigation was delegated to `gpt-6-luna` high reasoning, the available Luna 6 model; the exact name “Luna 6 High” was unavailable. The parent authored both reports and a separate reviewer assesses completeness.

Completed during assessment: refreshed GitHub refs/tree/tag/open PRs/rulesets; inspected code/contracts/Compose metadata; verified stored receipt checksums; SSH host identity and read-only Docker/image/catalog metadata; installed-file SHA comparison; GET health/readiness; conventional systemd/container name inventory. Existing source tests on issue423/current protected tree: `python3 -m pytest tests/core/test_provider_v2.py tests/deploy/test_server01_candidate.py -q` — **21 passed**; `python3 scripts/check-service-ownership.py` — **passed, 35 services** (17 gws, 18 ltr). Documentation-reference, secret-pattern, diff and copy-hash checks are retained with issue423 delivery evidence.

Catalog provenance validation `python3 scripts/build-catalog-index.py --check` **failed** with governed-input hash drift; the exact hashes are recorded in section 2. No catalog rewrite was made. No full suite, hosted certification, model invocation, production SQL, receipt submission, scheduled job, drain/restart, backup creation/restore or deployment was run. No data or live config was changed. No fresh authenticated operation was inferred from health alone. One readiness request took about 15 seconds; this single observation is not an established performance defect or agreed latency threshold.

## 9. Access, owners and safe continuation

Canonical repositories: `linktrend/LiNKskills` (this domain), `linktrend/LiNKplatform` (identity/database/host), `linktrend/openclaw_prime` (consumers), `linktrend/LiNKbrain` (separate knowledge/shared-host coordination), `linktrend/LiNKautowork` (AI automation consumer), plus IDE Development for shared tooling/host ownership. Confirm remotes in each checkout before binding any work; this task changes only LiNKskills documentation.

Dedicated deployment owner: **Server01 Production Owner**, task `01a0a309-7dfd-7a52-8764-2ebd7fa25be4`, owner workspace `/Users/linktrend/Documents/Codex/2026-09-15/server01-production-owner`. LiNKplatform Completion is task `01a0a3dc-c55e-76e2-a896-d7c0778e65e7`. OpenClaw consumer/source custody requires the corresponding implementation owner; current task names/leases can change and must be confirmed without interrupting unrelated work.

Authorized host access in this assessment: `ssh -o BatchMode=yes -o StrictHostKeyChecking=yes linkserver-01` as configured, then `sudo -n` for bounded Docker metadata. Alias resolves to Tailscale `100.98.225.48:22`. Config is `/Users/linktrend/.ssh/config`; existing identity is referenced there. An initial forced stale host-key alias failed; using the configured address matched its already-trusted ED25519 key. No known_hosts modification or relaxed checking was used. Ask the server owner for authenticated host-key reconciliation if access changes; do not disable verification.

GitHub auth already supports repository API/read/checkpoint operations; do not print `gh auth token`. Phase API scripts accept GH_TOKEN/GITHUB_TOKEN via secure process environment. GSM stores service secrets. Runtime reads rendered secret files through the read-only mount. Relevant names include `LINKSKILLS_AUTH_MODE`, `LINKSKILLS_PLATFORM_AUTHENTICATOR`, PACI issuer/JWKS/audience/scope/introspection configuration, database secret reference, publisher-only `LINKSKILLS_PUBLISHER_DATABASE_URL`, evaluator issuer reference and digest-pinned evaluator image. Obtain grants/versions from Platform and rendering from Server01. No secret values are required in a PRD or handover.

## 10. Delivery, migrations, regression and acceptance sequence

Engineering owns development, focused tests/CI, exact protected source, immutable release/evaluation packaging, migration manifest, documentation and a **deployment-ready handoff**. Platform reviews/sequences/applies shared database changes and owns credential/identity lifecycle and generic Librarian hosting. Server01 owns image build/load/deploy where assigned, live Compose projection, secret injection, service start/drain/restart, backup/recovery, consumer operational acceptance and receipts. A different IDE can continue from GitHub plus the owner’s authorized infrastructure access; it cannot derive secrets or unstored production changes from Git alone.

Recommended order (not a new PRD):

1. Resolve business scope/budgets/specialist mapping and obtain the current installed-source/secret incident custody register. Preserve running image/config/data and existing packages.
2. Inventory agreed source → profile → eval → immutable release → binding → consumer evidence. Explain deployed module/catalog deviations and create an incremental reconciliation plan; no blind reinstall from tag/main.
3. Integrate only needed, independently accepted source candidates through ordinary repository process. Confirm native-evaluator owner interfaces and quarantine/resource-row migration contracts without changing existing published bytes.
4. Prepare targeted regression coverage and release package. Include exact repo/commit/tree, image content digest and signature/SBOM/checksums, ordered hashed migrations, release/profile IDs and evidence, disabled-by-default bindings, worker version/schedule/alert configuration, prior image/config identity, recovery plan and acceptance commands.
5. Platform validates migrations/roles/credentials. Server01 performs the agreed staged deployment and bounded authenticated acceptance using existing authorized routes; any write, model/spend, job or service change needs execution authorization at that time.
6. Server01 demonstrates restart persistence and backup/restore/rollback for the exact accepted state; monitored Librarian runs and agreed consumer coverage complete the final operating outcome.

Apply additive migrations in the owner-approved manifest order. Do not replay the original non-idempotent create-table script blindly on an existing database, rewrite old SQL, drop new tables as rollback, or use broad image/volume pruning. Preserve old embedded releases and migration checkout consumers. Regression checks must cover tamper/revocation/quarantine, profile/identity mismatch, missing resource rows, deny/privacy paths, duplicate vs conflicting receipt retries, and unchanged consumer tool authority. Brain/Skills caches, credentials, queues and data domains remain separate.

Completion is observable when: the running image’s installed bytes/config/catalog have a truthful accepted source/artifact mapping; each **agreed** release has valid executable evidence and immutable publication; every agreed consumer retrieves the exact permitted release/resources and demonstrates permitted use plus safe denied cases; use/feedback receipts persist without duplication or cross-actor leakage; the pinned Librarian completes supervised then scheduled runs with monitoring/escalation; and Server01 supplies fresh health/readiness/restart/recovery evidence and the Principal accepts the resolved business criteria. No global percentage is assigned from entry counts.

## 11. Document publication state and evidence custody

The user requested both reports on main through required review/approval and identical copies in `/Users/linktrend/Downloads`. This task has no new Founder Bootstrap authorization. The ordinary path is issue checkpoint → independent completeness acceptance → Phase Packager/Coordinator draft phase PR → protected integration → staging/main promotion with required receipt and Principal gate. Do not let the implementer self-approve/merge, push protected refs or remove required statuses. Existing active main rules require `Linktrend Receipt Gate` and `Linktrend Branch Source Policy`, with no bypass actors observed.

Source checkpoint or review acceptance is not main publication. The final delivery message records the actual published ref or exact blocker. External Mac-only receipts remain owner-held evidence, and their material findings/checksums are included above so receiving agents do not require this conversation. Fresh read-only observation fields are embedded here; no separate production write was used to create evidence. Receiving agents must refresh drift-prone deployment, branch, incident, role, owner and lock state before execution.
