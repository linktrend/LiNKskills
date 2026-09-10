# LiNKskills end-to-end operational delivery PRD

**Product authority:** additive operational acceptance for the approved
LiNKskills Intent, Technical PRD, internal-launch plan, ADRs 0001–0008, and
provider-v2 contract.

**Target:** the existing LiNKserver 01 production installation; no second
staging installation is introduced.

## 1. Objective

Turn the preserved LiNKskills source and existing Server 01 container into a
usable, evidence-backed procedural-capability provider for the founder's first
three actor surfaces: Cursor, Codex, and Lisa/OpenClaw. The provider publishes
qualified immutable procedures. Each consumer selects and executes locally
under its own Program/tool authority. LiNKskills never grants permission to act.

## 2. Users and required business workflows

### 2.1 Founder and agent use

1. The actor authenticates through Platform-issued identity for audience
   `lskills-api` and service scope `lskills`.
2. It discovers bounded family/catalogue metadata without receiving every Skill
   Pack body.
3. It selects one exact qualified release from the initial set.
4. It retrieves summary, entrypoint, sections/resources, content, or package
   progressively and verifies release/package digests.
5. It stops rather than falling back to latest, stale cache, a similarly named
   skill, or a native substitute if a mandatory release is absent, revoked,
   quarantined, incompatible, tampered, or unsupported.
6. It executes the retrieved procedure locally using only consumer-authorised
   tools and records an opaque consumer correlation.
7. It sends a bounded successful-use report or bounded diagnostic feedback.
8. The founder can see which release was used, by which actor class, whether it
   succeeded, and whether follow-up is needed without exposing prompts,
   transcripts, reasoning, secrets, repository content, customer data, health
   data, trading data, attachments, or raw tool output.

### 2.2 Qualification and publication

1. A source release is structurally valid and has an immutable bundle digest.
2. The real Eval Runner executes representative cases for each target runtime
   profile and retains deterministic assertions, observed artifacts, toolchain
   hashes, and an externally sealed receipt.
3. Prompt-only or fake-judge evidence cannot certify.
4. A profile becomes `usable` only when the exact source, eval suite, tools,
   adapter/runtime profile, and evidence satisfy ADR 0006.
5. Publication creates an immutable release and advances only the intended
   internal channel pointer. It does not activate a consumer.
6. Revocation or regression blocks new retrieval/use without rewriting history.

### 2.3 Operations and curation

1. Operators can distinguish liveness, readiness, provider selectability,
   consumer functionality, and production acceptance.
2. Readiness requires production auth configuration, catalogue availability,
   and reachable durable store.
3. Metrics and alerts cover request/error/auth/readiness/latency, store health,
   publication/eval failures, feedback backlog, worker state, disk/capacity, and
   consumer canary failures with no sensitive payloads.
4. The Platform-hosted generic Librarian loads the versioned LiNKskills domain
   worker, processes Skills-only evidence, and can be disabled independently.
5. Backup and restore protect registry, release pointers, eval/qualification
   evidence, telemetry/feedback state, and runtime configuration. Immutable
   source and release artifacts retain digest provenance.
6. Drain, restart, previous-image/release rollback, pointer rollback, credential
   revocation, and database forward-fix/rollback are rehearsed and observable.

## 3. Initial scope

### 3.1 Included

- The five provider releases frozen in the package README.
- Resource-first provider v2 with bounded discovery and exact-release retrieval.
- Production HTTP Gateway and consumer-facing MCP adapters without duplicated
  business logic.
- Production Postgres-backed store and applicable `lskills` migrations, applied
  only by Platform's governed migration control.
- Real qualification for the five release/runtime-profile combinations needed
  by the initial actors.
- Cursor canary first, Codex second, Lisa/OpenClaw third, with independently
  owned credentials/configuration and rollback.
- Bounded use reporting, feedback, operator observability, and the LiNKskills
  Librarian domain worker.
- Server 01 installation, representative live tests, restart/recovery, and
  production acceptance.

### 3.2 Explicit exclusions

- Bulk qualification or activation of the other 54 source-catalogue skills.
- Qualification or activation of the six collection adapters or 207 external
  collection members; their existing classifications and disabled manifests
  are preserved.
- Provider-side execution through legacy `skills_run_*` or `skills_tool_*`.
- New governance, entitlements, leases, kill-switches, financial ledgers, or
  tenant policy in LiNKskills.
- A combined Brain/Skills service, schema, credential, queue, cache, telemetry
  stream, failure domain, or rollback.
- A separate staging server, Kubernetes, a new reverse proxy, or reinstatement
  of the retired Logic Engine Compose stack.
- LiNKlibraries worker expansion, public marketplace publication, paid provider
  jobs, or public-posting content.

## 4. Functional requirements

| ID | Requirement | Observable acceptance |
|---|---|---|
| FR-01 | Bounded catalogue/family discovery | An authorised actor receives paginated metadata; unqualified and inactive releases are not represented as selectable. |
| FR-02 | Progressive disclosure | The actor can fetch summary, entrypoint, named sections/resources, exact content, and package without broad catalogue-body disclosure. |
| FR-03 | Exact immutable retrieval | Every response binds skill, version, release/package digest, compatibility, and availability; byte/digest checks pass. |
| FR-04 | Fail-closed selection | Revoked, quarantined, unavailable, incompatible, tampered, stale, and unsupported releases return stable denial and no fallback. |
| FR-05 | Platform identity | Missing/invalid/expired/wrong-audience/wrong-scope credentials are rejected; active intended actor credentials succeed. |
| FR-06 | Consumer-local execution | Provider v2 exposes no active `skills_run_*`/`skills_tool_*`; consumer tools and side effects remain under consumer authority. |
| FR-07 | Use/feedback evidence | Success and bounded defect reports are accepted idempotently; status can be read; forbidden payload classes are rejected. |
| FR-08 | Qualification | Each initial release has executed-case evidence for the actor profiles it claims; prompt-only and fake evidence cannot promote. |
| FR-09 | Publication/revocation | Immutable release creation, channel advance, regression demotion/revocation, and prior-pointer rollback are proven. |
| FR-10 | Actor interoperability | Cursor, Codex, then Lisa each complete discover → retrieve → verify → local execute → report using an exact initial release. |
| FR-11 | Librarian | The versioned Skills worker runs in the Platform generic host, consumes Skills-only evidence, proposes/executes only authorised curation, and disables independently. |
| FR-12 | Founder visibility | A concise report distinguishes source, qualified/selectable, consumer, server/runtime, and production proof for every initial release and actor. |

## 5. Data and interface requirements

- Git is editable source authority. Published bundles and evidence are immutable;
  the registry/channel pointers are operational delivery authority.
- `lskills` remains a separate domain schema. Platform applies migrations and
  owns live infrastructure; LiNKskills authors packages, policies, verification,
  rollback/forward-fix, and hashed manifests.
- Platform is canonical for actor/org identity, runtime bindings, credentials,
  issuer/JWKS, and authentication. LiNKskills derives identity from credentials
  and stores only domain bindings/opaque references.
- Provider v2 is `skills.api.v0.2`, standard sessionless MCP, family/resource
  first, exact-release/digest bound. The legacy v0.1 HTTP service may remain only
  as a temporary explicitly observed compatibility adapter with a removal gate;
  it is not the target consumer contract.
- Cross-service correlation is opaque-reference only. Raw Brain conversations or
  private memory never enter Skills telemetry.
- Retention, backup, purge, and restore rules must cover registry, release,
  qualification, eval evidence, telemetry, feedback, and Librarian queue state.

## 6. Configuration requirements

Production configuration must be SecretRef-driven and bind at least:

- exact LiNKskills release/image/source commit and tree;
- `LINKSKILLS_ENV=production`, Postgres store, mandatory store probe, state path,
  drain and bounded shutdown settings;
- Platform authenticator, issuer, JWKS, audience `lskills-api`, required scope
  `lskills`, introspection endpoint/client, trusted mint allowlist, and
  assertion-key file paths;
- database DSN/role through GSM custody without values in Git, command arguments,
  receipts, or chat;
- initial release allowlist/channel and per-consumer activation pins;
- metrics scrape, alerts, log retention/redaction, backup, and restore targets;
- domain-worker artifact pin, schedule/retry/DLQ/disable state after the first
  supervised run.

Accounts, API keys, client registrations, and actor consent are execution work
after approval. They are not automatically founder prerequisites. Genuine
account consent or public posting is requested just in time if actually needed.

## 7. Deployment and recovery requirements

- Reuse the existing hardened Docker/Compose installation on LiNKserver 01.
- Preserve the current release `7067716…`, image digest `sha256:7cf2780…`,
  runtime state directory, secret mounts, and prior compose projection as
  rollback inputs until acceptance.
- Build/test heavy source work in hosted CI or cloud workers. Server work is
  limited to image/release verification, configuration, migrations through
  Platform control, deployment, probes, canaries, recovery, and observability.
- The server deployment remains loopback/private-network oriented unless the
  approved Platform route requires a Skills-specific private endpoint. A green
  container healthcheck cannot mask `/ready=503`.
- Before cutover: inventory and backup; after cutover: exact image/release
  readback, `/health`, `/ready`, authenticated contract probes, actor canaries,
  restart and rollback rehearsal, and evidence retention.
- Rollback drains traffic, disables consumer pins, restores the prior image and
  channel pointers, restores compatible configuration, verifies data state, and
  preserves failed-candidate evidence. Live DDL rollback/forward-fix is
  Platform-owned.

## 8. Definition of done

All of the following must be true at the same accepted identities:

1. Protected source and deployed image/release identities are exact and
   independently verified.
2. The production Gateway is live and ready (`/health=200`, `/ready=200`) with
   auth and durable store genuinely reachable.
3. Provider-v2 resource discovery/retrieval and exact digest verification pass;
   legacy execution operations are unavailable on the v2 route.
4. The five initial releases have immutable live publication plus valid
   executed-case qualification for their claimed profiles and are selectable
   only through intended consumer pins.
5. Cursor, Codex, and Lisa complete representative end-to-end use in order,
   including local execution and bounded evidence submission. Identity-backed
   read and a safe non-destructive workflow are both demonstrated.
6. Wrong identity/scope, revoked/tampered content, store outage, provider outage,
   and disabled-consumer scenarios fail closed without unsafe fallback.
7. Metrics, logs, alerts, founder report, Librarian status, backup, restore,
   restart, drain, and rollback evidence pass.
8. Brain/Skills separation, privacy/redaction, least privilege, and consumer
   tool authority remain intact.
9. Independent narrow reviews and the final cross-surface acceptance reconcile
   source, provider/selectability, consumer, server/live, and production proof.
10. Later expansion remains disabled/unqualified except for any release
    separately approved through a material scope change.
