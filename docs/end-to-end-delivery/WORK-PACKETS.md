# LiNKskills end-to-end delivery work packets

All packets are `PLAN` until the founder says `APPROVE` in this task. Packet
owners must refresh exact repository/ref/commit/tree, current Platform receipts,
server state, active leases, and consumer state immediately before work.

## Common execution contract

- LiNKskills source packets use one governed `issue/*` branch each and the
  operative direct REST Cursor route with Grok 4.6 Medium, Fast off, explicit
  `repos[]`, frequent pushed checkpoints, focused checks, and one exact-head
  independent narrow review. The installed SDK control is a future interface,
  not the current transport.
- Every packet and required worker input must be committed and pushed at its
  exact GitHub repository/ref/commit/tree/path before dispatch. Mac-only files,
  conversation history, and prompt-only requirements are not worker inputs.
- The implementer does not open a delivery PR, self-review, self-merge, promote
  protected refs, deploy production, mutate live providers, or prefer incoming.
- Packager/Coordinator opens logical Phase PRs; delivery controller merges to
  `development`; staging/main and production actions require their recorded
  gates. A staging branch is not another server.
- Evidence always separates source, qualification/selectability, consumer,
  server/live, and production acceptance.
- Product/server secrets are referenced by GSM name/path only. The operative
  coordinator route reads its existing named macOS Keychain item locally. No
  secret value may appear in Git, chat, packets, worker prompts, command
  arguments, process listings, test fixtures, logs, or receipts.
- Ordinary repair is bounded to three source repairs. Infrastructure has at most
  two attempts at one exact candidate. Code/test failure returns to a new
  identity; retries never weaken acceptance.

## ED-00 — Freeze current identity, interfaces, and acceptance

**Owner/scope:** LiNKskills planner/implementer. Only `docs/README.md`,
`docs/end-to-end-delivery/`, this delivery's `docs/handoffs/` record, and a new
issue evidence directory.

**Requirements and inputs:** Package README/PRD; provider-v2 documents; ADRs
0001, 0003, 0005, 0006, 0008; current protected refs; current Server 01 and
Platform recovery snapshots.

**Work:** refresh exact LiNKskills/Platform revisions; confirm the five initial
provider releases and local-adapter exception; record the provider-v2/local
execution boundary; classify any drift; update manifest baseline and packet
paths. Publish versioned non-secret `PLATFORM-INTERFACE.json` and
`CONSUMER-INTERFACES.json` handoffs under the ED-00 evidence directory, each
bound to upstream repository/ref/commit/tree/path/blob digest. Copy interface
facts only, never another repository's implementation or secrets. A material
scope/interface change is returned to the founder.

**Dependencies:** none. **Output:** immutable execution baseline and acceptance
matrix under `evidence/end-to-end-delivery/ed-00/`.

**Minimum validation:** manifest schema and semantic validator; relative-link
check; `git diff --check`; no product path changes; independent document review
bound to exact commit/tree.

**Acceptance/checkpoint:** current identities, contracts, initial set, proof
classes, dependencies, and founder-reserved actions agree across every package
file. Commit `docs(delivery): freeze end-to-end baseline`, push, write evidence,
and publish the exact checkpoint handoff. **Recovery:** revert the documentation
checkpoint; no runtime state exists.

## ED-01 — Reconcile durable provider store and migration package

**Owner/scope:** LiNKskills owns `packages/persistence/`,
`supabase/migrations/`, `docs/migrations/`, and focused persistence/migration
tests. ED-02 alone owns the Gateway store adapter. Platform alone applies live
DDL and owns `svc_lskills_runtime` issuance.

**Requirements and inputs:** Technical PRD §§8–9; the accepted ED-00
`PLATFORM-INTERFACE.json` handoff derived from Platform plan §§13–14 and Phase 6;
current `lskills` migration files; production `/ready` evidence showing
`OperationalError`; exact Platform migration/identity/backup receipts when available.

**Work:** inventory expected versus live migration fingerprints without printing
DSNs; produce one versioned/hash-bound migration package with prerequisites,
least-privilege grants/RLS, forward verification, rollback/forward-fix, backup
scope, and compatibility; make the store return sanitised actionable readiness
diagnostics while preserving fail-closed behavior. Do not apply live DDL.

**Dependencies:** ED-00, ENV-00, and the XP-00 route receipt; live apply waits for XP-01.
**Output:** Skills-owned migration artifact and Platform-consumable handoff.

**Minimum validation:** focused migration schema/RLS/idempotency tests against
an ephemeral Postgres version compatible with production; store readiness and
error-redaction tests; migration manifest hash verification; no service-role or
secret fixture; `git diff --check`.

**Acceptance/checkpoint:** Platform can verify/apply the exact package without
inventing requirements; runtime role can perform required operations and no
broader ones in the test DB; rollback/forward-fix is explicit. Commit
`feat(persistence): package production store readiness`, push, exact-head review,
handoff to XP-01. **Deployment/recovery:** Platform takes a governed backup,
applies in order, verifies fingerprints/grants/RLS, and issues receipt; on
failure stop writes and use the packaged forward-fix/rollback under Platform
authority.

## ENV-00 — Pin the reproducible cloud execution environment

**Owner/scope:** LiNKskills owns `requirements-dev.txt`, a generated
`requirements-dev.lock`, `.github/workflows/ci.yml`,
`docs/development/CLOUD-EXECUTION.md`, and focused `tests/environment/`. It does
not change product dependencies, product packages, deploy files, or Skills.

**Requirements and inputs:** accepted ED-00 identity; current root and package
`pyproject.toml` files; current CI (`ubuntu-24.04-arm`, Python 3.11); the
completed LiNKskills cloud qualification receipt (Linux x86_64, Python 3.12.3,
Node 22.14.0); and XP-00 owner/route receipt. The repository has no submodules,
no Node package manifest, no private Python package source, and currently uses
range-only `requirements-dev.txt`.

**Work:** on the disposable cloud VM, attest OS/architecture/Python/pip; install
the matching `venv`/development headers if absent; create and activate an
isolated venv; resolve only the existing public-PyPI requirements plus local
packages; generate and verify an exact-version, artifact-hash lock; teach CI to
install it with hash enforcement; document the local-package-before-umbrella
order and `PYTHONPATH`-only `packages/contracts` and `packages/persistence`.
Do not add a product dependency or use production credentials/data. Node and a
JavaScript package manager are not required for this packet.

**Dependencies:** ED-00 and XP-00. **Output:** one pushed, independently
reviewed environment checkpoint that later packets can install without an
unbounded resolver.

**Minimum validation:** clean initial/final Git identity; lock regeneration is
stable; `python -m pip install --require-hashes -r requirements-dev.lock` in a
new venv; current catalog gates and focused environment tests on the cloud
x86_64 worker; protected CI repeats its Python 3.11 Ubuntu 24.04 ARM matrix;
secret scan and `git diff --check`.

**Acceptance/checkpoint:** exact interpreter, OS/architecture, lock digest,
installation order, tests, and CI receipt are recorded. Commit
`build(deps): pin cloud execution environment`, push, exact-head review, then
handoff the immutable lock to ED-01 onward. **Recovery:** revert the checkpoint
and restore the preceding CI install line; no server or production state exists.

## ED-02 — Ship the provider-v2 Gateway/MCP artifact

**Owner/scope:** LiNKskills owns `packages/contracts/`, `packages/core/`,
`packages/gateway/`, `packages/mcp_server/`, `packages/client/`, and their
focused tests. It does not edit consumer repositories or Server 01 compose.

**Requirements and inputs:** provider-v2 operations/conformance; ADR 0003;
`skills.api.v0.2`; standard MCP `2026-07-28`; ED-01 store contract; current
v0.1 live compatibility surface.

**Work:** expose one production provider-v2 entrypoint across HTTP/MCP adapters;
keep business rules transport-independent; implement bounded family/catalogue,
release history/summary/qualification, exact entrypoint/section/resource/content/
package retrieval, digest verification, bounded use/feedback/status, and
Librarian status; ensure `skills_run_*` and `skills_tool_*` return
`legacy_execution_disabled` on v2; define the observed legacy adapter and
removal gate; preserve stable error envelopes, pagination, identity and privacy.

**Dependencies:** ED-00 and ED-01. Source work may use the accepted ED-01
contract while live XP-01 application remains pending. **Output:** installable provider-v2 image/package contract,
client fixtures, OpenAPI/MCP capability record, and upgrade/rollback notes.

**Minimum validation:** contract, core, Gateway, MCP, client, pagination,
sessionless negotiation, exact-byte/digest, legacy-denial, auth, privacy,
idempotency, and degraded-store tests; image build in hosted CI; SBOM/secret scan;
container `/health` and expected `/ready` behavior against fakes.

**Acceptance/checkpoint:** an independent actor can enumerate the advertised
v2 capabilities and complete exact retrieval with no provider execution route;
wrong version/digest/identity fails closed. Commit
`feat(provider): expose production skills v2`, push, exact-head review, and
artifact handoff. **Deployment/recovery:** retain the current v0.1 image and
compose projection; rollback drains and restores that digest without changing
immutable releases.

## ED-03 — Qualify the five initial release/profile combinations

**Owner/scope:** LiNKskills owns `packages/eval_runner/`, qualification logic,
five named `skills/<id>/` packages, their eval suites/tests, and
`evidence/end-to-end-delivery/ed-03/`. No other skill body or collection member
may change.

**Requirements and inputs:** ADR 0006; exact initial list in README; current
skill/eval/tool digests; Cursor, Codex, and Lisa capability profiles; confined
executor and external issuer SecretRef contract.

**Work:** audit each suite for representative success, guardrail, failure,
recovery, and privacy cases; add only missing deterministic executable coverage;
run exact packs/tools in digest-pinned sealed Linux with network isolation and a
real consumer-profile driver; retain observed artifacts/checks and signed
receipts; classify each release/profile independently. Prompt-only or fake
evidence remains non-certifying.

**Dependencies:** ED-00 and ED-02 contract; profile fixtures from XP-02/XP-03
may arrive incrementally. **Output:** five immutable release manifests and a
profile qualification matrix; a failure of one does not promote or block an
unrelated passing release.

**Minimum validation:** per-skill validator and eval-suite validation; confined
executor path/symlink/network tests; receipt signature/digest verification;
negative fake/prompt-only test; secret/privacy scan; focused regression tests.

**Acceptance/checkpoint:** every claimed `usable` profile has executed-case
evidence bound to source/eval/tool/adapter/runtime digests; non-passing profiles
stay `eval_pending` or quarantined. Commit
`feat(qualification): certify initial provider releases`, push, exact-head review,
and evidence handoff. **Recovery:** revoke/withhold the affected channel pointer;
never rewrite a release or evidence record.

## ED-04 — Publish the exact initial releases and enforce selectability

**Owner/scope:** LiNKskills owns `packages/publisher/`, release/eligibility
contracts, initial allowlist configuration, and focused publication tests. The
packet must not edit later expansion collections or bulk catalogue metadata.

**Requirements and inputs:** ED-03 passing receipts; ED-01 registry contract;
provider-v2 gate model; current local canary publication receipt as historical
input only.

**Work:** package and publish only passing initial profiles to the intended live
internal channel; bind source/bundle/eval/tool/profile digests; configure
technical eligibility, Skills selectability, and consumer activation as three
independent gates; reject stale/tampered/revoked/quarantined content; provide
channel rollback and revocation.

**Dependencies:** ED-01, ED-02, ED-03, and live apply XP-01. **Output:** immutable
release receipts, live qualification rows, intended channel pointers, and
selectability denial matrix.

**Minimum validation:** publisher/idempotency/revocation/pointer rollback tests;
exact readback through production provider; database receipt and digest match;
later catalogue entries remain unchanged and nonselectable.

**Acceptance/checkpoint:** each allowed initial release is retrievable by exact
version/digest and each ineligible profile is denied; ordinary selectable count
equals the explicitly accepted initial set, never an aggregate source count.
Commit `feat(publisher): publish initial qualified set`, push, review, then
founder-reserved live publication with receipt. **Recovery:** atomically restore
the prior pointer or revoke the new release; preserve immutable rows/artifacts.

## ED-05 — Produce consumer pins, adapters, and conformance fixtures

**Owner/scope:** LiNKskills owns `configs/fragments/`,
`configs/consumer-activation/`, `docs/integrations/`, and consumer conformance
fixtures/tests. ED-02 alone owns `packages/client/`. Consumer owners apply their
own files.

**Requirements and inputs:** exact ED-02 provider contract and ED-04 releases;
Platform claim contract from the ED-00 published handoff; approved actor order
Cursor → Codex → Lisa; consumer capability/tool-authority declarations from the
ED-00 handoff and later XP-02/XP-03 receipts.

**Work:** generate disabled-by-default, exact-release/digest pins for the five
initial Skills; define private endpoint, token mint, resource retrieval,
verification, local execution, use report, failure, and rollback flows; keep
Brain and Skills config/credentials separate; forbid unapproved native/stale/
similar-name fallback.

**Dependencies:** ED-02 and ED-04. **Output:** three owner-consumable packets and
contract fixtures with no live activation.

**Minimum validation:** schema/digest/allowlist/deny tests; fake Platform and
provider contract tests; no secret values; no consumer-owned file changed;
later expansion manifests remain disabled.

**Acceptance/checkpoint:** each consumer owner can apply one exact packet without
inventing URLs, scopes, versions, digests, tool authority, telemetry bounds, or
rollback. Commit `feat(integrations): pin initial consumer releases`, push,
review, and send one handoff per owner only during approved execution.
**Recovery:** consumers remove/disable their pin and retain local bootstrap
skills; provider state is unchanged.

## ED-06 — Build and prepare the Server 01 deployment candidate

**Owner/scope:** LiNKskills owns `deploy/vps/`, image definition/build metadata,
service definition, production runbook, and deployment tests. Platform/Server 01
owns `/srv/linktrend/deploy/compose/core-services.compose.yml`, secrets, network,
and live container mutation.

**Requirements and inputs:** ED-01/02 artifacts; exact source/commit/tree; current
image `sha256:7cf2780…`, release `7067716…`, compose/hardening readback;
Platform-provided endpoint/database/identity contracts.

**Work:** create one reproducible linux/amd64 image with non-root runtime,
read-only compatibility, health/readiness checks, SBOM/provenance, exact labels,
and no secrets; update environment template/runbook for v2, Postgres, metrics,
drain, backups, and rollback; produce a sanitized compose overlay/diff for the
Platform owner rather than editing live compose.

**Dependencies:** ED-01 and ED-02; can build before XP-01, cannot deploy before
ED-04 and Platform receipts. **Output:** digest-pinned candidate image/release,
release manifest, deployment pack, and previous-state rollback pack.

**Minimum validation:** hosted image build, vulnerability/secret scan, exact
label/readback, non-root/read-only/cap-drop/no-new-privileges tests, resource
limits, health/ready/drain/signal/store failure tests, architecture match.

**Acceptance/checkpoint:** Server owner can verify and deploy the artifact without
source rebuild or architecture invention; previous release/image/config/state
are explicitly retained. Commit `build(deploy): package server01 skills v2`,
push, review, and artifact receipt. **Recovery:** reject candidate before deploy
on any digest mismatch; after deploy drain and restore the prior exact compose
projection/image/release/config.

## ED-07 — Integrate telemetry, Librarian, and operator visibility

**Owner/scope:** LiNKskills owns `packages/librarian_domain/`, Skills telemetry/
feedback contracts, privacy validators, `global_evaluator.py`, and focused tests.
Platform owns generic host, queue/schedule/credentials/alerts and shared config.

**Requirements and inputs:** Technical PRD §§5, 7, 17–18; ADR 0008; ED-01 store;
ED-02 provider; the accepted ED-00 versioned handoff for the current Platform
domain-worker contract.

**Work:** bind use/feedback receipts to exact release/profile and opaque consumer
correlation; enforce forbidden payload rejection and retention; version the
domain worker artifact/conformance; expose Skills-specific backlog/status;
define first supervised run, retry/idempotency/DLQ/disable/recovery, and a
founder report separating proof classes.

**Dependencies:** ED-01, ED-02, ED-04; live host integration waits for XP-01.
**Output:** versioned Skills worker, conformance package, redacted metrics/report,
and Platform handoff.

**Minimum validation:** privacy/redaction, idempotency, retention/purge,
cross-domain rejection, worker conformance, prompt-only rejection, disable/
retry/DLQ, metrics cardinality, and status-report tests.

**Acceptance/checkpoint:** one supervised production-equivalent run processes
only Skills evidence, cannot certify from prompt-only input, is independently
disableable, and produces a truthful founder report. Commit
`feat(librarian): operationalize skills evidence loop`, push, review, Platform
handoff. **Recovery:** disable the Skills worker/schedule, preserve queue and
evidence, and keep provider reads independent.

## ED-08 — Deploy and verify the provider on LiNKserver 01

**Owner/scope:** Platform/Server 01 performs live actions from the ED-06 pack;
LiNKskills owner observes domain conformance and records sanitized evidence under
`evidence/end-to-end-delivery/ed-08/`. No separate staging server is created.

**Requirements and inputs:** founder approval for deploy/provider mutation;
Platform accepted migration/backup/identity receipts; ED-04 releases; ED-06
image; complete server resource snapshot; current rollback image/config/state.

**Work:** preflight capacity and active leases; take/verify backup; stage exact
release/image; apply Platform-owned migration; render GSM secrets; drain current
container; deploy hardened candidate on existing network; verify image/config/
mount readback; test `/health`, `/ready`, metrics, valid/invalid auth, provider-v2
retrieval, denied legacy routes, store outage, restart, and rollback rehearsal.

**Dependencies:** ED-01–ED-07 and XP-01. **Output:** checkout/image/config,
migration, deployment, health/readiness, auth, provider, backup/restore, restart,
and rollback receipts.

**Minimum validation:** all probes named above plus log/metric redaction,
Prometheus target/alert, no public unintended listener, all Server 01 containers
healthy, and previous release still recoverable. No load test during planning;
approved execution uses only bounded representative traffic unless a separate
load packet is approved.

**Acceptance/checkpoint:** production `/ready=200`; exact v2 release retrieval and
negative paths pass at the deployed digest; a rollback rehearsal succeeds and
returns to the candidate without data loss. Commit sanitized receipts only,
push, independent operations review. **Recovery:** drain, disable consumer
activation, restore previous compose/image/release/config/pointers, verify store
compatibility and health, retain failed state/evidence.

## ED-09 — Run ordered consumer canaries and multi-day Cursor use

**Owner/scope:** LiNKskills owns the project-scoped Cursor integration/template,
conformance, canary, and cross-consumer evidence. A shared/global Cursor mutation,
if unavoidable, is applied only by the shared configuration owner in XP-02.
The Codex owner executes XP-03; OpenClaw owner executes XP-04. LiNKskills writes
only its approved integration surfaces and `evidence/end-to-end-delivery/ed-09/`.

**Requirements and inputs:** ED-08 production provider PASS; exact consumer pins;
valid Platform identities; per-consumer local tool authority; rollback ready;
initial releases only.

**Work:** enable the isolated/project-scoped Cursor canary, run discover →
retrieve → verify → local execute → report, then operate it for the approved
multi-day window while recording availability, failure, cost, and non-disruption
evidence; disable/rollback on failure. Repeat the acceptance flow for Codex only
after Cursor acceptance, then Lisa after Codex. Exercise wrong scope, revoked
release, tampered/stale cache, provider/store outage, and consumer-disable
negatives. Reconcile qualification, provider, consumer, server, observability,
Librarian, backup/recovery, and rollback evidence.

**Dependencies:** ED-05, ED-07, ED-08, XP-02 when shared Cursor mutation is
required, XP-03, and XP-04. **Output:** three exact canary receipts,
negative-path matrix, founder walkthrough, and final acceptance inputs.

**Minimum validation:** each consumer uses one safe representative task and one
negative case; Cursor additionally passes the multi-day window; exact release/
profile/tool/consumer/provider identities match; telemetry contains only allowed
bounded fields; unrelated consumers and later skills remain disabled.

**Acceptance/checkpoint:** all three actor flows and the Cursor multi-day gate are
PASS at compatible identities. Commit
`test(canary): prove initial skills consumers`, push, review, and hand the exact
receipts to ED-10. **Recovery:** disable only the failing consumer first; if
systemic, disable all pins and execute ED-08 rollback.

## ED-10 — Prove the improvement loop, assurance, cost, and final acceptance

**Owner/scope:** LiNKskills owns a bounded regression-eval/release change only in
the one affected initial skill and its exact tests/evidence; final assurance and
acceptance records live under `evidence/end-to-end-delivery/ed-10/` and
`docs/end-to-end-delivery/ACCEPTANCE.md`. Any discovered failure determines the
single affected skill path; other skills and later expansion are prohibited.

**Requirements and inputs:** ED-09 real-use evidence; approved internal-launch
definition of done; exact tool dependency/reverse-dependency graph; provider,
database, request, model, storage, and evaluation cost measurements; SBOM,
vulnerability, secret, privacy, auth/RLS, and supply-chain evidence.

**Work:** select one real observed failure/correction from the accepted canary;
turn it into an executable regression eval; improve and republish one immutable
release through ED-03/04 controls; prove the new version fixes the failure.
Make or simulate through an immutable fixture one exact tool-version change,
prove affected-profile invalidation/revalidation, prove unaffected profiles stay
valid, and roll the tool/release pointer back. Reconcile measured cost per run
for founder acceptance. Complete security/privacy/supply-chain review and the
full source/provider/consumer/server/production matrix.

**Dependencies:** ED-03, ED-04, ED-07, ED-08, and ED-09. **Output:** regression
eval, improved immutable release receipt, tool blast-radius/rollback receipt,
accepted cost record, assurance report, 59-entry classification inventory, and
final acceptance decision.

**Minimum validation:** reproduce-before/fix-after case; exact release/eval/tool
digests; reverse-dependency and unaffected-profile assertions; pointer rollback;
cost calculation inputs and plausibility check; security/privacy/RLS/auth/
supply-chain/secret scans; final independent cross-surface review.

**Acceptance/checkpoint:** every PRD Definition of Done item is PASS at compatible
identities and no assurance blocker remains. Any missing item stays HOLD; no
aggregate percentage substitutes for proof. Commit
`docs(acceptance): close linkskills production delivery`, push, review, then use
governed promotion/release procedures. **Recovery:** revoke the improved release
or restore its prior pointer/tool pin; retain regression and failed evidence;
disable consumers or execute ED-08 rollback if the defect is systemic.

## External dependency packets — recorded, not dispatched

### Planning dependencies versus runtime dependencies

Planning dependencies are already satisfied: approved LiNKskills Intent/PRD/
ADRs, provider-v2 contract, initial five-release lock evidence, current Platform
plan, current Server 01 inspection, and installed IDE Development 2.5.2
protocol/schema were reviewed and pinned. A future revision change requires
refresh/reconciliation but does not make this plan incomplete.

Runtime dependencies are XP-00 through XP-04. They are needed for executable
ordinary routing, live database,
identity, generic-host, consumer, and production acceptance. Planning-ready for
any dependency never means deployed, configured, or accepted; only its exact
execution receipt can satisfy a downstream gate.

### XP-00 — Direct Cursor execution-route preflight

**Sole owner:** local coordinator / Cursor account owner. Re-hash the operative
standard-library REST dispatcher, prove the GitHub issue branch/commit/tree,
then perform one rate-limit-aware account/model/repository read using the
existing Keychain reference. The receipt must prove Grok 4.6 Medium, Fast off,
explicit LiNKskills `repos[]`, status/result retrieval controls, exact identity
attestation, fail-closed mismatch behavior, and the controlled reconciliation/
archive procedure for a rejected created agent. It must also prove this task's
exact owner is admitted by the current global queue and run the transport suite
in an isolated accepted context; the 2026-09-10 baseline was 7 PASS with 3
fixture cases stopped early by the live suspension guard. No agent is created during this
preflight. ED-00 may run without XP-00 through the founder Gate-0 Luna High
route; ED-01 and all ordinary post-Gate-0 Cursor work wait for its fresh XP-00
receipt. See `EXECUTION-ROUTE.md`.

### XP-01 — Platform foundation and live data plane

**Sole owner:** LiNKplatform / task `01a0843c-0df9-74e2-907a-05c5f736d6ed`.
Provide exact accepted backup/restore, migrations, `svc_lskills_runtime` and
worker identities/credentials, PACI issuer/client/runtime bindings, storage,
generic Librarian host, observability, and production receipts. Apply the
ED-01 package and ED-06 compose overlay. Exit when Skills store/auth/worker
contracts pass without broad credentials. Owned live surfaces include
`/srv/linktrend/deploy/compose/core-services.compose.yml`,
`/run/linktrend/linkskills/runtime.env`, the read-only
`/etc/linktrend/runtime-secrets/linkskills/secrets/` mount, Platform migration
control/receipts, and `LiNKplatform/packages/librarian-runner/`. LiNKskills must
not repair Platform.

### XP-02 — Shared/global Cursor configuration, only if required

**Sole owner:** IDE Development/shared Cursor configuration owner. LiNKskills
owns the project-scoped template, installer, conformance, and canary under ED-05/
ED-09. XP-02 exists only if a shared/global Cursor change is unavoidable; it
applies that exact change in a maintenance window and returns non-disruption and
rollback evidence. Owned repository paths are
`core/link-integrations/skills-loader.mjs`, `core/link-integrations/skills.mjs`,
`core/link-integrations/skills-lock.json`,
`core/managed-core/platforms/cursor/skills-{loader.mjs,lock.json}`, and their
`tests/link-integrations/` coverage. Installed projections change only through
the official installer/rollout path. Preserve local `agentsetup`/`agentcomply`;
no physical skill removal occurs until retrieval and rollback are proven.

### XP-03 — Codex consumer application

**Sole owner:** LiNKbrain shared Codex configuration owner unless the founder
assigns a dedicated integration owner. LiNKskills supplies the independently
named Skills fragment and conformance; the owner applies the separate Skills
entry to shared `config.toml`, common hooks, and lifecycle scripts, uses a
separate credential, executes locally, and returns exact conformance/rollback
receipts. Relevant IDE source paths are
`core/managed-core/platforms/codex/skills-{loader.mjs,lock.json}` and focused
`tests/link-integrations/`; the live user/project config path is resolved and
recorded immediately before apply.

### XP-04 — Lisa/OpenClaw consumer application

**Sole owner:** OpenClaw Prime/Lisa. Apply ED-05 Skills-only config to the native
bridge, preserve Brain separation and consumer tool authority, execute the third
canary, and return exact conformance/rollback receipts. No other agent identity
or future collection is activated by this packet. Owned paths are
`extensions/linkskills/`, the applicable
`docs/execution/openclawdevelopmentplan01/mcp-templates/` Skills template and
Skills runbooks, plus their focused extension tests; live Lisa configuration and
SecretRefs remain OpenClaw/Server 01-owned state, never LiNKskills files.

## Logical integration and promotion sequence

1. Phase A: ED-00 through the founder Gate-0 route; XP-00 performs the narrowly
   authorised coordinator owner transition and route preflight after approval.
2. Environment phase: ENV-00 is the first Grok worker and produces the frozen
   cloud/CI dependency basis.
3. Phase B after ED-00, XP-00, and ENV-00: ED-01, followed by dependency-safe
   ED-02 and ED-03 preparation where paths are disjoint.
4. Phase C: ED-03 evidence completion → ED-04 publication source → ED-05 consumer
   packs; ED-06 image; ED-07 worker/telemetry.
5. Platform dependency group: XP-01 consumes ED-01/06/07 and returns receipts.
6. Production group: ED-08 only after accepted source/artifacts, XP-01, resource
   preflight, and founder-reserved production approvals.
7. Consumer group: ED-09 Cursor (XP-02 only if shared mutation is required),
   then XP-03 Codex, then XP-04 Lisa; ED-09 reconciles actor evidence.
8. Assurance group: ED-10 proves the real failure-to-improvement loop, tool
   blast radius/rollback, accepted run cost, security/privacy/supply-chain
   clearance, and final classification/acceptance.
8. Protected source moves `issue/*` → Phase PR → `development` → `staging` →
   `main`; production deployment uses only an accepted immutable source/image
   and is never inferred from branch promotion.
