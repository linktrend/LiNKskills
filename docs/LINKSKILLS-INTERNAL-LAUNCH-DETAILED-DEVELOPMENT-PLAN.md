# LiNKskills Internal Launch — Detailed Development Plan

**Status:** Proposed for Principal review. This document is a development plan, not authorization to make every described change at once. Implementation begins only after the Principal approves this plan and each repository follows its own coordination and Git workflow.

**Primary repository:** `LiNKskills`

**Related repositories required for the internal launch:** `LiNKplatform`, `openclaw_prime`, and `LiNKbrain`

**Initial actor rollout:** Cursor macOS first, Codex macOS second, Lisa/OpenClaw Prime third

**Launch mode:** Trusted internal use only (the original manual's “Mode 1”)

**Explicit permanent boundary:** LiNKskills certifies and delivers procedural capabilities. It never grants permission to perform Program work.

**Concurrent execution model:** Four repository-specific Cursor agents using Grok 4.5 High Fast execute the approved LiNKskills, LiNKbrain, LiNKplatform, and OpenClaw Prime plans concurrently in separate checkouts/worktrees and branches. Codex 5.6 Sol Medium agents remain the planning and independent verification layer. A Grok completion report is provisional until the matching repository Codex verifier checks the actual implementation and evidence.

**Shared-surface rule:** Independent domain work may proceed concurrently, but shared identity, live migrations, the generic Librarian host, OpenClaw/Lisa internals, shared Codex host configuration, and any unavoidable global Cursor configuration each have exactly one assigned implementation owner.

---

## 1. Purpose of this document

This is the standalone development and internal-launch plan for LiNKskills. It assumes the reader:

- has no access to the conversations that produced the plan;
- has no prior knowledge of LiNKtrend or LiNKskills;
- can inspect the current `LiNKskills`, `LiNKplatform`, `LiNKbrain`, and `openclaw_prime` repositories;
- may be a Cursor, Codex, OpenClaw, or other implementation agent picking up the work later.

The document explains:

- what LiNKskills is intended to become;
- what exists today and what is only a partial implementation;
- why Git and LiNKplatform are both required;
- the canonical Skill Pack, tool, eval, telemetry, release, and certification models;
- how the institutional Librarian participates without absorbing domain ownership;
- how Cursor, Codex, and Lisa/OpenClaw consume the same service;
- which repository owns each change;
- the phased implementation sequence, tests, evidence, rollout gates, rollback, and definition of done.

This plan deliberately contains enough context for a new agent to create implementation work packets without reconstructing the original discussion. It does not itself implement the system.

## 2. Authority and interpretation

The implementation reader must distinguish current authority from future intent:

1. **Principal-approved decisions recorded in this plan** define the intended internal-launch end state.
2. **Current code and applied migrations** are authoritative for what exists now.
3. **Current repository source-of-truth documents** describe the narrower system that was built through 2026-07-19. They must be reconciled through ADRs before implementation changes their stated boundaries.
4. **The original long-form LiNKskills manual** is design guidance. Its Skill Pack, adapter, telemetry, eval, and improvement concepts inform this plan. It does not override later decisions that permanently removed governance and permission-to-act from LiNKskills.
5. **ADR 0001 remains permanent:** entitlements, Program leases, kill switches, financial ledgers, and permission-to-act do not return to this repository.
6. **The proposed LiNKbrain Phase 1 plan is a compatibility input, not LiNKskills authority.** It keeps LiNKbrain and LiNKskills separate and defines shared LiNKplatform and actor-integration boundaries.
7. **Older combined LiNKbrain/LiNKskills and Lisa Git-mount proposals are historical inputs.** Their LiNKskills delivery assumptions are superseded when this plan is approved.
8. **The four approved repository plans are controlled execution inputs.** Execution agents implement them; they may not redefine architecture, repository ownership, shared contracts, or rollout boundaries merely to unblock work.
9. **Shared-surface ownership overrides convenience.** A domain agent may supply a contract, fixture, configuration fragment, migration package, or validation suite without gaining authority to mutate another repository or a shared live surface.

If implementation exposes a contradiction or requires a deviation, stop dependent work, record the proposed change and reason, identify every affected plan/repository/interface/file, send it to the LiNKskills Codex verifier and LiNKbrain coordinating agent, and wait for a plan-level decision. Do not silently reinterpret the product or take over another owner's work.

## 3. Executive outcome

After the internal launch, LiNKskills will be LiNKtrend's shared procedural-capability platform for AI actors.

An integrated actor will be able to:

1. authenticate as a known actor and runtime profile;
2. describe a task or capability need;
3. discover relevant certified skills without loading the entire catalog into context;
4. inspect a summary, routing guidance, requirements, and progressively deeper skill sections;
5. start a versioned skill run;
6. resolve the exact certified tools and dependencies for that run;
7. execute packaged tools locally or centrally through the appropriate adapter;
8. validate inputs, outputs, artifacts, and completion evidence;
9. record structured, observable telemetry and user feedback;
10. close or fail the run with evidence;
11. allow the Librarian to use telemetry, failures, corrections, and eval evidence to improve the next version;
12. receive only published versions that passed real eval execution for its compatible runtime profile.

The core improvement loop is:

```text
Author Skill Pack in Git
  -> validate and build immutable bundle
  -> execute complete eval suite with exact tools
  -> certify an execution profile
  -> publish to LiNKplatform registry/storage
  -> disclose and run through LiNKskills MCP/API
  -> collect telemetry and feedback
  -> create improvement/eval candidates
  -> Librarian proposes and tests the next version
  -> staged release or rollback
```

## 4. Plain-English product definition

LiNKskills stores and delivers repeatable instructions for how an AI actor should perform a capability. A skill is not merely a prompt. A launch-quality skill specifies:

- when it should and should not be used;
- required inputs and expected outputs;
- a step-by-step procedure and conditional branches;
- required and optional tools;
- verification and completion rules;
- examples, failure handling, and known limitations;
- eval cases that prove it works;
- telemetry that shows how it performs in real use.

LiNKskills solves procedural drift. Once the studio establishes the correct method for a recurring capability, agents should retrieve the current certified version instead of recreating the process from memory or copying instructions between chats.

LiNKskills is separate from:

- **LiNKbrain**, which stores institutional knowledge, private agent memory, continuity, and advisory coordination;
- **LiNKlibraries**, which stores reusable application components, templates, integrations, and starter kits;
- **Program Ledgers**, which own Issues, Runs, Gates, operational authority, and permission to act;
- **actor runtimes**, which own their context windows, local tools, sandboxing, and host-specific lifecycle.

Example:

```text
LiNKbrain: "The studio's approved authentication architecture is X, for reasons Y."
LiNKskills: "Follow this certified procedure to implement and verify X."
LiNKlibraries: "Here is the reusable X component/starter-kit asset at version Z."
Program Ledger: "This Issue is authorized to modify application A and passed its gates."
```

## 5. Product boundaries

### 5.1 LiNKskills owns

- the canonical Skill Pack standard;
- skill identity, versions, dependencies, categories, and routing metadata;
- source validation and compilation into runtime representations;
- the published internal catalog and release state;
- progressive disclosure of skill content;
- packaged agent-facing tools and their interfaces;
- eval standards, fixtures, runners, results, and certification profiles;
- skill-run lifecycle and observable telemetry;
- user feedback and trace-to-eval candidates;
- skill quality scores and regression evidence;
- skill intake, normalization, improvement, deduplication, merge/split, deprecation, retirement, and rollback workflows;
- the LiNKskills domain API and MCP adapter;
- LiNKskills-specific Librarian contracts, policies, tests, and domain worker behavior.

### 5.2 LiNKplatform owns

- the shared Supabase/Postgres and storage foundation where published LiNKskills data physically lives;
- organizations, actor identity, membership/RBAC, and shared access primitives;
- common secrets, credential, audit, and environment conventions;
- the one institutional Librarian identity, generic runner host, scheduler, retries, and operational monitoring;
- versioned domain-worker loading and invocation;
- review, sequencing, live application, and operation of shared stage/production database migrations supplied by domain repositories;
- least-privilege service identities and shared infrastructure deployment conventions.

LiNKplatform is not the owner of Skill Pack business rules. The `lskills` schema, policies, and migration source remain LiNKskills domain assets even though they are deployed on the shared platform. LiNKskills authors and tests those migrations; only the LiNKplatform agent reviews, sequences, applies, and operates them in shared stage/production environments.

### 5.3 LiNKbrain owns

- institutional knowledge and memory;
- private agent memory and conversation retention when its approved plan is implemented;
- task continuity, handoffs, and advisory coordination;
- LiNKbrain-specific Librarian extraction and canonical-knowledge rules;
- its own MCP/API service.

LiNKskills and LiNKbrain may reuse LiNKplatform-defined cross-cutting contracts, but neither service is a transport alias for the other. They retain separate services, schemas, MCP/API domains, credentials/scopes, caches, queues, telemetry, retention rules, failure states, and feature flags. Their MCP tools use independently named namespaces: `skills_*` for LiNKskills and `brain_*` for LiNKbrain. There is no combined Brain/Skills Gateway and no shared mutable domain table.

### 5.4 Program Ledgers and capability grants own

- permission to modify repositories, deploy, publish, send, purchase, migrate, or perform other Program work;
- Issue/Run/Gate/Event state;
- assignments, leases, fences, approvals, and release authority;
- checks against `platform.capabilities` and `platform.capability_grants` where applicable.

LiNKskills certification answers “Is this skill/tool combination demonstrated to work?” It never answers “May this actor perform this action now?”

### 5.5 Local actor runtimes own

- current conversation and working context;
- local file and repository access;
- tool approval and sandbox enforcement;
- runtime lifecycle and model selection;
- host-specific MCP configuration;
- local cache/buffer storage and offline behavior.

Runtime ownership does not permit every domain agent to edit runtime internals. The OpenClaw Prime repository agent solely owns OpenClaw/Lisa implementation surfaces. For this four-agent rollout, the LiNKbrain execution agent is the default owner of shared Codex host configuration. LiNKskills owns its Cursor product canary, subject to the shared/global configuration safeguards in Section 21.2.

### 5.6 LiNKlibraries boundary

LiNKskills and LiNKlibraries remain separate repositories:

- agent procedure, evals, verification, and an agent tool wrapper belong in LiNKskills;
- reusable application source, template, component, integration, or starter kit belongs in LiNKlibraries;
- a skill references a LiNKlibraries asset by stable identity/version rather than duplicating it.

LiNKdeveloper may continue to identify and submit reusable library candidates. The complete intelligent LiNKlibraries Librarian workflow is a separate concept and plan. It does not block LiNKskills internal launch.

### 5.7 Explicitly out of scope for internal launch

- customer-facing licensing and billing;
- prepaid credits or vendor-executed commercial mode;
- tenant entitlements owned by LiNKskills;
- Program leases, permission gates, or kill switches;
- a general workflow/Suite orchestrator;
- replacement of LiNKbrain or Program memory;
- storage of complete private conversations in LiNKskills telemetry;
- a full commercial LiNKconsole;
- watermarking, DRM, and external IP-protection controls;
- a customer marketplace;
- merging LiNKskills into LiNKlibraries or LiNKbrain;
- certifying every possible model or runtime permutation.

## 6. Terms used in this plan

| Term | Meaning |
|---|---|
| Actor | A consumer identity such as Cursor Desktop, Codex Desktop, Lisa, or a Program executor. |
| Runtime profile | A bounded compatibility profile describing actor/runtime capabilities, adapter range, model capability, and tools. |
| Skill | A reusable procedural capability. |
| Skill Pack | The canonical multi-file, versioned, testable source package for one skill version. |
| Skill fragment | An addressable portion disclosed progressively, such as summary, routing, procedure section, example, or verification instructions. |
| Tool package | A callable implementation shipped or referenced by LiNKskills with an interface, version, hash, tests, and side-effect metadata. |
| Execution profile | The complete combination of Skill Pack, eval suite, toolchain, adapter, and runtime profile being certified. |
| Skill run | One actor's use of one published skill version for a task. |
| Verification | Checks that one actual output/artifact satisfies its contract. |
| Eval | A repeatable test of skill quality across defined cases. |
| Certification | Evidence-backed statement that an execution profile passed its required evals. |
| Release | An immutable published Skill Pack/tool bundle made available through a channel. |
| Librarian | The single institutional AI custodian, hosted by LiNKplatform, with separate domain workflows. |
| Candidate | A new skill, improvement, eval, consolidation, deprecation, or retirement proposal awaiting processing. |
| Trace-to-eval | Turning an observed failure, correction, or edge case into a regression eval. |
| Platform actor ID | The canonical durable actor identifier issued and governed by LiNKplatform. LiNKskills references it and does not create a competing permanent identity. |
| Domain actor binding | A LiNKskills record that associates a platform actor with a runtime profile, adapter, session, or skill run. |
| Execution agent | The repository-specific Cursor/Grok agent authorised to implement one approved plan in its assigned checkout/worktree and branch. |
| Repository verifier | The repository-specific Codex agent that independently checks the Grok implementation against the approved plan and actual evidence. |
| Coordinating verifier | The LiNKbrain Codex agent that reconciles the four repository verification results and identifies cross-repository gaps. |
| Interface gate | A required producer/consumer handoff that must pass before a shared integration or live action proceeds. |
| Cursor development environment | The IDE used by all four execution agents; distinct from Cursor as the LiNKskills product actor/canary. |

## 7. Current LiNKskills repository state

### 7.1 Healthy foundation that must be preserved

As verified during planning:

- 34 skills exist under `skills/`;
- all 34 have baseline `references/eval-suite.yaml` files;
- 32 use `format_profile: heavy`, and 2 use `simple`;
- 19 top-level tool packages exist under `tools/`;
- `validator.py --scan-all` validates 53 registry targets;
- `catalog/index.json` is current;
- all 6 `lib/skill_runtime` unit tests pass;
- the service-ownership matrix validates 35 services;
- the `lskills.catalog`, `lskills.telemetry`, and `lskills.eval_runs` migrations exist;
- database triggers prevent promotion to `usable` without a passing latest eval row and demote on a later failing eval;
- ADR 0001 has retired the former Logic Engine governance subsystem.

The two validator warnings are old `execution_ledger.jsonl` rows using the legacy telemetry shape. They are not current validation failures.

### 7.2 Current runtime

`lib/skill_runtime` currently:

- builds/reads a filesystem catalog;
- resolves one checked-out skill directory;
- loads the complete `SKILL.md` and supporting paths;
- optionally refuses a non-`usable` skill;
- appends high-level invocation events to a local JSONL buffer;
- optionally writes telemetry through PostgREST.

Programs currently require a pinned Git checkout. There is no LiNKskills MCP server, HTTP domain service, authenticated actor identity, published-bundle registry, run session, fragment disclosure controller, or capability negotiation.

### 7.3 Current catalog and schema limitations

- all 34 generated catalog entries are `draft`;
- the filesystem catalog represents only the version present in the checkout;
- catalog metadata lacks a normalized category taxonomy, immutable bundle hash, eval hash, toolchain lock, release channel, runtime compatibility, and enabled/retired state;
- the database contains catalog, eval-run, and invocation telemetry foundations, but not full runs, event streams, tools, dependencies, artifacts, feedback, certification profiles, releases, Librarian proposals, or trace-to-eval candidates;
- ordinary runtime access is still shaped around direct PostgREST/database configuration rather than a LiNKskills Gateway.

### 7.4 Current eval limitation

The eval YAML files are baseline definitions, not proven complete certification specifications.

The current LiNKplatform skills runner loads the suite and passes only the following to its model judge:

- skill ID and version;
- eval-suite file reference;
- rubric dimension names;
- pass threshold.

It does not execute the skill against scenario inputs, run the exact tools, collect actual outputs/artifacts, apply deterministic assertions, or provide the observed trace to the judge. Model-produced efficiency and size metrics are therefore not measured evidence.

This is the most serious current certification gap. The existing runner's tests prove orchestration and response parsing, not actual skill performance.

### 7.5 Current telemetry limitation

Current invocation telemetry records useful summary fields but not the canonical lifecycle needed for improvement:

- requested/selected/disclosed/started events;
- fragments used;
- exact tool calls and tool failures;
- validation/eval steps;
- produced artifact references;
- user corrections and satisfaction;
- release channel and execution profile;
- trace-to-eval disposition.

Telemetry is cooperative: consumers must remember to record it. The Gateway and adapters must capture the lifecycle they directly observe.

### 7.6 Current Librarian limitation

The LiNKplatform runner currently prioritizes catalog rows, asks a model to score, records an eval row, and promotes/demotes/escalates.

It does not yet implement the intended LiNKskills lifecycle:

- new-skill intake and normalization;
- source modification and improvement;
- complete eval execution;
- category/index maintenance;
- dependency and blast-radius analysis;
- toolchain certification;
- deduplication, merge, split, deprecation, retirement, and archival;
- durable skill-specific review queues;
- release creation and rollback.

LiNKplatform currently defines one Librarian identity with two workflows (LiNKbrain and LiNKskills). The Principal has agreed that the eventual identity has three separate domain workflows: LiNKbrain, LiNKskills, and LiNKlibraries. LiNKlibraries expansion is not required to launch LiNKskills, but the identity/docs must stop asserting that “exactly two” is permanent once the third workflow is formally designed.

### 7.7 Documentation and coordination drift

Current authoritative LiNKskills documents say:

- Git checkout is the normal consumer path;
- no long-lived skill-text API exists;
- catalog + baseline eval + telemetry is the Program-level done state.

Those statements describe the current implementation but conflict with the approved end state. Phase 0 must reconcile them before implementation.

The repository has no `docs/handoffs/` directory despite the current root `AGENTS.md` requiring handoffs. The shared `.cursor` symlink currently exposes instructions that misidentify this repository as LiNKdeveloper. These are preflight defects to correct deliberately, not instructions to ignore silently.

## 8. Target architecture

```text
Cursor macOS        Codex macOS        Lisa/OpenClaw        Program executors
     |                   |                  |                       |
     +------------- LiNKskills MCP / API / SDK adapters -----------+
                                 |
                     LiNKskills Gateway Service
            auth, catalog, disclosure, runs, validation,
             tool resolution, telemetry, feedback, audit
                                 |
                     LiNKskills domain services
           registry | publisher | eval runner | tool runner
                                 |
            LiNKplatform Postgres + object storage
        lskills operational records + immutable published bundles
                                 |
              Institutional Librarian host in LiNKplatform
                     invokes LiNKskills domain worker
                                 |
                    Git-authoritative source
          Skill Packs + tools + evals + tests + release history

Separate parallel service (not part of this stack):
  LiNKbrain Gateway -> lbrain domain -> LiNKbrain domain worker

Shared LiNKplatform cross-cutting plane only:
  actor identity/auth claims | correlation IDs | credentials
  deployment/audit/observability conventions | Librarian host lifecycle
```

### 8.1 Core architecture rule

MCP is the primary internal agent interface, but it is not the internal ontology. HTTP/API and future SDK adapters call the same domain operations. Skill Packs remain protocol-independent.

LiNKskills exposes only independently named `skills_*` MCP tools. LiNKbrain exposes `brain_*` tools through its own service. The two services do not share request queues, runtime caches, telemetry streams, retention jobs, mutable domain tables, credentials, health states, or feature flags. A consumer adapter may connect to both, but must keep their configuration and failure handling distinguishable.

### 8.2 LiNKskills Gateway Service

Create a stateless actor-facing service owned by LiNKskills. It must:

- authenticate actors through approved LiNKplatform identity;
- derive actor identity from credentials rather than request-body claims;
- expose the versioned domain API and MCP adapter;
- serve only published immutable releases for ordinary execution;
- search/rank skills and disclose bounded fragments;
- create and close skill runs atomically;
- resolve certified execution profiles and exact tool versions;
- validate inputs/outputs and accept safe artifact references;
- record structured events, feedback, and audit receipts;
- hide database, storage, model-provider, and Librarian credentials from actors;
- fail clearly when a required exact/compatible tool is unavailable;
- support cursor/idempotency semantics for retries and offline flush.

The Gateway consumes LiNKplatform's canonical actor/auth claim contract. It may persist LiNKskills-specific actor/runtime/run bindings referencing the platform actor ID, but it must not become an organisation-wide identity issuer or permanent competing actor registry.

### 8.3 Domain packages recommendation

Exact names require an ADR, but responsibilities should be separated:

```text
packages/
  contracts/            versioned schemas and compatibility fixtures
  core/                 pure policies, lifecycle, selection, disclosure
  publisher/            Git source -> validated immutable release bundle
  eval-runner/           case execution, evidence, verification, grading
  tool-runtime/          tool descriptors and controlled invocation adapters
  gateway/               HTTP service, auth, rate limits, health, metrics
  mcp-server/            MCP resources/prompts/tools over the core services
  client/                generic API client and offline event buffer
  librarian-domain/      LiNKskills-specific candidate/improvement workflows
integrations/
  cursor/
  codex/
```

OpenClaw-specific implementation remains in `openclaw_prime`, not in this repository.

Shared Codex host configuration also remains outside the LiNKskills domain implementation. LiNKskills publishes an independently named configuration fragment and conformance fixtures; the shared Codex integration owner applies it after the Skills readiness gate.

## 9. Source, publication, and storage model

### 9.1 Multiple sources of truth by responsibility

| Responsibility | Authority |
|---|---|
| Editable skill/tool/eval source | LiNKskills Git repository |
| Review, branches, diffs, and source rollback | Git |
| Published skill identity/version/status | LiNKplatform Postgres (`lskills`) |
| Certified immutable bundle | LiNKplatform-backed object storage |
| Search/routing/disclosure fragments | Postgres/cache derived from the bundle |
| Certification/eval evidence | Postgres plus immutable evidence artifacts where needed |
| Runs, events, feedback, quality metrics | Postgres |
| Consumer delivery | LiNKskills Gateway through MCP/API |

Git and the database are not competing stores. Git is the authoring system; LiNKplatform is the publication and runtime system.

### 9.2 Publication pipeline

For each candidate version:

1. Resolve the Git commit and clean source tree.
2. Validate Skill Pack structure and all referenced files.
3. Resolve typed skill, tool, asset, and external capability dependencies.
4. Run tool unit/integration/security checks.
5. Compile canonical fragments and runtime descriptors.
6. Build a deterministic bundle.
7. Hash the source tree, bundle, eval suite, tools, and descriptors.
8. Execute required eval profiles.
9. Record certification evidence.
10. Upload the immutable bundle/evidence.
11. Insert or advance the published release record transactionally.
12. Warm/index disclosure and search records.
13. Emit a release audit event.

Published bundles are immutable. A correction creates a new version/release; it never edits an already certified bundle in place.

### 9.3 Runtime cache and degraded operation

Adapters may cache the last verified published bundle/fragments by content hash. During a temporary outage:

- cached certified instructions may remain readable;
- exact cached tools may run only if their bundle hash and runtime profile still match;
- telemetry buffers locally and flushes idempotently later;
- an actor must report that live catalog/certification freshness could not be checked;
- no draft or mismatched version is silently substituted.

## 10. Skill Pack v0.1 launch standard

The launch standard is deliberately between the current minimal frontmatter and the manual's full commercial format.

### 10.1 Required identity and release fields

- stable `skill_id` and display name;
- semantic version;
- description and capability category;
- provenance/author/source;
- license/provenance record for imported material;
- source commit and content hash at publication;
- release channel and lifecycle state;
- format/schema version;
- compatible runtime profiles and minimum capability tier.

### 10.2 Required routing fields

- when to use;
- when not to use;
- supported task/capability tags;
- exclusion and ambiguity rules;
- related, alternative, superseded, and prerequisite skills;
- recommended disclosure starting level.

### 10.3 Required execution contract

- required and optional inputs;
- input schema where structured;
- expected output/artifact contract;
- procedure and conditional branches;
- forbidden actions and failure handling;
- verification steps;
- completion criteria;
- known limitations.

### 10.4 Required dependency types

Do not keep all requirements in one untyped `dependencies` list. Distinguish:

- `skill_dependencies`;
- `packaged_tools`;
- `host_capabilities` such as repository/filesystem/browser access;
- `external_services`;
- `library_assets` referencing LiNKlibraries;
- `runtime_requirements`;
- `optional_dependencies` and certified alternatives.

### 10.5 Required eval and telemetry declarations

- eval-suite path, schema version, and hash;
- required certification profiles;
- verification implementation references;
- telemetry classification and redaction rules;
- artifact/evidence retention policy;
- performance/cost budgets where relevant.

### 10.6 Progressive-disclosure structure

Each Skill Pack must expose addressable fragments:

0. existence/index entry;
1. routing/metadata;
2. short summary and requirements;
3. applicable procedure section;
4. verification/failure section;
5. examples or schemas;
6. full internal Skill Pack when explicitly required.

Internal actors may access full packs, but default selection must remain summary-first to protect context quality.

### 10.7 Current skill migration

Preserve the current `simple` and `heavy` concept. Do not force every skill into the largest layout.

Migration steps:

1. define v0.1 schemas and examples;
2. update `skill-template`, `skill-architect`, and `tool-architect` first;
3. create a deterministic migration/audit report for all 34 skills;
4. migrate a representative canary set;
5. refine the schema from observed friction without breaking published identities;
6. migrate the remaining catalog;
7. keep legacy parsing only for source migration, not steady-state published runtime.

## 11. Tool architecture

### 11.1 Tool ownership rule

- an agent-facing procedural tool or wrapper required by a skill belongs in LiNKskills;
- a reusable application component belongs in LiNKlibraries;
- a host-native capability remains owned by the host and is mapped by capability;
- a third-party service remains external and is referenced by a versioned adapter contract.

### 11.2 Required tool descriptor

Every packaged tool must declare:

- stable tool ID and semantic version;
- source and bundle hashes;
- input/output JSON schema;
- command/transport entrypoint;
- supported platforms and runtime requirements;
- side-effect class and reversibility;
- secrets/capabilities required (names only, never values);
- network/filesystem boundaries;
- timeout, retry, and idempotency behavior;
- verification and smoke tests;
- owning skill(s) and reverse dependency list;
- compatibility and deprecation state.

### 11.3 Execution placement

Default placement:

- repository, filesystem, local browser, and local-development tools run on the actor host;
- centralized data/services may run through a server-side adapter;
- the execution profile records which placement was certified;
- the host enforces approval and operational authority;
- LiNKskills never bypasses the host's Program/runtime controls.

### 11.4 MCP exposure

The MCP surface needs both stable control operations and packaged tool execution.

Preferred design:

- stable LiNKskills tools handle discovery, runs, validation, feedback, and tool resolution;
- packaged tools are exposed under stable names when the client supports dynamic registration;
- a generic versioned invocation endpoint may be used where dynamic registration is impractical;
- every invocation resolves to an exact tool version/hash and execution profile;
- MCP annotations/metadata accurately state read-only, destructive, idempotent, and external-side-effect behavior.

### 11.5 Tool change blast radius

A tool release must identify every certified skill profile that references it. Material tool changes move affected profiles to compatibility-check/eval-pending until required regression tests pass. Unaffected profiles remain usable.

## 12. Discovery, selection, and progressive disclosure

### 12.1 Phase 1 visibility

All internal `usable` skills are discoverable to participating actors. Draft skills may appear only in explicit development/evaluation views and must never look production-certified.

### 12.2 Selection flow

1. Actor supplies task, Program/repository/Issue context, runtime profile, and available capabilities.
2. LiNKskills filters to compatible published releases.
3. It ranks by task match, category, exclusions, dependencies, profile evidence, quality, and freshness.
4. It returns a small result set with reasons and requirements.
5. Actor selects/confirms a skill.
6. LiNKskills creates a run and returns the starting fragments and exact profile.
7. Actor requests deeper fragments only when needed.

LiNKskills recommends; it does not force a skill into context or decide Program authorization.

### 12.3 Routing quality

Routing evals must test:

- correct selection;
- correct non-selection;
- ambiguity handling;
- closely overlapping skills;
- dependency/tool unavailability;
- outdated/deprecated versions;
- task contexts from different Programs.

## 13. Agent-facing MCP/API contract

Final names require an ADR. The minimum domain operations are:

### 13.1 Catalog and disclosure

| Proposed operation | Purpose |
|---|---|
| `skills_list` | Browse categories and compatible usable skills. |
| `skills_search` | Rank skills for a task/runtime context. |
| `skills_describe` | Return routing, requirements, profile evidence, and breadcrumbs. |
| `skills_fragment_get` | Return one addressable fragment or explicit full internal pack. |
| `skills_release_get` | Return immutable release/profile metadata and hashes. |

### 13.2 Run lifecycle

| Proposed operation | Purpose |
|---|---|
| `skills_run_start` | Select exact release/profile and create an idempotent run. |
| `skills_run_update` | Record material progress, disclosure, validation, or artifact references. |
| `skills_run_complete` | Close with output/evidence/feedback and success classification. |
| `skills_run_fail` | Close with structured failure and trace-to-eval eligibility. |

### 13.3 Tools and verification

| Proposed operation | Purpose |
|---|---|
| `skills_tool_resolve` | Resolve exact tool descriptor/version/placement. |
| `skills_tool_invoke` | Invoke a packaged tool when the adapter owns execution. |
| `skills_input_validate` | Validate structured input against the release contract. |
| `skills_output_validate` | Apply deterministic output/artifact checks. |

### 13.4 Feedback

| Proposed operation | Purpose |
|---|---|
| `skills_feedback_submit` | Record correction, rating, friction, missing step, or outcome. |
| `skills_trace_candidate_submit` | Propose an observed case for eval conversion. |

### 13.5 Common response envelope

Every response should include:

- contract version;
- request/idempotency ID;
- server time;
- actor/session/run identifiers where relevant;
- release and execution-profile hashes;
- data and bounded warnings;
- compatibility/deprecation state;
- recommended next operation;
- retryability and safe error text.

Writes require idempotency keys and optimistic concurrency where state is mutable.

## 14. Eval standard before Eval Runner

The eval format must be fully defined and audited before it is trusted for certification.

### 14.1 Eval-suite v0.1 requirements

Each suite declares:

- suite ID, schema version, version/hash, owning skill version range;
- required runtime and execution profiles;
- fixtures and deterministic setup;
- case IDs and case types;
- invocation input and allowed contextual inputs;
- expected output/artifact contract;
- deterministic assertions;
- rubric dimensions, weights, anchors, and examples;
- hard-failure conditions;
- pass threshold and per-dimension minimums;
- toolchain lock and permitted certified alternatives;
- judge independence/model-family requirements;
- token/time/tool/cost budgets;
- evidence and redaction policy;
- regression baseline and comparison rule;
- cleanup and isolation requirements.

### 14.2 Required case classes

As applicable:

- golden/happy path;
- edge/boundary;
- negative/missing input;
- adversarial/prompt injection/tool misuse;
- regression from real incidents;
- routing/non-selection;
- tool failure and unavailable dependency;
- compatibility across required runtime profiles;
- efficiency/context-disclosure;
- side-effect safety/dry-run behavior.

### 14.3 Verification versus eval

- verification checks one actual run/artifact;
- eval executes repeatable cases to judge the skill version/profile;
- deterministic checks run before model judgment;
- the model that produced the output must not be the sole certifier of that output;
- prompt-only scoring with no observed output is prohibited.

### 14.4 Audit of the 34 suites

Produce a machine-readable audit report for every current suite:

- valid structure;
- scenario completeness;
- fixture availability;
- deterministic assertions;
- rubric specificity;
- hard-fail coverage;
- toolchain references;
- runtime profiles;
- adversarial/regression coverage;
- evidence policy;
- ready/not-ready reasons.

No existing suite should be assumed complete merely because the validator accepts its current YAML shape.

## 15. Real Eval Runner

### 15.1 Execution lifecycle

For each case/profile:

1. create an isolated, deterministic workspace;
2. resolve the immutable Skill Pack and exact tools;
3. seed approved fixtures;
4. invoke the target runtime/actor harness;
5. capture observable inputs, fragments, tool calls, outputs, artifacts, costs, and timings;
6. apply deterministic validations and hard failures;
7. invoke an independent high/frontier-tier judge only for qualitative rubric dimensions;
8. compute weighted scores using code, not model arithmetic alone;
9. compare against regression baseline;
10. persist evidence, hashes, and cleanup receipt;
11. aggregate the execution-profile verdict.

### 15.2 Reproducibility

Record:

- source/bundle/eval/tool hashes;
- runtime/adapter/model identifiers and capability profile;
- fixture hashes;
- environment image/platform information;
- deterministic check versions;
- judge provider/model/tier/version;
- random seed where relevant;
- token/tool/time/cost metrics;
- evidence artifact hashes.

### 15.3 Failure posture

- missing suite, fixture, tool, profile, or evidence means “cannot certify,” not pass;
- malformed model judgment fails closed;
- infrastructure failure is distinct from skill failure;
- flaky cases are quarantined and investigated, not repeatedly retried until passing;
- secrets and private content are redacted before evidence persistence.

## 16. Certification and release model

### 16.1 Certification unit

Certification belongs to:

```text
skill source/bundle hash
+ eval-suite hash
+ exact toolchain hashes
+ adapter version range
+ bounded runtime/model capability profile
= certified execution profile
```

Do not claim universal certification from one profile.

### 16.2 Runtime profiles for internal launch

At minimum:

- Cursor macOS profile;
- Codex macOS profile;
- Lisa/OpenClaw profile;
- Program-controlled executor profile when first needed.

Profiles specify capabilities rather than pinning every harmless model patch. Material model, adapter, tool, schema, or sandbox changes trigger compatibility checks based on blast radius.

### 16.3 Lifecycle states

Preserve compatible existing states while defining explicit release semantics:

- `draft`: source exists, not ready for eval;
- `eval_pending`: candidate/profile awaits or failed required eval;
- `usable`: certified published profile available internally;
- `deprecated`: still available for pinned consumers with replacement guidance;
- `retired`: unavailable for new runs, retained for audit/rollback history.

Release channels should distinguish development/eval, internal canary, and internal stable without turning channels into Program permissions.

### 16.4 Promotion rules

Promotion requires:

- source validation;
- complete required eval cases;
- no hard failure;
- threshold and per-dimension minimums;
- no prohibited regression;
- toolchain/profile compatibility;
- immutable bundle publication;
- audit/evidence receipt.

Git remains `issue/*` or `dev/*` -> PR to `development`; repository Integrator merges merge-ready work. Promotion to `staging` and `main` remains Principal-controlled under repository policy.

### 16.5 Rollback

Rollback changes the channel pointer/default profile to the last known-good immutable release. It does not mutate history. Active pinned runs remain auditable. A rollback creates an event and an improvement/regression candidate.

## 17. Telemetry, feedback, and trace-to-eval

### 17.1 Canonical observable event spine

Initial event types:

- `skill.requested`;
- `skill.candidates_returned`;
- `skill.selected` / `skill.not_selected`;
- `skill.fragment_disclosed`;
- `skill.run_started`;
- `tool.resolved` / `tool.called` / `tool.completed` / `tool.failed`;
- `artifact.produced`;
- `verification.completed` / `verification.failed`;
- `skill.run_completed` / `skill.run_failed` / `skill.run_abandoned`;
- `feedback.submitted`;
- `eval.candidate_created` / `eval.executed`;
- `release.promoted` / `release.demoted` / `release.rolled_back`.

### 17.2 Event envelope

Events include:

- event/schema version and event ID;
- actor, runtime, session, Program, repository, Issue/Run references where available;
- skill release and execution-profile hashes;
- tool release/hash where relevant;
- timestamp and sequence;
- outcome/failure classification;
- duration, token, tool, and cost metrics;
- safe artifact/evidence references;
- sensitivity/redaction classification;
- idempotency and correlation IDs.

### 17.3 Privacy boundary

Retain by default:

- identifiers, versions, lifecycle events, metrics, validations, error categories, artifact references/hashes, and explicit feedback.

Do not retain by default:

- hidden reasoning;
- credentials or authentication material;
- complete private conversations;
- unnecessarily large prompts/tool outputs;
- sensitive artifact bodies when a reference/hash is sufficient.

LiNKbrain, not LiNKskills, owns private conversation memory. An actor may separately send institutional findings to LiNKbrain under LiNKbrain's contracts.

### 17.4 Buffering and cost control

- batch ordinary events;
- flush immediately on run close/failure when practical;
- use idempotent batch receipts and sequence cursors;
- cache catalog/fragments by hash;
- avoid database calls for every thought or harmless local operation;
- track payload bytes, rows, embedding/model calls, and estimated cost per run.

### 17.5 Trace-to-eval

A failed run, user correction, missing step, tool incompatibility, or surprising success can become an eval candidate. The candidate stores a redacted minimal reproduction, expected behavior, provenance, affected profile, and evidence references.

The Librarian deduplicates and proposes the regression case. It does not silently add contaminated/private raw content to eval fixtures.

## 18. Institutional Librarian architecture

### 18.1 One identity, separate domain workers

The institutional Librarian remains one identity hosted by LiNKplatform, with separate workflows for:

1. LiNKbrain knowledge curation;
2. LiNKskills procedural-capability curation;
3. LiNKlibraries asset curation when that workflow is separately defined.

The workflows have separate credentials/scopes, evidence requirements, schedules, domain queues, domain contracts, telemetry, and failure states. LiNKplatform provides one generic worker-host lifecycle; it does not merge the domain workers or their data.

### 18.2 Repository ownership

LiNKskills owns:

- Librarian skill-domain requirements and schemas;
- candidate types and decision rules;
- eval and improvement execution;
- source-change/publishing interfaces;
- intake, improvement, eval, consolidation, release, and retirement behavior;
- the versioned LiNKskills domain-worker implementation and tests.

LiNKplatform owns:

- institutional identity;
- generic job host/scheduler/retry model;
- versioned worker loading and invocation;
- credentials and least privilege;
- shared logging, audit, and operational alerts;
- invoking the versioned domain worker contract.

LiNKbrain separately owns its LiNKbrain domain worker. Neither the LiNKskills nor LiNKbrain execution agent may independently edit the same existing files under `LiNKplatform/packages/librarian-runner`. Cross-repository contracts are defined first. Integration into the generic host requires a coordinated work packet owned and executed by the LiNKplatform agent, followed by domain conformance validation.

### 18.3 LiNKskills workflows

#### Intake and normalization

- receive a new/internal/imported skill candidate;
- inspect provenance/license;
- map it to Skill Pack v0.1;
- classify/category/index it;
- resolve overlaps/dependencies/tools;
- require complete eval definitions before certification.

#### Performance and improvement

- aggregate telemetry and feedback;
- prioritize by failure, impact, usage, cost, and confidence;
- reproduce observed failures;
- create trace-to-eval cases;
- propose source/eval/tool changes on a branch;
- run complete regression profiles;
- open a reviewable PR with evidence.

#### Consolidation

- detect duplicate/overlapping skills;
- compare responsibilities, routing, performance, and dependencies;
- propose merge, split, or clearer routing;
- preserve aliases/migration guidance and historical run references;
- require Principal review for ambiguous/high-impact consolidations.

#### Lifecycle

- deprecate with replacement/migration guidance;
- retire noncompliant, insecure, obsolete, or unused skills;
- roll back regressions;
- archive source/history without deleting audit evidence.

### 18.4 Autonomy boundary

The Librarian may autonomously normalize, diagnose, create branches, modify domain source, run evals, open PRs, and recommend/publish clean internal releases through the normal integration process.

It may not:

- bypass CI/evals or repository integration;
- push directly to `staging` or `main`;
- rewrite published versions;
- grant Program permissions;
- auto-apply low-confidence/high-impact merge/split decisions;
- hide regressions or unresolved evidence gaps.

### 18.5 Replace prompt-only scoring

The current `scoreSkill` path must not certify after receiving only identifiers and rubric names. LiNKplatform integration must consume a signed/hashed Eval Runner result containing actual case evidence. The model judge may score qualitative observed outputs, but deterministic orchestration computes the verdict.

## 19. Proposed operational data model

Final SQL names require ADR and migration review. Logical entities include:

### 19.1 Registry/publication

- skills;
- skill_versions;
- skill_fragments;
- skill_dependencies;
- releases/channels;
- immutable_bundle_records;
- runtime_profiles;
- execution_profiles;
- certifications;
- compatibility_results.

### 19.2 Tools

- tools;
- tool_versions;
- tool_capabilities;
- tool_dependencies;
- tool_compatibility;
- skill_tool_bindings.

### 19.3 Evals

- eval_suites/versions;
- eval_cases;
- eval_runs;
- eval_case_runs;
- deterministic_check_results;
- rubric_judgments;
- evidence_artifacts;
- regression_baselines.

### 19.4 Runtime and telemetry

- actor_runtime_bindings referencing canonical LiNKplatform actor IDs;
- skill_runs;
- run_events;
- fragment_disclosures;
- tool_invocations;
- artifacts/references;
- feedback;
- trace_to_eval_candidates.

A skill run may store an optional LiNKbrain task/activity reference strictly for correlation. It must not copy the Brain activity, checkpoint, transcript, or private-memory payload. LiNKbrain may separately record the certified skill release/execution-profile reference that contributed to an outcome; it must not copy Skill Packs, eval artifacts, or certification evidence.

### 19.5 Librarian and release operations

- curation_jobs;
- improvement_proposals;
- intake_candidates;
- consolidation_candidates;
- review_queue/escalations;
- release_events;
- purge/retention receipts.

Extend current tables additively where practical. Do not destructively rewrite applied migrations.

## 20. Identity, security, and trust

### 20.1 Actor identity

LiNKplatform is the canonical authority for actor identity, organisation membership, authentication, and credential issuance/lifecycle. LiNKskills defines the claims it requires and the conformance tests for accepting them. LiNKskills may persist domain-specific bindings that reference the canonical platform actor ID; it must not create a competing permanent actor authority.

Resolve from authenticated platform claims and LiNKskills bindings:

- actor ID/kind;
- organization;
- runtime profile and adapter version;
- session/run correlation;
- Program/repository/Issue context where present;
- allowed LiNKskills operations.

Actors never receive Supabase service-role or Librarian credentials.

Minimum shared claim expectations include the platform actor ID, actor kind, organisation membership/internal status, allowed service scopes, credential identity, and expiry/rotation metadata. The exact token format and issuer implementation belong to LiNKplatform. LiNKskills owns rejection behavior, claim-version compatibility, and test fixtures for the operations it exposes.

### 20.2 LiNKskills access versus permission to act

LiNKskills may control access to its own draft/private/eval content and tool service. It does not authorize the underlying Program operation. The actor host/Program must independently approve tool side effects.

### 20.3 Mandatory controls

- TLS for non-loopback access;
- scoped short-lived credentials or approved OAuth/service identity;
- GSM-managed secrets and rotation;
- server-derived actor identity;
- RLS/role tests;
- content and payload limits;
- immutable release hashes;
- supply-chain/provenance checks;
- prompt-injection treatment of skill inputs and telemetry as untrusted data;
- logs without secrets, raw private conversations, or unnecessary artifacts;
- audit of publication, certification, restricted reads, and tool invocation.

LiNKskills telemetry must never ingest raw LiNKbrain conversations, private Brain memory, checkpoints, or handoff content. Cross-service correlation uses opaque IDs and approved outcome references only.

### 20.4 Tool security

Tool tests include malformed input, path traversal, secret leakage, network boundaries, timeout, partial failure, idempotency, and side-effect classification. Security-sensitive tools need independent review before stable publication.

## 21. Actor integrations

### 21.1 Shared integration contract

An actor is fully integrated only when it can:

- authenticate;
- discover and progressively load skills;
- create/close correlated runs;
- resolve and invoke exact tools;
- validate outputs;
- buffer/flush telemetry;
- submit feedback;
- report degraded access honestly.

Merely mounting Skill Pack files is not a complete integration.

LiNKbrain and LiNKskills remain separate even when one actor consumes both. An adapter must expose `brain_*` and `skills_*` tools separately and preserve independent endpoints, credentials/scopes, queues/buffers, telemetry, feature flags, health, and rollback. A Brain task/activity ID may correlate a skill run, but raw Brain conversation/private-memory content is never a LiNKskills telemetry input.

### 21.2 Cursor macOS — first canary

Cursor is first because it is the approved LiNKskills product canary and can exercise the new surface during development. This does not mean that every Grok execution agent running inside Cursor owns Cursor's shared configuration.

LiNKskills owns:

- MCP service and contract;
- Cursor integration template/installer and conformance fixtures;
- durable LiNKskills usage guidance;
- test profiles and diagnostics.

Cursor-specific implementation uses current official capabilities:

- `.cursor/mcp.json` or the approved global MCP configuration;
- Cursor Agent/IDE MCP tools;
- Cursor rules/`AGENTS.md` for lifecycle guidance;
- hooks where they materially improve telemetry/finalization rather than duplicating server-side records.

Because this repository's `.cursor` path is a symlink to the shared IDE Development system, implementation must first decide whether LiNKskills belongs in global Cursor MCP configuration or a separately owned project configuration. Do not casually edit the shared symlink target.

Prefer an isolated or project-scoped canary configuration. No execution agent may change shared/global Cursor rules, MCP configuration, hooks, extensions, IDE Development symlink targets, or user-level settings merely because it runs inside Cursor. If a global Cursor mutation is unavoidable, the LiNKskills execution agent must:

1. stop before making the change;
2. document the exact mutation, affected active agents, validation, and rollback;
3. obtain a coordinated maintenance window;
4. confirm the other three Grok sessions will not be disrupted;
5. apply and verify the change only within the approved window;
6. record the result and restoration path in its implementation handoff.

Cursor canary acceptance:

1. discover representative usable skills;
2. select one with correct routing explanation;
3. disclose only required fragments;
4. invoke an exact packaged tool;
5. produce/validate an artifact;
6. record complete telemetry and feedback;
7. demonstrate unavailable-tool and failed-run paths;
8. operate from another repository without a LiNKskills checkout dependency.

### 21.3 Codex macOS — second actor

Codex validates that the service is not Cursor-specific.

Use current supported surfaces:

- MCP configuration in user or trusted project `config.toml`;
- concise `AGENTS.md` lifecycle guidance;
- project/global hooks only where they add reliable finalization or diagnostics;
- the same LiNKskills release/profile contracts used by Cursor.

For this four-agent rollout, the LiNKbrain execution agent is the default owner of shared Codex host configuration: shared `config.toml` edits, common hook registration, and common Codex-side lifecycle scripts. LiNKskills owns its service, Codex-facing requirements, independently named Skills configuration fragment, LiNKskills conformance tests, and validation of the configured Skills behavior. The LiNKskills agent must not concurrently edit shared Codex configuration.

The LiNKbrain integration owner applies separate Brain and ready Skills MCP entries through a coordinated Codex work packet. If the Principal later assigns a dedicated Codex integration agent, that explicit assignment supersedes this default. Whether configuration is user-level or project-level remains an implementation decision; ownership of the shared file does not. Re-check the installed Codex version and current official manual immediately before implementation because configuration and hook surfaces can change.

Codex acceptance repeats the Cursor scenarios and additionally proves that the same published release/evidence is consumed without Cursor-specific representation.

### 21.4 Lisa/OpenClaw Prime — third actor

OpenClaw-specific changes are owned by the `openclaw_prime` repository agent.

LiNKskills supplies:

- MCP/API contracts;
- generic client behavior;
- runtime-profile/eval requirements;
- an independently named configuration fragment;
- a fake LiNKskills service and conformance fixtures;
- conformance tests and safe fixtures.

The OpenClaw Prime agent owns:

- managed MCP configuration;
- any thin plugin/modules and hook integration;
- Lisa actor/session correlation;
- all local buffers/outboxes if plugin state is required;
- integration tests, live-profile rollout, and rollback documentation.

Preserve:

- Lisa's existing local memory and compaction;
- built-in OpenClaw skills/tools;
- heartbeat, cron, channels, and profile behavior;
- OpenClaw plugin/core ownership boundaries.

The older `PHASE1-LINKBRAIN-LINKSKILLS.md` Git `extraDirs` proposal becomes historical for LiNKskills delivery. It may remain as migration context, but production usage moves to the LiNKskills MCP/API and published registry.

OpenClaw integration should use the smallest verified set of public plugin hooks after inspecting the checked-out version. Do not modify OpenClaw core when managed MCP plus a plugin can satisfy the requirement.

The LiNKskills execution agent must not modify OpenClaw internals unless a coordinated cross-repository work packet explicitly transfers ownership of exact files. The future OpenClaw design may use one thin plugin with separate Brain and Skills modules, or separate plugins, but it must preserve separate services, credentials/scopes, queues, telemetry, feature flags, and failure states. The OpenClaw agent may enable LiNKbrain before LiNKskills because their readiness gates are independent.

## 22. Operational interface

### 22.1 Canary interface

A CLI/generated report is sufficient initially. It must show:

- catalog versions and states;
- execution profiles and compatibility;
- eval readiness and evidence;
- runs/failures/feedback;
- tool health and dependency blast radius;
- Librarian candidate/job status;
- release/rollback history;
- costs and telemetry gaps.

### 22.2 General internal-launch interface

Before general internal launch, provide a minimal readable dashboard or equivalent generated operational report. It need not become a full commercial LiNKconsole. It must make failures and uncertified states visible without direct SQL inspection.

## 23. Detailed implementation sequence

Every phase requires a scoped work packet, repository ownership declaration, tests, evidence, handoff, and approval gate. Later phases must not treat unverified earlier work as complete.

### Phase 0 — Approval, ADRs, and source-of-truth reconciliation

**Primary owner:** LiNKskills

**Goal:** make the approved end state authoritative before feature implementation.

Work:

1. Principal reviews/approves this plan.
2. Add ADRs for:
   - Git source + LiNKplatform publication/storage;
   - protocol-independent core with MCP/API adapters;
   - Skill Pack v0.1 and progressive disclosure;
   - tool execution/binding and host authority;
   - complete execution-profile certification;
   - telemetry/privacy/retention;
   - Librarian ownership and cross-repository contract.
3. Update Intent, Technical PRD, Operations Manual, README, and OPEN-ISSUES.
4. Mark conflicting historical Git-checkout/runtime documents as superseded without deleting history.
5. Establish `docs/handoffs/` and repository-local session/handoff expectations if retained by root rules.
6. Document the stale shared `.cursor` identity instructions and isolate the LiNKskills canary through project-scoped configuration where possible; do not edit the shared symlink target without the Cursor maintenance gate.
7. Inventory every current LiNKskills consumer, direct PostgREST credential, checkout path, tool dependency, and Librarian integration.
8. Confirm applied stage/prod `lskills` migrations and current storage/hosting conventions without claiming unverified health.
9. Publish LiNKskills requirements and conformance fixtures for the LiNKplatform actor/auth claim contract.
10. Define the versioned LiNKskills Librarian domain-worker contract and the coordinated LiNKplatform integration handoff; do not edit shared runner files.
11. Define independently named Cursor, Codex, and OpenClaw configuration fragments, fake service behavior, and conformance boundaries.
12. Accept and record the cross-plan interface gates and sole-owner mutation surfaces in Section 29.
13. Assign the four Cursor/Grok execution agents to separate repository checkouts/worktrees, branches, and session/ownership records; assign the four Codex verifiers and LiNKbrain coordinating verifier.
14. Establish the approved deviation process and execution-to-verification handoff format before implementation starts.
15. Inventory shared/global Cursor and Codex mutation surfaces. Reserve Cursor product-canary changes to LiNKskills and shared Codex host configuration to the default LiNKbrain integration owner.

Exit evidence:

- approved ADRs and aligned source-of-truth docs;
- consumer/credential/integration inventory;
- repository ownership matrix;
- no ambiguity that permission-to-act remains external;
- no ambiguity that LiNKbrain/LiNKskills are separate services.
- accepted cross-plan gates and one named owner for every shared mutation surface;
- named execution/verifier roles, isolated worktrees/branches, and standard evidence handoff;
- no execution agent has changed shared/global Cursor configuration merely to set up its development environment.

### Phase 1 — Contracts, Skill Pack v0.1, and eval standard

**Owner:** LiNKskills

**Goal:** define behavior and evidence before service/database expansion.

Work:

1. Versioned schemas for Skill Pack, fragments, dependencies, tool descriptors, runtime/execution profiles, runs/events, feedback, releases, and errors.
2. Eval-suite v0.1 schema and examples.
3. Pure lifecycle, selection, compatibility, certification, release, and retention policies.
4. Update authoring meta-skills and validator.
5. Audit all 34 skill suites and 19 tool packages.
6. Select a representative 5–10 skill canary set covering simple/heavy, tool/no-tool, artifact, side-effect, failure, and routing differences.

Exit evidence:

- schemas and compatibility fixtures;
- validator tests and migration audit;
- each existing skill/eval/tool has a readiness finding;
- no service implementation is needed to understand expected behavior.

### Phase 2 — Publishing and operational registry foundation

**Owners:** LiNKskills authors/tests the domain migrations; LiNKplatform alone reviews, sequences, applies, and operates them on shared stage/production

**Goal:** publish immutable releases without runtime Git checkout dependency.

Work:

1. Additive schema/storage changes for releases, bundles, fragments, tools, dependencies, profiles, and certifications.
2. Publisher builds deterministic hashed bundles.
3. Storage upload and transactional release record.
4. Server-side catalog/browse/search functions.
5. Least-privilege service roles/RLS.
6. Backfill current catalog as draft source records; do not mark usable.
7. Produce a migration manifest containing ordered files, prerequisites, schema/policy intent, hashes, verification evidence, rollback/forward-fix instructions, and expected operational checks.
8. Hand the package to the LiNKplatform agent. The LiNKskills execution agent must not independently apply it to shared live environments.

Validation:

- fresh and upgrade migration tests;
- RLS actor/Librarian/observer/wrong-org matrix;
- deterministic bundle reproducibility;
- corrupted/mismatched bundle rejection;
- query plans and bounded responses;
- rollback procedure on stage clone.
- LiNKplatform-owned stage application receipt identifies the reviewed manifest/version and operator; production remains separately gated.

### Phase 3 — Tool registry/runtime and real Eval Runner

**Owner:** LiNKskills

**Goal:** replace declarative/prompt-only certification with observed execution.

Work:

1. Normalize tool descriptors and typed bindings.
2. Implement local/server execution adapters and exact-hash resolution.
3. Build isolated eval workspace/fixture lifecycle.
4. Implement deterministic assertions and hard failures.
5. Implement independent qualitative judge adapter.
6. Compute scores/metrics deterministically.
7. Persist case/run/profile evidence.
8. Run canary suites; repair suites before blaming skills where specification is incomplete.

Exit evidence:

- every canary profile has actual outputs/tool traces/checks;
- prompt-only runner cannot certify;
- failure/infrastructure/flaky classifications proven;
- exact toolchain is visible in certification evidence.

### Phase 4 — Gateway Service and MCP/API

**Owner:** LiNKskills

**Goal:** provide the secure shared consumer interface.

Work:

1. Implement domain application services.
2. Implement actor auth/claim mapping.
3. Implement HTTP endpoints and MCP adapter over identical operations.
4. Implement search, selection, progressive disclosure, runs, validation, tool resolution/invocation, and feedback.
5. Implement idempotency, rate/payload limits, health/readiness, metrics, and audit.
6. Implement generic client and local event buffer.
7. Preserve a migration wrapper for current Python consumers until they move.

Exit evidence:

- HTTP/MCP parity;
- no actor can choose another identity;
- no broad database credential reaches consumers;
- ordinary runs use published immutable bundles;
- retries do not duplicate runs/events;
- bounded progressive disclosure is measured.

### Phase 5 — Telemetry, feedback, and trace-to-eval

**Owner:** LiNKskills

**Goal:** make real use improve future versions.

Work:

1. Add full event spine and retention/redaction rules.
2. Add adapter buffering/batch receipts.
3. Add feedback and artifact-reference handling.
4. Add quality/cost aggregations.
5. Add manual trace-to-eval queue and deduplication.
6. Prove one failed/corrected canary run becomes a regression candidate and later an eval case.

Exit evidence:

- complete event sequence for success/failure;
- no hidden reasoning/secrets/private transcript captured;
- offline retry proven;
- cost and missing-sequence diagnostics visible.

### Phase 6 — Librarian LiNKskills domain worker

**Owners:** LiNKskills domain; LiNKplatform host/integration

**Goal:** implement the intended curation lifecycle.

LiNKskills work:

- publish the versioned domain-worker interface and compatibility fixtures;
- intake/normalization;
- performance prioritization;
- improvement branch/PR proposal;
- eval execution request and evidence interpretation;
- consolidation and lifecycle proposals;
- durable domain review queue.

LiNKplatform work:

- load and invoke the versioned LiNKskills worker in the generic institutional host;
- integrate versioned worker contract;
- scheduler/retries/credentials;
- job observability and escalation delivery;
- keep LiNKbrain and LiNKskills runs independently executable.

The LiNKskills and LiNKbrain agents must not independently modify the same existing files under `LiNKplatform/packages/librarian-runner`. The LiNKplatform agent owns the coordinated integration work packet and shared-file implementation. LiNKskills validates the hosted worker through its domain conformance suite and reports defects back to the platform owner.

Validation:

- telemetry failure -> candidate -> source/eval proposal -> real eval -> clean release or escalation;
- new skill -> normalized draft -> complete eval -> publication;
- duplicate/merge/split/retirement proposals remain evidence-backed;
- no direct staging/main push;
- brain workflow remains unaffected.

### Phase 7 — Cursor macOS canary

**Owner:** LiNKskills execution agent owns the Cursor product canary; shared/global mutation still requires the coordinated maintenance gate

**Goal:** first real actor proves the end-to-end system while developing it.

Stages:

1. prove fake/contract tests using isolated or project-scoped configuration;
2. inspect `.cursor` symlinks and shared/global settings read-only and record exact ownership;
3. stage read-only discovery;
4. stage run/telemetry with non-side-effecting skills;
5. exact packaged tool and artifact validation;
6. controlled failures/feedback/offline buffer;
7. Librarian dry-run then evidence-backed write mode;
8. multi-day real use of the representative canary set.

If global Cursor configuration is unavoidable, stop before mutation, obtain the coordinated maintenance window in Section 21.2, confirm the other three Grok sessions will not be disrupted, and include exact rollback evidence in the handoff.

Exit gate:

- agreed canary metrics meet thresholds;
- no unresolved privacy/security/certification issue;
- rollback and removal of Cursor integration proven.

### Phase 8 — Codex macOS interoperability

**Owners:** LiNKskills supplies requirements/fragment/tests and validates; LiNKbrain execution agent is the default shared Codex host-configuration owner

**Goal:** prove the contracts are not Cursor-specific.

Work:

- freeze the independently named `skills_*` endpoint/configuration fragment and Codex conformance suite;
- hand that fragment to the shared Codex integration owner after the Skills readiness gate;
- shared owner configures the same Skills MCP endpoint without combining it with Brain credentials, tools, or failure state;
- shared owner adds coordinated concise lifecycle guidance and common hooks without duplicate registration;
- run equivalent conformance scenarios;
- certify required Codex profiles;
- compare disclosure, tool, result, latency, and telemetry behavior;
- prove configuration rollback.

The LiNKskills execution agent must not concurrently edit the shared `config.toml`, common hook registration, or common lifecycle scripts. If a dedicated Codex integration agent is later assigned, the handoff targets that owner instead.

Exit gate:

- same release works through both actors where profiles claim compatibility;
- profile-specific limitations are explicit;
- no consumer holds broad database credentials.

### Phase 9 — Lisa/OpenClaw Prime integration

**Owner:** OpenClaw Prime agent, using LiNKskills contracts

**Preflight:** read current OpenClaw rules, dashboard, active sessions, recent handoffs, live Lisa profile read-only/sanitized, and current plugin/MCP contracts. Use a dedicated branch/worktree and coordinate overlap.

Work:

1. LiNKskills freezes the Skills MCP/API contract, runtime-profile requirements, configuration fragment, fake service, and conformance suite;
2. OpenClaw configures managed MCP and scoped Skills actor credentials;
3. OpenClaw implements a thin plugin/module only for lifecycle/buffering gaps;
4. OpenClaw owns Lisa actor/session mapping, buffers/outboxes, hooks, live profile, tests, rollout, and rollback;
5. preserve native skill/tool/memory behavior and keep Brain/Skills service state separate;
6. certify Lisa runtime profiles;
7. stage then production canary after the Skills readiness gate;
8. record rollback without changing unrelated Lisa services/config.

The LiNKskills execution agent validates the delivered adapter but does not edit OpenClaw internals. Raw Brain conversations/private memory must never enter Skills telemetry. OpenClaw may already have Brain enabled; that is neither a blocker nor proof that Skills is ready.

Exit gate:

- Lisa uses published LiNKskills in real work;
- built-in skills remain available;
- native memory/compaction/heartbeat/cron/channels remain healthy;
- telemetry/eval evidence is complete and private data boundaries hold.

### Phase 10 — General internal launch and closeout

**Owner:** LiNKskills, with cross-repository evidence

Work:

1. classify all 34 skills deliberately as usable/draft/deprecated/retired;
2. certify intended launch profiles, not necessarily every draft skill;
3. provide minimal dashboard/report;
4. complete security/privacy/supply-chain review;
5. demonstrate backup/restore, purge, and rollback;
6. update operations manuals in every changed repository;
7. record production evidence and remaining roadmap.

Launch decision is based on evidence, not the number of files or green structural validation alone.

### Phase 11 — Independent plan-conformance verification and cross-plan reconciliation

**Owners:** LiNKskills Codex verifier for this repository; LiNKbrain Codex coordinating verifier for the four-plan result

**Goal:** independently determine what was actually delivered before accepting the Grok completion report or internal launch.

The LiNKskills Codex verifier reads the approved plan, execution handoff, actual repository, tests, eval evidence, migration manifest/application receipts, configuration evidence, service/deployment evidence, and live proof where required. Every planned item is classified as exactly one of:

- implemented and proven;
- implemented but not proven live;
- partially implemented;
- omitted;
- implemented differently from plan;
- blocked by another repository/interface;
- outside the execution agent's ownership.

The verifier reruns or independently inspects proportionate checks instead of accepting copied terminal summaries. Deficiencies become a correction work packet for the original LiNKskills Grok execution owner. The verifier must not silently take over implementation unless the Principal explicitly authorises that role change.

After all four repository verifiers report, the LiNKbrain Codex coordinating verifier reconciles contract versions/hashes, actor claims, migration application, Librarian loading, OpenClaw/Codex configuration, rollout gates, and cross-service privacy. A repository or interface remains incomplete when evidence is provisional, contradictory, or owned by another plan but not delivered.

## 24. Test strategy

### 24.1 Unit tests

- schemas and validation;
- selection/routing/exclusions;
- fragment disclosure;
- dependency/tool compatibility;
- run and release state machines;
- scoring, thresholds, hard failures, regression comparison;
- telemetry redaction/retention;
- Librarian candidate decisions;
- idempotency and offline cursors.

### 24.2 Database/storage tests

- fresh/upgrade migrations;
- RLS/roles;
- atomic publication/run close;
- uniqueness/concurrency;
- search indexes/query plans;
- immutable bundle/evidence hashes;
- retention and audit receipts;
- backup/restore.

### 24.3 Contract tests

- MCP/API parity;
- version negotiation;
- bounded responses;
- Cursor/Codex/OpenClaw fixtures;
- malformed/old client behavior;
- exact tool resolution;
- retries/partial failure.
- canonical LiNKplatform actor claim acceptance/rejection and actor-ID binding;
- independently named `skills_*` tools with no `brain_*` alias or combined Gateway behavior;
- Brain task/activity correlation by opaque reference without Brain payload ingestion;
- versioned LiNKskills Librarian worker compatibility with the generic host fixture;
- independently named Cursor, Codex, and OpenClaw configuration fragments.

### 24.4 Eval-system tests

- golden/edge/negative/adversarial/regression cases;
- missing/malformed fixtures;
- tool unavailable/fails/times out;
- judge malformed/unavailable;
- executing model and judge independence;
- flaky-case quarantine;
- profile mismatch;
- budget exceeded;
- deterministic evidence reproduction.

### 24.5 End-to-end scenarios

1. Cursor searches, selects, loads, runs, validates, and closes a skill.
2. Same release works in Codex under a compatible profile.
3. Lisa runs it without replacing built-in skills or memory.
4. Tool version changes and affected profiles return to eval-pending.
5. User correction becomes a deduplicated regression eval candidate.
6. Librarian proposes an improvement, real evals pass, release publishes.
7. Regression blocks/demotes and rollback restores last known good.
8. Wrong actor cannot access restricted development/eval evidence.
9. Service outage uses verified cache and later flushes telemetry exactly once.
10. Program denial remains a Program concern; LiNKskills does not bypass it.
11. A LiNKbrain task reference correlates to a skill run without copying Brain conversation/private-memory data.
12. Brain and Skills fail, recover, disable, and roll back independently in a dual-service consumer.
13. LiNKplatform applies the reviewed `lskills` migration manifest while the LiNKskills agent has no live migration credential/action.
14. OpenClaw and shared Codex adapters pass Skills conformance without combining domain credentials, telemetry, queues, or tool namespaces.

### 24.6 Independent plan-conformance verification

The LiNKskills Codex verifier must map every Phase 0–10 task, validation item, exit criterion, definition-of-done item, and ownership boundary to actual evidence using the seven classifications in Phase 11. Verification includes:

- inspecting the dedicated Grok checkout/worktree, branch, session record, and handoff;
- comparing changed files with the repository ownership matrix and explicitly untouched boundaries;
- rerunning representative unit, integration, database, MCP/API, eval, actor-conformance, migration-package, and rollback checks;
- distinguishing local/mock/stage evidence from actual live proof;
- checking configuration, credentials, migrations, deployments, and live actions against their assigned owner;
- verifying contract versions and hashes consumed across repositories;
- issuing a correction work packet to the original execution owner for every deficiency.

The execution agent's report is evidence input, not verification. Only the Codex verifier may mark the LiNKskills implementation plan-conformant, and only the LiNKbrain coordinating verifier may declare the four-plan interfaces reconciled.

## 25. Observability, operations, and cost

Provide:

- `/health` and `/ready`;
- catalog/publication/profile reports;
- eval queue/run/failure visibility;
- tool health and compatibility reports;
- telemetry missing-sequence/dead-letter visibility;
- Librarian job/review/escalation reports;
- release/rollback audit;
- actor integration diagnostics;
- credential rotation/revocation procedure;
- incident runbooks.

Measure:

- discovery relevance and false selection;
- context/fragments/full-pack disclosure;
- run success/failure/abandonment;
- verification and eval pass rates;
- tool failure and mismatch;
- user correction/satisfaction;
- latency, tokens, tool calls, payload bytes, embeddings/models, and estimated cost;
- Librarian candidate acceptance/regression/escalation;
- cache/offline recovery;
- actor-specific integration overhead.

Cost controls include batching, caching, deterministic checks before model judgment, bounded retrieval, canary-sized eval matrices, and avoiding model calls when code can decide.

## 26. Migration and backward compatibility

- preserve current Git loader during a bounded migration window;
- add a compatibility client that maps old load/record calls to the Gateway where practical;
- inventory and migrate consumers before tightening direct DB/catalog access;
- do not let compatibility paths serve draft skills as though usable;
- mark old Git `extraDirs`/checkout deployment as deprecated after all three actors pass;
- remove steady-state direct PostgREST actor credentials only after replacement proof;
- archive legacy JSONL rows according to retention policy;
- keep old published identities/audit history queryable.

Compatibility is temporary and has an owner/removal criterion. Do not create permanent dual sources of truth.

## 27. Deployment and rollback

Use independent feature flags/capabilities for:

- catalog read/search;
- progressive disclosure;
- skill runs;
- tool resolution/invocation;
- telemetry/feedback;
- eval execution;
- publication;
- Librarian intake/improvement/consolidation;
- each actor adapter.

Rollback order:

1. disable affected actor adapter/tool surface;
2. point release channel to last known-good immutable version;
3. stop new writes while preserving local buffers;
4. keep safe catalog reads available if possible;
5. stop Librarian publication while retaining evidence;
6. investigate without deleting tables/bundles;
7. restore previous integration config and prove actor-native behavior.

## 28. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Prompt-only certification continues | Eval Runner evidence becomes mandatory; identifiers/rubric names alone cannot create certification. |
| Git/database split becomes dual truth | Explicit authoring vs publication authority, immutable hashes, one-way publication pipeline. |
| Tool change silently breaks skills | Exact toolchain lock, reverse dependencies, blast-radius compatibility checks. |
| LiNKskills becomes permission layer | ADR 0001, host/Program authority, no leases/grants in domain contracts. |
| Context bloat | Ranked small results and addressable fragments; full pack explicit. |
| Telemetry leaks private data | Observable-event schema, redaction, references/hashes, no raw conversations. |
| Librarian edits unsafe source | Reviewable branches/PRs, complete evals, no staging/main direct push. |
| Librarian repo ownership collisions | Domain contracts first; LiNKplatform agent integrates shared runner; one owner per work packet. |
| MCP ties internal model to one client | Protocol-independent core and API parity tests. |
| Runtime-specific behavior is overclaimed | Bounded certification profiles and cross-actor conformance. |
| OpenClaw regressions | Thin plugin/managed MCP, preserve native systems, separate repo agent and staged canary. |
| Cursor shared `.cursor` edits affect other repos | Preflight global/project ownership; do not casually edit symlink target. |
| A global Cursor canary change disrupts the other three Grok execution sessions | Prefer project-scoped configuration; if unavoidable, stop, document impact/rollback, obtain a maintenance window, confirm all sessions are safe, then apply and verify once. |
| LiNKskills and LiNKbrain agents edit shared Codex configuration concurrently | LiNKbrain is the default shared Codex integration owner; LiNKskills supplies a separate fragment/tests and validates after application. |
| A domain agent independently applies shared live migrations | LiNKskills only authors/tests and hands off a hashed manifest; LiNKplatform is the sole stage/production reviewer, sequencer, applier, and operator. |
| Brain and Skills collide in the shared Librarian runner | Separate versioned domain workers; LiNKplatform owns generic-host integration and existing shared runner files. |
| Brain private content leaks into skill telemetry | Opaque correlation IDs only; schema rejection, adapter tests, redaction, and no raw Brain conversation/private-memory fields. |
| Four execution agents redefine plans to unblock themselves | Approved-plan control requires stop, impact record, verifier/coordinator review, and a plan-level decision before dependent work resumes. |
| Grok completion is accepted without independent proof | Completion stays provisional until the repository Codex verifier classifies every planned item and the LiNKbrain Codex agent reconciles shared interfaces. |
| All 34 skills delay useful canary | Representative 5–10 canary; deliberate classification for general launch. |
| External/commercial manual scope expands MVP | Explicit Mode 1 boundary and deferred roadmap. |

## 29. Repository ownership, interface gates, and concurrent execution

Four repository-specific Cursor agents using Grok 4.5 High Fast execute the approved LiNKskills, LiNKbrain, LiNKplatform, and OpenClaw Prime plans concurrently. Each requires an assigned repository, separate checkout/worktree, dedicated branch, session/ownership record, and implementation handoff. Concurrent work is allowed only on independently owned files and components.

Four Codex 5.6 Sol Medium agents independently verify the matching repositories. The LiNKbrain Codex verifier then reconciles all four verified results. A Grok completion report is provisional until this verification chain completes.

### 29.1 Ownership principles

1. **Domain defines and implements its domain.** LiNKskills owns Skill Packs, tools, evals, certification, registry behavior, Gateway, `skills_*` MCP/API, `lskills` migration source, domain worker, and conformance tests.
2. **LiNKplatform owns shared foundations and live operations.** It owns canonical actor identity/authentication, credential issuance/lifecycle, shared deployment/audit/observability conventions, live migration application, and the generic Librarian host.
3. **Consumer repository owns its internals.** OpenClaw Prime owns all Lisa/OpenClaw implementation. The shared Codex integration has one owner. Cursor product-canary changes belong to LiNKskills but do not make shared/global Cursor settings casually editable.
4. **Contract producer validates the consumer.** LiNKskills supplies stable contracts, fakes, configuration fragments, and conformance fixtures, then validates the owner-delivered adapter.
5. **No casual cross-repository editing.** A cross-repository work packet must name exact files, owner, branch/worktree, inputs, acceptance criteria, and handoff before ownership can transfer.
6. **Plans control execution.** An execution agent cannot redefine architecture or ownership. Deviations follow Section 2's stop-and-escalate process.
7. **Verification is independent.** The Codex verifier reports deficiencies and sends corrections to the original Grok owner; it does not silently implement them.

### 29.2 Repository ownership matrix

| Work or mutation surface | LiNKskills agent | LiNKplatform agent | LiNKbrain agent | OpenClaw Prime agent |
|---|---|---|---|---|
| Skill Pack/tool/eval/certification contracts and implementation | **Own/implement** | Consume/host support | No change | Consume |
| LiNKskills Gateway, `skills_*` MCP/API, client, tests | **Own/implement** | Auth/infrastructure support | Separate Brain service | Consume adapter contract |
| Canonical actor identity, organisations, shared token/credential issuer | Supply claim requirements/tests | **Own/implement/operate** | Supply Brain requirements/tests | Consume |
| LiNKskills actor/runtime/run bindings | **Own; reference platform actor ID** | Supply canonical ID | No change | Supply runtime context |
| `lskills` migrations and policies | **Author/test/package** | **Review/sequence/apply/operate live** | No change | No change |
| Shared stage/production migration execution | Must not apply independently | **Sole live owner** | Must not apply independently | No change |
| Published bundle storage conventions/operation | Define bundle and publication behavior | Provide/operate approved storage | Separate Brain storage | Consume |
| Real Eval Runner | **Own/implement** | Hosting/credential support if approved | No change | Runtime-profile fixtures |
| LiNKskills Librarian domain worker | **Own logic/contracts/tests** | Integrate/host/schedule | Own separate Brain worker | No change |
| Generic Librarian host and existing `packages/librarian-runner` shared files | Consume via versioned contract | **Sole integration/implementation owner** | Consume via versioned contract | No change |
| Cursor LiNKskills product canary | **Own, prefer project scope** | Identity/credentials | No Brain Phase 1 production rollout | No change |
| Shared/global Cursor environment used by all Grok agents | No change except approved maintenance-gated canary mutation | No change | No change | No change |
| Shared Codex host configuration for this rollout | Supply separate Skills fragment/tests; validate | Identity/credentials | **Default integration owner** | No change |
| OpenClaw/Lisa MCP, plugins/modules, hooks, buffers, mapping, profile, tests, rollout | Contract/fragment/fake/conformance/validation only | Identity/credentials/hosting | Separate Brain contract/validation | **Sole implementation/live owner** |
| Program permission, Issues, Runs, gates, deployments | Never | Capability foundation only | Never | Respect Program/host authority |

### 29.3 Separate services and cross-service correlation

LiNKbrain and LiNKskills remain independently deployable and operable: separate endpoints, schemas, credentials/scopes, MCP namespaces, caches, queues, telemetry, retention, failures, and feature flags. They share only LiNKplatform-defined actor/organisation claims, correlation identifiers, credential/deployment/audit/observability conventions, and the generic Librarian worker-host lifecycle.

LiNKskills may record an opaque LiNKbrain task/activity reference. LiNKbrain may record the certified skill release/execution profile that contributed to an outcome. Neither duplicates the other's domain data: LiNKskills does not read/store raw Brain conversations or private memory, and LiNKbrain does not copy Skill Packs, eval artifacts, or certification evidence.

### 29.4 Cross-plan interface gates

The agents may work concurrently on their independently owned Phase 0 and contract tasks. They may not bypass these gates because another plan is unfinished:

1. **Identity gate:** LiNKplatform publishes the canonical actor/auth claim contract and fixtures. LiNKskills may develop against fakes, but cannot declare live authentication complete beforehand.
2. **Migration gate:** LiNKskills supplies a versioned migration manifest, tests, evidence, and rollback/forward-fix instructions. LiNKplatform alone reviews, sequences, and applies shared live migrations.
3. **Librarian gate:** LiNKskills and LiNKbrain publish separate versioned worker contracts. LiNKplatform integrates them into the generic host and owns shared runner files; domain agents run their own conformance validation.
4. **OpenClaw gate:** Brain and Skills provide stable separate contracts, fakes, configuration fragments, and conformance suites. OpenClaw Prime owns implementation and may enable Brain before Skills.
5. **Codex gate:** both domains provide independently named configuration fragments. The shared integration owner applies only services that passed their own readiness gate; each domain validates its behavior.
6. **Production gate:** domain agents do not independently enable production credentials, apply live migrations, or modify Lisa's authoritative profile.
7. **Cursor maintenance gate:** prefer isolated/project-scoped configuration. Any unavoidable global mutation requires the stop, impact, maintenance-window, validation, and rollback procedure in Section 21.2.
8. **Verification gate:** no implementation or interface is complete solely because its Grok owner reported success. Repository Codex verification and, for shared interfaces, LiNKbrain Codex reconciliation are required.

### 29.5 Approved-plan and interface-change control

If an execution agent believes deviation is necessary, it must stop dependent work, record the reason and proposed change, identify all affected plans/repositories/interfaces/files, notify its repository Codex verifier and the LiNKbrain coordinating agent, and wait for the plan-level decision. A frozen interface changes only through a new version and a handoff to every affected consumer.

Every Grok execution handoff must include:

- approved phases/issues claimed complete;
- changed files and intentionally untouched ownership boundaries;
- commands, tests, evals, and validation results;
- migrations, configuration, credentials, deployments, and live actions performed, including who performed them;
- failures, deviations, blockers, residual risks, and omitted work;
- reproduction and rollback instructions;
- evidence locations suitable for independent Codex verification;
- cross-repository contracts produced/consumed, including versions and hashes.

### 29.6 Rollout-order compatibility

LiNKbrain rolls out Lisa first and Codex second. LiNKskills rolls out Cursor first, Codex second, and Lisa third. These orders do not conflict because the services have independent feature flags and readiness gates. OpenClaw may enable Brain before Skills. The shared Codex integration includes only services that have passed their own readiness gate.

## 30. Documentation deliverables

### LiNKskills

- updated Intent, Technical PRD, Operations Manual, README, OPEN-ISSUES;
- ADRs listed in Phase 0;
- Skill Pack/eval/tool schemas;
- MCP/API reference;
- data dictionary and release model;
- authoring, eval, Librarian, telemetry, incident, deployment, and rollback runbooks;
- Cursor/Codex integration guides;
- stage/production evidence and launch report.
- migration manifests, cross-plan interface handoffs, execution handoff, and independent Codex verification report.

### LiNKplatform

- institutional Librarian host/domain-worker architecture;
- LiNKskills worker integration and brain-only/skills-only modes;
- identity/credential/storage/migration/scheduler operations;
- live migration application receipts tied to the LiNKskills manifest/version/hash;
- scoped-role and smoke-test evidence;
- updated statement about eventual third LiNKlibraries workflow when approved.

### OpenClaw Prime

- plugin/MCP setup and compatibility;
- Lisa actor/profile rollout and rollback;
- lifecycle/buffering behavior;
- sanitized validation evidence;
- session/current-status/handoff records;
- explicit proof that Brain and Skills services, credentials, queues, telemetry, failure states, and rollback remain separate.

### LiNKbrain

No LiNKbrain domain implementation is required for LiNKskills launch. For this rollout, the LiNKbrain execution agent does own the coordinated shared Codex host configuration and the LiNKbrain Codex agent owns final four-plan reconciliation. Do not fold LiNKskills into the Brain Gateway or use that coordination role to merge domain services.

## 31. Definition of internal launch done

Internal launch is complete only when:

- source-of-truth documents reflect this architecture;
- Git source publishes immutable certified bundles to LiNKplatform;
- consumers do not require a LiNKskills Git checkout;
- the MCP/API service is authenticated, versioned, observable, and rollback-capable;
- Skill Pack v0.1, typed dependencies, tool descriptors, and progressive disclosure are implemented;
- eval suites are audited against the complete standard;
- real cases execute with exact tools and observed evidence;
- prompt-only scoring cannot certify;
- certification is bound to complete execution profiles;
- telemetry/feedback/trace-to-eval work without private-conversation capture;
- the Librarian can intake, improve, evaluate, propose releases, consolidate, deprecate, retire, and escalate under repository controls;
- Cursor passes first canary and multi-day use;
- Codex proves interoperability;
- Lisa/OpenClaw passes without losing native behavior;
- every one of the 34 current skills is deliberately classified, while normal delivery exposes only compatible `usable` profiles;
- at least one real failure/correction becomes a regression eval and one improved version completes the governed release loop;
- tool change blast radius and rollback are demonstrated;
- database/request/model cost per run is measured and accepted;
- security/privacy/supply-chain review has no unresolved launch blocker;
- stage and production rollback are demonstrated;
- every changed repository contains operations evidence and handoff documentation;
- LiNKskills uses canonical LiNKplatform actor IDs and has not created a competing identity authority;
- `lskills` migrations were authored/tested in LiNKskills and applied live only by the LiNKplatform owner from a reviewed manifest;
- the LiNKskills Librarian worker runs through the generic LiNKplatform host without coupling its schema, queue, telemetry, or failure state to the LiNKbrain worker;
- `skills_*` and `brain_*` services/tools, credentials, caches, queues, telemetry, retention, feature flags, and rollback remain separate;
- OpenClaw and shared Codex mutations were made only by their assigned owners and passed LiNKskills conformance;
- no raw LiNKbrain conversation/private-memory content appears in LiNKskills telemetry or storage;
- Cursor canary configuration did not disrupt the other three Grok sessions and any global mutation has maintenance-window/rollback evidence;
- the LiNKskills Grok implementation has a complete execution handoff and an independent LiNKskills Codex verification record classifying every planned item;
- the LiNKbrain Codex coordinating verifier has reconciled all four repository results with no unresolved launch-blocking contract, ownership, migration, configuration, privacy, or rollout contradiction.

## 32. Decisions already approved

The following are not open design questions during implementation:

1. LiNKskills and LiNKbrain remain separate products and MCP/API services.
2. LiNKskills and LiNKlibraries remain separate repositories.
3. Git is authoritative for editable source; LiNKplatform is authoritative for published operational state.
4. MCP is the primary internal actor interface over a protocol-independent core.
5. The first MCP release includes skill instructions and executable packaged tools.
6. Certification applies to the complete execution profile.
7. Evals must be fully defined and then actually executed.
8. Telemetry is structured and observable, not hidden reasoning.
9. One institutional Librarian has separate LiNKbrain, LiNKskills, and eventual LiNKlibraries workflows.
10. LiNKplatform owns the Librarian host; each domain owns its requirements and worker logic.
11. OpenClaw-specific changes are made by the OpenClaw Prime repo agent from LiNKskills contracts.
12. Cursor is first canary, Codex second, Lisa/OpenClaw third.
13. All internal usable skills are discoverable; progressive selection/disclosure remains explicit.
14. The Librarian may work autonomously but cannot bypass evals, repository integration, or Principal promotion boundaries.
15. The canary may use 5–10 representative skills; general launch requires deliberate classification of the whole current catalog.
16. LiNKplatform is the canonical actor identity/authentication/credential authority; LiNKskills stores only domain bindings referencing platform actor IDs.
17. LiNKskills authors/tests `lskills` migrations; LiNKplatform alone reviews, sequences, applies, and operates shared live migrations.
18. LiNKskills owns its versioned Librarian domain worker; LiNKplatform owns the generic host and existing shared runner integration files; LiNKbrain owns a separate worker.
19. OpenClaw Prime solely owns Lisa/OpenClaw implementation and live-profile mutation; LiNKskills supplies contracts, fragments, fakes, fixtures, and validation.
20. For this four-agent rollout, LiNKbrain is the default shared Codex host-configuration owner; LiNKskills supplies a separate Skills fragment/tests and validates afterward.
21. Cursor is both the execution environment and the first LiNKskills product canary, but only the latter is LiNKskills integration scope; global changes require a coordinated maintenance window.
22. Four Cursor/Grok agents execute in isolated repository worktrees/branches; four Codex agents verify independently; the LiNKbrain Codex agent reconciles the verified whole.
23. Execution agents implement approved plans and must use the stop-and-escalate process for deviations.
24. Grok completion reports are provisional until independent Codex verification.
25. Cross-service correlation uses references only; neither Brain nor Skills duplicates the other's private/domain evidence.

## 33. Implementation-time decisions intentionally deferred

These are engineering decisions to settle through ADR/work packets, not reasons to reopen product intent:

- exact package names and TypeScript/Python migration order;
- exact table and MCP operation names;
- stage/prod Gateway hosting target;
- object-storage bucket layout;
- exact batch size, timeout, and retention duration;
- search implementation and whether embeddings are required initially;
- individual eval thresholds and canary skill names;
- exact dashboard framework;
- whether packaged MCP tools register dynamically or use a generic invocation operation;
- the boundary between global and project-scoped Cursor canary configuration;
- exact user-level versus project-level placement of the shared Codex configuration, while LiNKbrain remains the assigned shared-file owner for this rollout;
- the smallest OpenClaw plugin hook set supported by the checked-out version.

The following are not deferred: canonical identity ownership, live migration ownership, generic Librarian host ownership, OpenClaw implementation ownership, default shared Codex configuration ownership, separate Brain/Skills services, or the independent verification roles.

Every deferred decision must preserve the approved boundaries and produce evidence.

## 34. Reference entry points

### LiNKskills

- `AGENTS.md`
- `README.md`
- `docs/LINKSKILLS-INTENT.md`
- `docs/LINKSKILLS-TECHNICAL-PRD.md`
- `docs/LINKSKILLS-OPERATIONS-MANUAL.md`
- `docs/OPEN-ISSUES.md`
- `docs/adr/0001-retire-logic-engine-governance-layer.md`
- `validator.py`
- `lib/skill_runtime/`
- `catalog/index.json`
- `skills/`
- `tools/`
- `supabase/migrations/`
- original manual: `/Users/linktrend/Library/CloudStorage/GoogleDrive-info@linktrend.media/My Drive/LiNKdrive/Manuals/LiNKskills/linkskills_manual.md`

### LiNKplatform

- `README.md`
- `docs/LINKPLATFORM-INTENT.md`
- `docs/LINKPLATFORM-TECHNICAL-PRD.md`
- `docs/OPEN-ISSUES.md`
- `agents/librarian.md`
- `packages/librarian-runner/`
- `packages/contracts/`
- shared foundation and identity migrations

### LiNKbrain

- `README.md`
- `docs/LINKBRAIN-INTENT.md`
- `docs/LINKBRAIN-TECHNICAL-PRD.md`
- `docs/LINKBRAIN-PHASE-1-DETAILED-IMPLEMENTATION-PLAN.md` (proposed/untracked at planning time; verify approval/current state)
- `supabase/migrations/`
- runtime and Principal-review packages

### OpenClaw Prime

- root and scoped `AGENTS.md` files;
- `docs/agent-briefing.md`;
- `docs/agent-coordination.md`;
- `docs/current-status.md`;
- active agent-session records and recent handoffs;
- `linkbots/lisa/docs/PHASE1-LINKBRAIN-LINKSKILLS.md` as historical input;
- current MCP config/CLI, plugin SDK, hook, skill, and agent-runtime source;
- sanitized live Lisa profile as runtime authority.

### Current product documentation to re-check at implementation time

- Cursor MCP: <https://docs.cursor.com/context/model-context-protocol>
- Cursor CLI/MCP: <https://docs.cursor.com/en/cli/reference/parameters>
- Cursor hooks: <https://cursor.com/blog/hooks-partners>
- Codex MCP: <https://learn.chatgpt.com/docs/extend/mcp>
- Codex configuration: <https://learn.chatgpt.com/docs/config-file/config-basic>
- Codex hooks: <https://learn.chatgpt.com/docs/hooks>
- Codex `AGENTS.md`: <https://learn.chatgpt.com/docs/agent-configuration/agents-md>

These product surfaces are version-sensitive. Record the exact installed versions and contracts tested before changing live configuration.
