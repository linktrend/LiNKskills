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

## Implementation lanes and maximum safe parallelism

Each lane has at most one active implementation worker on its own issue branch
and isolated checkout. The integration owner is deployment task
`01a089cb-ee73-7c52-9e62-4f9654114eba`; it collects pushed checkpoints and
hands logical groups to the installed Phase Packager/Coordinator. Shared files
move between lanes only after the preceding lease/checkpoint closes.

| Lane | Outcome / packets | Exact owned paths | Prohibited or shared paths | Upstream input / entry | Worker | Wave maximum | Complete / destination |
|---|---|---|---|---|---|---:|---|
| L-BASE | Freeze interfaces (`ED-00`) | Manifest-listed planning docs and `evidence/end-to-end-delivery/ed-00/` | All product, Skill, migration, deploy, consumer paths | `APPROVE`; refresh protected identities | Luna High / Codex CLI | 1 | Reviewed planning/interface checkpoint → integration owner |
| L-ENV | Reproducible environment (`ENV-00`) | `requirements-dev.txt`, `requirements-dev.lock`, `.github/workflows/ci.yml`, `docs/development/CLOUD-EXECUTION.md`, `tests/environment/` | Product packages, Skills, migrations, deploy | ED-00 + XP-00 owner/route receipt | Grok 4.6 Medium, Fast off | 1 | Hash-locked clean install + cloud/CI receipts → Phase environment group |
| L-DATA | Durable store/migrations (`ED-01`) | `packages/persistence/`, `supabase/migrations/`, `docs/migrations/`, `tests/migrations/` | Provider/Skill/consumer paths; migration files are exclusive | ENV-00 + ED-00 | Grok 4.6 Medium, Fast off | 1 | Migration package/review → provider and Platform handoff |
| L-PROVIDER | Provider-v2 Gateway/MCP (`ED-02`) | `packages/contracts/`, `packages/core/`, `packages/gateway/`, `packages/mcp_server/`, `packages/client/`, `tests/contracts/`, `tests/core/`, `tests/gateway/`, `tests/mcp_server/`, `tests/client/` | Skills, migrations, consumer config | ED-01 contract accepted | Grok 4.6 Medium, Fast off | 1 | Provider artifact/review → provider Phase group |
| L-QUAL | Initial qualification (`ED-03`) | `packages/eval_runner/`, `skills/git-safeguard/`, `skills/persistent-qa/`, `skills/repository-manager/`, `skills/skill-template/`, `skills/tool-architect/`, `tests/eval_runner/`, `evidence/end-to-end-delivery/ed-03/` | Other Skills, collections, vendor Skills, consumer config, catalog index | ED-02 accepted | Grok 4.6 Medium, Fast off | 2 with L-DEPLOY | Five profile receipts → release lane |
| L-RELEASE | Publication/selectability (`ED-04`) | `packages/publisher/`, `tests/publisher/`, `evidence/end-to-end-delivery/ed-04/` | Skills, collections, vendor Skills, consumer config | ED-03 accepted; XP-01 for live apply | Grok 4.6 Medium, Fast off | 2 with L-DEPLOY | Reviewed publisher checkpoint; live receipt → consumers |
| L-CONSUMER | Consumer packs (`ED-05`) | `configs/fragments/`, `configs/consumer-activation/`, `docs/integrations/`, `tests/integrations/`, `evidence/end-to-end-delivery/ed-05/` | Skills, migrations, external consumer repos | ED-04 accepted | Grok 4.6 Medium, Fast off | 3 with L-DEPLOY and L-OBS | Three disabled owner packets → XP-02/03/04 |
| L-DEPLOY | Server candidate (`ED-06`) | `deploy/vps/`, `docs/deploy/`, `docs/runbooks/PRODUCTION_OPERATIONS.md`, `tests/deploy/`, `evidence/end-to-end-delivery/ed-06/` | Live compose, migrations, Skills, consumer config | ED-01 + ED-02 | Grok 4.6 Medium, Fast off | 3 with L-CONSUMER and L-OBS | Image/digest/SBOM/rollback pack → Platform owner |
| L-OBS | Librarian/telemetry (`ED-07`) | `packages/librarian_domain/`, `global_evaluator.py`, `tests/librarian_domain/`, `evidence/end-to-end-delivery/ed-07/` | Platform runner, migrations, consumer config | ED-01 + ED-02 + ED-04 | Grok 4.6 Medium, Fast off | 3 with L-CONSUMER and L-DEPLOY | Reviewed worker contract → Platform owner |
| L-LIVE | Server deployment (`ED-08`) | `evidence/end-to-end-delivery/ed-08/`; Platform owns live state | All concurrent shared migrations/server mutations | ED-01–07 + XP-01 + the single recorded `APPROVE` | Privileged Platform owner; Luna only if directed | 1 | Production source/provider/live receipt → canary lane |
| L-CANARY | Ordered consumers (`ED-09`) | `evidence/end-to-end-delivery/ed-09/` | Consumer repos/config remain XP owners | ED-05/07/08 + consumer receipts | Coordinator; consumers execute in owner tasks | 1 | Cursor → Codex → Lisa receipts → correction/acceptance |
| L-IMPROVE | Existing real correction replay (`IMP-00`) | `evidence/end-to-end-delivery/imp-00/` | All source, Skills, migrations, consumer and deploy paths | ED-06/07/08/09; verified historical correction provenance | Coordinator / independent reviewer | 1 | Regression/provider-release/canary receipt → ED-10 |
| L-FIX | Conditional new-defect repair (zero or one of `FIXGS-00`, `FIXPQ-00`, `FIXRM-00`, `FIXST-00`, `FIXTA-00`) | One exact named initial Skill directory, its regression directory, and packet evidence | Every other Skill; no shared publisher/eval source mutation | Only an actual new ED-09 failure selects one packet | Grok 4.6 Medium, Fast off | 1 | Optional corrected release receipt; not an ED-10 prerequisite |
| L-ACCEPT | Assurance/final decision (`ED-10`) | `evidence/end-to-end-delivery/ed-10/`, `docs/end-to-end-delivery/ACCEPTANCE.md` | All source, Skills, migrations, consumer and deploy paths | ED-09 + accepted IMP-00 receipt | Coordinator / independent reviewer | 1 | Final cross-surface decision → governed promotion/deploy owner |

The dependency graph—not an arbitrary worker quota—sets the planned maximum.
The shared XP-05 dispatcher extension is independently accepted. After
`APPROVE`, XP-00 owner admission, and dependency readiness, the highest safe
wave is three
simultaneous workers: L-CONSUMER, L-DEPLOY, and L-OBS. Earlier safe waves are
L-QUAL + L-DEPLOY (two), then L-RELEASE + L-DEPLOY (two). Store/interface
freeze, provider integration, live deployment, ordered actor canaries, any
selected new-defect correction, and final reconciliation serialize because each supplies
an input or mutates shared state required by the next lane.

The coordinator recomputes readiness on every completion, invalidation, or
capacity change and immediately admits every dependency-ready disjoint lane up
to the lower of the safe-wave count and live account capacity. It preserves a
lane's pushed checkpoint through repairs/reviewer feedback; replacement workers
resume from that checkpoint rather than restarting discovery. Broad or unknown
scope remains exclusive.

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
classes, dependencies, and actions covered by the single recorded `APPROVE`
agree across every package
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

**Dependencies:** ED-00 and ED-02 contract; profile fixtures from
XP-02/XP-03/XP-04 may arrive incrementally. **Output:** five immutable release manifests and a
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
live publication covered by the single recorded `APPROVE`, with receipt.
**Recovery:** atomically restore
the prior pointer or revoke the new release; preserve immutable rows/artifacts.

## ED-05 — Produce consumer pins, adapters, and conformance fixtures

**Owner/scope:** LiNKskills owns `configs/fragments/`,
`configs/consumer-activation/`, `docs/integrations/`, and consumer conformance
fixtures/tests. ED-02 alone owns `packages/client/`. Consumer owners apply their
own files.

**Requirements and inputs:** exact ED-02 provider contract and ED-04 releases;
Platform claim contract from the ED-00 published handoff; approved actor order
Cursor → Codex → Lisa; consumer capability/tool-authority declarations from the
ED-00 handoff and later XP-02/XP-03/XP-04 receipts.

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

**Requirements and inputs:** the single recorded `APPROVE`, which covers the
documented deploy/provider mutation;
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
retrieve → verify → local execute → report, then operate it for 48 consecutive
hours spanning at least two Asia/Taipei calendar dates. Record start, midpoint,
and end availability, failure, cost, and non-disruption evidence; continuous
paid activity is not required. Disable/rollback on failure. Repeat the functional
acceptance flow for Codex after Cursor functional acceptance, then Lisa after
Codex. Exercise wrong scope, revoked
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

**Acceptance/checkpoint:** `FUNCTIONAL_ACCEPTED` is available when all three actor
flows pass at compatible identities. `INTERNAL_LAUNCH_COMPLETE` remains HOLD
until the 48-hour Cursor observation also passes. The internal-launch plan at
`docs/LINKSKILLS-INTERNAL-LAUNCH-DETAILED-DEVELOPMENT-PLAN.md` §§13.10 and
15.4 requires multi-day real use; the 48-hour minimum is this package's explicit
interpretation of that otherwise unspecified duration. The single `APPROVE`
authorizes this bounded observation as documented work; it is not a second
approval gate. Commit
`test(canary): prove initial skills consumers`, push, review, and hand the exact
receipts to ED-10. **Recovery:** disable only the failing consumer first; if
systemic, disable all pins and execute ED-08 rollback.

## ED-10 — Prove the improvement loop, assurance, cost, and final acceptance

**Owner/scope:** ED-10 is coordination-only. It owns final assurance and
acceptance records under `evidence/end-to-end-delivery/ed-10/` and
`docs/end-to-end-delivery/ACCEPTANCE.md`; it may not edit source, Skills,
publisher/eval code, migrations, consumer configuration, or deploy files.

**Requirements and inputs:** ED-09 real-use evidence; approved internal-launch
definition of done; exact tool dependency/reverse-dependency graph; provider,
database, request, model, storage, and evaluation cost measurements; SBOM,
vulnerability, secret, privacy, auth/RLS, and supply-chain evidence.

**Work:** consume IMP-00's replay of the existing real Mac Mini PACI canary
issuer-policy correction at commit
`6a2101d132b42010162595a2bab2c72fee6282da`. Its existing
`ResolveClaimsVerifierPaciIssuerPolicyTests` cases in
`tests/gateway/test_paci_adversarial.py` are the regression; IMP-00
re-executes them against the accepted candidate, records the redacted
trace-to-eval candidate through ED-07's supervised Librarian flow. The Librarian
must deduplicate it against the existing correction and record `already_corrected`
rather than propose unnecessary source work. IMP-00 then binds the correction to the exact
immutable provider image/release from ED-06/08 plus the accepted ED-09 consumer
canary. This satisfies the approved
internal-launch plan's real failure/correction requirement without waiting for
or fabricating a new defect. Make or simulate through an immutable fixture one exact tool-version change,
prove affected-profile invalidation/revalidation, prove unaffected profiles stay
valid, and roll the tool/release pointer back. Reconcile measured cost per run
for founder acceptance. Complete security/privacy/supply-chain review and the
full source/provider/consumer/server/production matrix.

**Dependencies:** ED-03, ED-04, ED-06, ED-07, ED-08, ED-09, and one accepted IMP-00
receipt. Conditional L-FIX packets are not dependencies.
**Output:** regression
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

### IMP-00 and conditional L-FIX packets

IMP-00 is the required no-source-mutation improvement packet. It verifies that
the historical correction commit is an ancestor of the accepted candidate,
replays the checked-in PACI canary regression, records its redacted
trace-to-eval disposition, and binds the exact corrected source/test/provider
image/release/consumer-canary identities in
`evidence/end-to-end-delivery/imp-00/improvement-loop-receipt.json`. If that
historical provenance cannot be verified, IMP-00 may demonstrate the mechanism
with a controlled, reproducible nonproduction fixture, but the strict real-
failure criterion remains `OBSERVATION_PENDING`; it may not be reported as the
legacy internal-launch definition of done. Functional acceptance may still be
reported separately.

The five packets below are conditional recovery capacity only. They remain in
the installed supported no-work state `PLAN` when ED-09 finds no new defect; no
agent, issue, lease, archive transition, or mutation is created for them. If
ED-09 finds an actual new failure in one named Skill, exactly that packet may be
activated after its GitHub issue branch, exact paths, commit/tree, and admission
are frozen. Ownership transfers only after ED-03 and ED-09 leases are closed;
no concurrent Skill writer is allowed.

| Packet | Exact source/test/evidence ownership |
|---|---|
| `FIXGS-00` | `skills/git-safeguard/`, `tests/regression/git-safeguard/`, `evidence/end-to-end-delivery/fixgs-00/` |
| `FIXPQ-00` | `skills/persistent-qa/`, `tests/regression/persistent-qa/`, `evidence/end-to-end-delivery/fixpq-00/` |
| `FIXRM-00` | `skills/repository-manager/`, `tests/regression/repository-manager/`, `evidence/end-to-end-delivery/fixrm-00/` |
| `FIXST-00` | `skills/skill-template/`, `tests/regression/skill-template/`, `evidence/end-to-end-delivery/fixst-00/` |
| `FIXTA-00` | `skills/tool-architect/`, `tests/regression/tool-architect/`, `evidence/end-to-end-delivery/fixta-00/` |

Any selected packet reproduces the failure before the fix, changes only its
owned Skill/tests, reruns the relevant existing eval and publisher controls,
publishes a new immutable version without rewriting the old one, proves the
fix, and records revocation/pointer rollback. It commits/pushes and receives an
exact-head independent review before ED-10 may accept it.

An activated packet then transitions to `COMPLETE` only with all semantic
lifecycle fields: one or more terminal attempts and no nonterminal attempt; an
inactive write lock; exact `acceptedCommit`/`acceptedTree`; non-event
`completionEvidence.kind=packet_completion` whose commit/tree and non-empty
summary match; and a checkout-bound `verificationReceipt` with the exact ref,
commit, tree, repository lease identity, and `promotableIdentity=true`. Any
retry exhaustion is diagnosed in `retryExhaustion`; it is never silently reset.

Unselected packets remain `PLAN`. The plan makes no archive API claim for an
agent that was never created, and ED-10 does not count no-work packets as
completed work.

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
exact owner is admitted by the current global queue. Reuse the already verified
transport evidence; the three fixture-only guard stops are not a product or
startup blocker and are not rerun. XP-05's accepted receipt supplies the focused
offline extension-test evidence. No agent is created during this preflight.
ED-00 may run without XP-00 through the founder Gate-0 Luna High
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

### XP-05 — Shared lane-aware dispatcher extension

**Sole owner:** Deployment Advisor. This is one coordinator-side extension to
the established dispatcher, not LiNKskills product work and not an IDE
Development change. It binds repository + lane + branch + baseline + allowed
paths to each stable packet; admits one active writer per lane; rejects
overlapping/shared/broad scopes; serializes admission changes; preserves the
global 20-job/16-writer ceilings, suspension and owner map; and reconciles
active/ambiguous provider state before releasing a reservation.

Focused offline cases cover disjoint same-repository admission, overlap denial,
duplicate/ambiguous creation, suspension, and global limits. Until that exact
extension is verified, LiNKskills executable capacity remains one cloud writer.
After it passes, the coordinator may admit the disjoint waves in the lane table
up to live account capacity. No repository implements or bypasses this shared
change, and no paid probe is required for its offline acceptance.

**Current receipt:** complete. Dispatcher SHA-256
`9c5b5486842e695e47f32896728ec15568237f304ea86115cde50997e419c260`;
`LANE-VERIFICATION.json` SHA-256
`0a8dfbcd5f8d31157b454204e7a9fa57458c0c53f0f59558cf5f9f51718289ba`;
23 focused offline tests PASS and separate independent review PASS. Packets opt
in with `lane_id` and `lane_plan_sha256`. No live provider job, owner admission,
product change, control change, or server mutation occurred.

## Logical integration and promotion sequence

1. Phase A: ED-00 through the founder Gate-0 route; XP-00 performs the narrowly
   authorised coordinator owner transition and route preflight after approval.
2. Environment phase: ENV-00 is the first Grok worker and produces the frozen
   cloud/CI dependency basis after XP-00 owner admission.
3. Phase B after ED-00, XP-00, and ENV-00: ED-01, then ED-02. After ED-02,
   L-QUAL and L-DEPLOY may run as the first disjoint parallel wave using the
   accepted XP-05 lane controls.
4. Phase C: ED-03 evidence completion → ED-04 publication source → ED-05 consumer
   packs; ED-06 image; ED-07 worker/telemetry.
5. Platform dependency group: XP-01 consumes ED-01/06/07 and returns receipts.
6. Production group: ED-08 only after accepted source/artifacts, XP-01, resource
   preflight, and the single recorded `APPROVE`; no second production approval
   is required for the documented actions.
7. Consumer group: ED-09 Cursor (XP-02 only if shared mutation is required),
   then XP-03 Codex, then XP-04 Lisa; ED-09 reconciles actor evidence.
8. Assurance group: IMP-00 replays the existing real correction; ED-10 proves
   the failure-to-improvement loop, tool
   blast radius/rollback, accepted run cost, security/privacy/supply-chain
   clearance, and final classification/acceptance.
9. Protected source moves `issue/*` → Phase PR → `development` → `staging` →
   `main`; production deployment uses only an accepted immutable source/image
   and is never inferred from branch promotion.
