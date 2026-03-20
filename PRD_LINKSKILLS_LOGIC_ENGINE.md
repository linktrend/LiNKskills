# Product Requirements Document
## LiNKskills Logic Engine

Version: 1.0
Status: Draft
Date: 2026-03-04
Owner: LiNKtrend / Venture Studio
Repository: LiNKskills Library

## 1. Executive Summary

LiNKskills Library currently exists as a standards-controlled registry of reusable AI skills and supporting tools for a Venture Studio. It is an active operating layer, not a passive prompt archive: it contains skill definitions, tool wrappers, validation logic, operating procedures, audit patterns, persistence conventions, and department-oriented bundles of capabilities. The original operating idea was to copy this library into separate OpenClaw instances so that different AI operators inside the Venture Studio could use the same high-standard skills while remaining specialized by department, such as Engineering & Delivery, Marketing, Finance, Operations, and Governance. The intended evolution described in this PRD is to convert LiNKskills from a repository-centric shared library into a centralized server product called the LiNKskills Logic Engine: a multi-tenant API and MCP-accessible service that exposes atomic skills and department packages to first-party OpenClaw instances, IDEs, chat interfaces, automations, SaaS products, and third-party customers. In the target model, clients do not receive the full source of a skill or package upfront. Instead, the system uses progressive disclosure and just-in-time delivery of a minimal public contract plus tightly scoped execution fragments. This allows clients to use LiNKskills capabilities while preserving central control over quality, policy, monetization, versioning, and sensitive logic.

## 2. Purpose of This Document

This PRD is intended to give a new reader, including someone who has never seen the current repository, a complete understanding of:

- what LiNKskills Library is today;
- why it was created;
- how it has been intended to be used so far;
- why the current copy-into-each-agent distribution model is no longer sufficient;
- what the new centralized server/API model is supposed to become;
- how progressive disclosure and limited source exposure should work;
- what core technical requirements must be satisfied;
- how the current repository can evolve into the new system in phases.

## 3. Background and Context

### 3.1 Original Vision

LiNKskills Library was created to act as a single source of truth for a Venture Studio's agent operating standards. Instead of independently crafting prompts, agent instructions, tools, and workflows inside every separate AI runtime, the library centralizes them into one governed codebase. This ensures that skills used across the studio share the same standards for:

- reliability;
- structure;
- validation;
- persistence;
- auditability;
- tooling;
- security;
- versioning;
- continuous improvement.

The original operational model was straightforward:

1. Maintain one central LiNKskills Library repository.
2. Organize the repository into reusable skills and tools.
3. Copy all or part of that library into one or more OpenClaw instances.
4. Enable only the skill bundles relevant to each OpenClaw's role.
5. Improve the library over time and push updated versions into those OpenClaw instances.

This meant one OpenClaw instance could function as a software development department, another as a marketing department, another as a finance or operations desk, while all of them inherited the same standards from the same library.

### 3.2 Why the Original Model Becomes Insufficient

The copy-into-each-instance approach eventually creates operational friction:

- distribution becomes manual or semi-manual;
- version drift appears between agent instances;
- quality control becomes harder to enforce centrally;
- token consumption and model policy become fragmented;
- secrets and tool access become harder to standardize;
- monetization to third parties becomes awkward;
- IP protection is weaker because full skill artifacts live on each client runtime;
- telemetry and evaluation are fragmented across separate environments.

As the number of internal OpenClaw instances grows, and especially if external customers are allowed access, the library should evolve from a distributable artifact into a centrally operated product.

## 4. Current State of the Repository

### 4.1 What the Repository Is Today

LiNKskills Library is currently a repository-based operating system for reusable AI capabilities. It contains:

- a `/skills` directory of structured skills;
- a `/tools` directory of reusable CLI-first tools and wrappers;
- a catalog of all targets grouped by department in `SKILLS_CATALOGUE.md`;
- a global `manifest.json` for registered capabilities and versions;
- validation logic in `validator.py` and `global_evaluator.py`;
- operating procedures in `SOP.md`, `SOP_HUMAN.md`, `SOP_MACHINE.md`, and `OPERATOR_BRIEFING.md`;
- shared conventions for safety, persistence, auditing, and deployment;
- Multi-Agent Sync scripts for governed branch/review/deploy workflows.

The repository is not just a document store. It is an operational framework for how AI skills should be designed, validated, and executed.

### 4.2 What a Skill Is in the Current System

In the current system, a skill is a reusable capability packaged with structure and discipline. A production-grade skill is not merely prompt text. It typically includes:

- a `SKILL.md` file with frontmatter and workflow rules;
- a Decision Tree for fail-fast execution;
- explicit scope-in and scope-out rules;
- tooling protocol guidance;
- persistence requirements using `.workdir/tasks/{{task_id}}/state.jsonl`;
- input, output, and state contracts in `references/schemas.json`;
- changelog and old-patterns references;
- optional scripts, advanced logic, examples, and task-local artifacts.

This means skills are governed operating assets, not ad hoc prompts.

### 4.3 What a Tool Is in the Current System

A tool is a reusable execution primitive that skills can rely on. Tools are typically implemented as CLI-first wrappers or adapters and are expected to provide deterministic or governed behavior. Examples include:

- `gws` for Google Workspace actions and `ltr` for non-Workspace Google + selected external actions;
- `memory` for scoped recall and notes;
- `vault` for secrets management;
- `sandbox` for isolated execution;
- `n8n` for workflow operations;
- `playwright-cli` and `fast-playwright` for automation.

The current system explicitly favors native CLI first, then local wrapper scripts, with direct API and MCP use only in controlled cases.

### 4.4 Department Bundles in the Current System

The current catalog groups skills and tools into department or function-oriented bundles, for example:

- Platform Core;
- Product Strategy & Discovery;
- Engineering & Delivery;
- Research & Intelligence;
- Growth & Marketing;
- Creative & Content;
- Finance & Revenue;
- Operations, Governance & Executive;
- Security & Compliance.

This department grouping matters because it foreshadows the future product packaging model. The Engineering & Delivery section, for example, effectively represents a software development department bundle. The intent has been that different OpenClaw instances or future clients would enable different bundles depending on role.

### 4.5 Core Meta-Skills in the Current Repository

The library includes meta-skills that shape and maintain the system itself.

#### `skill-template`
A Golden Template for production-grade skills. It defines the structural baseline, persistence conventions, decision-tree style, contracts, and progressive disclosure references that other skills should follow.

#### `skill-architect`
The meta-skill used to create new skills, reverse-engineer external skills into LiNKskills standards, and refine existing skills. It exists to make the library self-improving and structurally consistent.

#### `tool-architect`
The meta-skill used to design and standardize tools that the skills depend on. It ensures tools are wrapped, versioned, and aligned with the global registry conventions.

These meta-skills are important because the future server product must preserve them as the internal authoring and maintenance engine that continuously evolves the library.

### 4.6 Current Maturity Level

The repository is active and already contains a meaningful catalog of skills and tools, but it is still functionally in a pre-product platform phase. It is mature enough to demonstrate:

- structure;
- standards;
- departmental capability layout;
- meta-skill generation patterns;
- validation philosophy;
- core security and operating conventions.

However, it is not yet a centralized, multi-tenant service product. It is still principally a source library and internal operating layer.

## 5. Product Vision: LiNKskills Logic Engine

### 5.1 Product Definition

LiNKskills Logic Engine is the intended evolution of the current repository into a centralized, multi-tenant, API-first service that provides governed AI skills and department packages to multiple client environments without distributing the full internal source of the logic.

It should function as a Specialist Bureau for AI systems.

Any client runtime, including but not limited to:

- OpenClaw instances;
- IDE environments such as Cursor;
- chat interfaces;
- Telegram, WhatsApp, or Slack apps;
- backend SaaS systems;
- CLI tools;
- third-party businesses;

should be able to call a LiNKskills capability through a stable interface and receive an output that is aligned with LiNKskills standards.

### 5.2 Core Principle

The central principle is to separate:

- logic governance;
- quality standards;
- skill/package IP;
- orchestration policy;
- pricing and access policy;
- model routing policy;

from the raw client environment where the request originates.

### 5.3 High-Level Product Promise

The product promise is:

- clients can use high-standard specialist skills without receiving the entire source;
- the platform owner retains control over quality, policy, and monetization;
- internal OpenClaw instances can operate as specialized departments under one Venture Studio;
- external customers can consume atomic skills or full department packages;
- the system can support multiple privacy and cost models, including client-supplied LLM keys and client-supplied static context.

## 6. Problem Statement

The current library solves standardization of skills but does not yet solve centralized delivery, IP protection, or scalable multi-tenant access. The target product must solve the following problems:

- how to expose reusable specialist capabilities to many agents and clients without copying full skill source everywhere;
- how to keep skill logic centralized and version-controlled while supporting different client runtimes;
- how to support internal Venture Studio operators and external third parties from the same capability base;
- how to allow clients to use their own LLM keys or context when desired;
- how to avoid long-term retention of sensitive client data;
- how to preserve standards, safety, compliance, and output quality;
- how to turn bundles of internal capabilities into sellable API products.

## 7. Goals

### 7.1 Primary Goals

- Transform LiNKskills into a centralized logic service.
- Preserve the current standards-driven skill architecture.
- Expose atomic skills and department packages through API and MCP.
- Support internal and external multi-tenant consumption.
- Use progressive disclosure so clients never receive full skill/package source upfront.
- Support client-side execution tiers where appropriate.
- Allow optional client-supplied LLM credentials and static context.
- Maintain strong quality, auditability, and policy enforcement.
- Use Supabase for auth, database, and storage.
- Support hosting on DigitalOcean.

### 7.2 Secondary Goals

- Create a monetizable skill and package platform.
- Reduce version drift across internal agent instances.
- Create a path for distribution beyond OpenClaw to broader agent ecosystems.
- Keep the system compatible with future front-end interfaces and automation channels.

## 8. Non-Goals

The following are not primary goals of V1:

- exposing raw skill source code to all clients by default;
- building a public marketplace of ungoverned community-contributed skills;
- replacing every client agent runtime;
- becoming a general-purpose low-level LLM gateway without opinionated skill logic;
- supporting unrestricted arbitrary code execution for third parties;
- solving every possible department package in the first release.

## 9. User Types and Personas

### 9.1 Internal Venture Studio Operator

A first-party operator running one or more internal OpenClaw instances. This user needs access to department-specific bundles while staying aligned with central standards.

### 9.2 Internal Platform Owner

The owner or maintainer of LiNKskills who controls skill evolution, model policy, pricing, disclosure policy, compliance policy, and package definitions.

### 9.3 External Developer / Agency Integrator

A third party who wants to call atomic skills or packages from an IDE, internal tool, automation system, or SaaS backend.

### 9.4 SMB Customer

A customer who does not want to build or manage skill logic but wants access to a department capability such as finance, marketing, or content operations.

### 9.5 Enterprise Customer

A high-trust client that wants branded or SOP-aware package execution, optional use of their own LLM keys, and stronger privacy boundaries.

## 10. Product Interaction Models

The intended service should support six logical tiers.

### Tier 1: Single Command, Managed Model, Generic Context

- Client provides no LLM key.
- Client uses a generic version of the skill.
- LiNKskills manages the model execution policy and billing.
- Best for simple one-off use.

### Tier 2: Single Command, Client LLM Key, Generic Context

- Client provides their own LLM API credentials.
- LiNKskills still supplies the skill logic and execution wrapper.
- Best for cost-sensitive developers who want platform logic but not platform token billing.

### Tier 3: Single Command, Client LLM Key, Client Static Context

- Client provides their own LLM credentials.
- Client also provides static context, such as SOPs or brand guidelines.
- The skill operates against a client-customized but still governed contract.

### Tier 4: Package Access, Managed Model, Generic Context

- Client consumes a department package without their own API keys.
- LiNKskills orchestrates the bundle as a managed service.
- Best for SMBs that want turnkey capability.

### Tier 5: Package Access, Client LLM Key, Generic Context

- Client uses department bundles with their own model billing.
- LiNKskills still controls orchestration logic and package design.

### Tier 6: Package Access, Client LLM Key, Client Static Context

- Enterprise-grade model.
- Client supplies LLM credentials and proprietary context.
- LiNKskills provides the governed package architecture and progressive-disclosure logic.
- Best for bespoke departmental operations under client-specific rules.

## 11. Functional Model of Skills and Packages

### 11.1 Atomic Skill

An atomic skill is a discrete capability such as:

- market analysis;
- software PM decomposition;
- QA review;
- compliance review;
- revenue normalization;
- content strategy.

An atomic skill must have:

- a stable identifier;
- a public description;
- an input schema;
- an output schema;
- versioning;
- entitlement policy;
- disclosure policy;
- execution policy;
- telemetry policy.

### 11.2 Package / Department Bundle

A package is a governed orchestration of multiple atomic skills presented as one higher-level business function. For example:

- `engineering-dept`;
- `marketing-dept`;
- `finance-dept`;
- `content-dept`;
- `studio-ops-dept`.

A package is not simply a folder. It is a productized orchestration contract that specifies:

- the ordered or graph-based skill flow;
- state handoff rules between steps;
- required client inputs;
- approval gates;
- compliance checkpoints;
- error handling and retries;
- disclosure boundary rules;
- billing policy.

## 12. Progressive Disclosure and Just-in-Time Delivery

### 12.1 Why Progressive Disclosure Exists

The platform must balance two competing realities:

- clients need enough information and logic to execute or participate in execution;
- the platform owner must avoid disclosing the full reusable source of a valuable skill or package.

Progressive disclosure is the mechanism used to balance access, privacy, and IP protection.

### 12.2 Public Contract Layer

Every exposed skill or package should publish a thin public contract that can safely be disclosed. The public contract includes only what is necessary for discovery and integration, for example:

- skill or package identifier;
- plain-language description;
- input schema summary;
- output schema summary;
- authentication requirements;
- pricing tier;
- permission requirements;
- latency expectations;
- whether execution is managed, hybrid, or client-side.

The public contract must not include:

- the full internal prompt structure;
- the full orchestration graph;
- the full rule system;
- proprietary heuristics;
- hidden evaluation criteria;
- all package composition details.

### 12.3 Runtime Disclosure Layer

At runtime, the server discloses only the minimum additional material required for the exact run. This can include:

- a short-lived execution manifest;
- a subset of steps needed for the next stage only;
- signed tool schemas;
- constrained policy fragments;
- ephemeral context bindings;
- temporary credentials or capability tokens;
- a step-specific evaluation contract.

Each disclosed fragment should be:

- scoped to one tenant;
- scoped to one run;
- scoped to one capability;
- time limited;
- revocable where possible;
- non-transferable where possible;
- auditable.

### 12.4 Client-Side Execution in the Intended Model

The intended model described in this PRD includes client-side execution with limited disclosure for certain tiers. In this model, the central LiNKskills server acts primarily as:

- the control plane;
- entitlement authority;
- disclosure authority;
- package and skill registry;
- policy engine;
- billing and telemetry layer;
- quality and standards authority.

The client runtime executes the disclosed fragment locally or inside its own environment using the client's tools, credentials, or model provider, subject to the rules that the server provides just in time.

This means that the client may receive:

- a run-specific step manifest;
- a minimal reasoning or routing template;
- a constrained tool invocation contract;
- evaluation gates for the produced output.

The client does not automatically receive:

- the full skill package;
- the full reusable prompt tree;
- the full package DAG;
- the entire internal standards corpus;
- all anti-pattern memory or hidden heuristics.

### 12.5 Important Practical Limitation

If any logic is executed fully on the client side, perfect anti-theft guarantees are impossible. Any client-side executable artifact can eventually be inspected, captured, or reverse-engineered by a determined actor. Therefore, the product must be explicit that progressive disclosure does not create perfect IP protection. Instead, it should:

- reduce disclosure surface area;
- increase the cost of copying;
- preserve the highest-value orchestration logic centrally where necessary;
- use legal, contractual, and technical controls together.

### 12.6 Trust Models

The platform should support three execution trust modes.

#### Managed Execution
The server executes the skill or package and returns the output. Best for strong quality control and highest IP protection.

#### Hybrid Execution
The server keeps orchestration and sensitive policy central, but delegates limited tool or sub-step execution to the client.

#### Client-Side JIT Execution
The server discloses minimal run-scoped logic to the client, which executes locally and returns results or attestations. Best for privacy-sensitive or client-key workflows, but weakest for IP protection.

These trust modes should be selectable per tier, per skill, and per package.

## 13. Product Architecture

### 13.1 Architectural Overview

The target system should consist of the following logical components:

- Unified API Gateway
- Authentication and Tenant Control Layer
- Skill Registry Service
- Package Orchestrator
- Progressive Disclosure Service
- Policy Engine
- Metering and Billing Layer
- Static Context Vault
- Ephemeral Execution / Data Buffer
- Evaluation and Compliance Layer
- Front-End Control Panel
- MCP Adapter
- CLI / SDK Layer
- Internal Authoring Layer backed by the current repository

### 13.2 Unified API Gateway

A single entry point for all clients. Responsibilities:

- receive REST or MCP requests;
- authenticate caller;
- resolve tenant and entitlements;
- route request to the correct skill or package handler;
- attach disclosure and execution policy;
- emit consistent response envelopes.

### 13.3 Skill Registry Service

The registry service stores machine-readable definitions for all published skills. It should be derived from the current repository but served as a product catalog. It is responsible for:

- published skill metadata;
- versions;
- public contract data;
- disclosure policy;
- execution mode support;
- schema references;
- deprecation and compatibility policy.

### 13.4 Package Orchestrator

This service executes or coordinates packages that combine multiple skills into one business capability. It should support:

- DAG or step-chain orchestration;
- conditional branching;
- retries and compensating steps;
- approval gates;
- output validation;
- package state management;
- cross-skill telemetry.

### 13.5 Progressive Disclosure Service

This service is central to the new product. It should:

- issue public contracts for discovery;
- generate run-scoped manifests;
- decide what logic fragments can be disclosed to the caller;
- sign and time-limit those fragments;
- bind disclosure to tenant, capability, and run;
- log what was disclosed and why.

### 13.6 Policy Engine

The policy engine decides:

- which clients can access which skills/packages;
- whether managed, hybrid, or client-side execution is allowed;
- whether client-supplied keys are required or optional;
- how much of a workflow may be disclosed;
- what data can be retained;
- what telemetry is permitted;
- what compliance checks are mandatory.

### 13.7 Static Context Vault

A secure store for client-provided static context such as:

- SOPs;
- brand guidelines;
- policy documents;
- style guides;
- reusable organizational rules.

This context must be encrypted, tenant-scoped, versioned, and retrievable only for authorized execution contexts.

### 13.8 Ephemeral Data Buffer

Sensitive dynamic task data should be processed in an ephemeral, zero-retention or low-retention environment when policy requires. Responsibilities:

- handle transient evidence payloads;
- avoid durable storage by default;
- emit purge confirmations or receipts;
- separate transient run data from long-term static context.

### 13.9 Evaluation and Compliance Layer

A response should not be considered complete solely because a model returned text. The platform must provide:

- schema validation;
- quality gates;
- optional skill-specific evaluators;
- policy checks;
- compliance checks;
- audit logs;
- regression testing support.

### 13.10 Front-End Control Panel

A web interface is needed for:

- tenant onboarding;
- skill/package discovery;
- API key management;
- static context upload;
- billing and usage visibility;
- entitlement management;
- logs, runs, and audit traces;
- client-side execution receipts and purge reports.

## 14. Role of the Current Repository in the Future System

The current repository should remain the source authoring environment and control repository for the product's logic. It should not disappear. Instead, it becomes the upstream governed content and build source for the server.

### 14.1 The Repository as Authoring Layer

The repository remains responsible for:

- defining skills;
- defining tools;
- defining contracts;
- defining package composition source;
- maintaining standards;
- validation and quality checks;
- changelog and version discipline;
- evolving meta-skills.

### 14.2 The Server as Serving Layer

The server becomes responsible for:

- publication;
- tenancy;
- disclosure;
- execution routing;
- access control;
- billing;
- runtime telemetry;
- API and MCP exposure.

### 14.3 Meta-Skills in the New Architecture

#### `skill-architect`
In the future architecture, `skill-architect` remains the internal meta-skill for generating and refining the product catalog itself. It should be used to:

- create new atomic skills;
- convert legacy prompts or third-party workflows into platform-grade skills;
- upgrade contracts and execution rules;
- prepare publishable skill definitions for the server registry.

#### `tool-architect`
`tool-architect` remains the internal meta-skill for building the execution primitives that the skills depend on. In the future product it should be used to:

- wrap third-party services into governed tools;
- create client-side adapters and MCP adapters;
- create worker-compatible execution wrappers;
- formalize new tool contracts required by server-published skills.

Together, these meta-skills are internal production machinery for the LiNKskills product platform.

## 15. Functional Requirements

### 15.1 Skill Publishing

The system must allow skills from the repository to be published into a product registry with:

- unique IDs;
- semantic versions;
- lifecycle states such as draft, internal, beta, public, deprecated;
- public contract metadata;
- execution mode declarations;
- disclosure mode declarations.

### 15.2 Package Publishing

The system must allow packages to be published as composed capabilities with:

- package IDs;
- versioned dependency on underlying skill versions;
- package-level schemas and policies;
- package-level billing and entitlement configuration.

### 15.3 API Access

The system must expose versioned HTTP endpoints for:

- catalog discovery;
- skill invocation;
- package invocation;
- context upload and management;
- run status lookup;
- disclosure token issuance;
- evaluation and receipt retrieval;
- usage and billing visibility.

### 15.4 MCP Access

The system should expose selected capabilities through MCP for IDE and agent clients that prefer tool-like consumption over direct HTTP.

### 15.5 Client Credentials Modes

The system must support both:

- platform-managed model/provider credentials;
- client-supplied provider credentials.

### 15.6 Static Context Support

The system must allow a client to upload and manage static context artifacts for use by approved skills and packages.

### 15.7 Ephemeral Evidence Handling

The system must support transient task evidence that is processed without durable retention by default, unless a policy explicitly requires retention.

### 15.8 Usage Metering

The system must meter:

- requests;
- latency;
- token or model usage where available;
- package step counts;
- failures;
- retries;
- billable events.

### 15.9 Auditability

The system must log at least:

- caller identity;
- tenant identity;
- capability invoked;
- version;
- disclosure level;
- execution mode;
- timestamps;
- policy decisions;
- result status.

### 15.10 Front-End Administration

The system must provide a front-end UI for:

- tenants;
- plans;
- package assignment;
- keys and credentials;
- context management;
- run inspection;
- usage analytics;
- support and audit workflows.

## 16. Non-Functional Requirements

### 16.1 Security

- Tenant isolation is mandatory.
- Secrets must never be exposed to other tenants.
- Server-side service keys must remain server-only.
- Signed disclosures must expire quickly.
- Sensitive payloads should default to ephemeral handling.
- Package or skill source should not be fully downloadable by default.

### 16.2 Reliability

- API should be resilient to partial downstream failures.
- Package execution must support retries and resumability.
- Client-side execution flows must support re-issuance of short-lived manifests.

### 16.3 Performance

- Catalog and contract discovery should be low-latency.
- JIT disclosure generation should be fast enough to feel interactive.
- Long-running packages must support asynchronous run tracking.

### 16.4 Maintainability

- Published skills must remain traceable to source repository versions.
- Contracts must be machine-readable and testable.
- Deployment and publishing should be automated.

### 16.5 Observability

- All skill and package runs should emit structured telemetry.
- Errors must be traceable by tenant, capability, and version.
- Evaluation failures must be inspectable.

## 17. Technical Requirements

### 17.1 Data Platform

Supabase should be used for:

- Postgres database;
- authentication;
- row-level security;
- storage for static context and artifacts;
- optional edge functions where appropriate;
- real-time events where useful for dashboards or run updates.

### 17.2 Hosting

DigitalOcean should be used initially for the serving stack. Recommended baseline:

- one or more Droplets for API and orchestration services;
- containerized deployment for service isolation;
- managed PostgreSQL is unnecessary if Supabase remains primary DB;
- object storage may remain in Supabase Storage unless separate blob economics justify change;
- a front-end can be hosted either on DigitalOcean App Platform or on a separate static hosting layer.

Recommended deployment split:

- back-end API/orchestrator on DO compute;
- front-end web app on DO App Platform or similar static/CDN hosting;
- Supabase for auth, database, and storage.

For MVP, a single Droplet can host the API, workers, reverse proxy, and background jobs, but the architecture should assume later separation.

### 17.3 API Surface

At minimum, the product should support endpoints resembling:

- `GET /v1/catalog/skills`
- `GET /v1/catalog/packages`
- `GET /v1/skills/{skill_id}`
- `POST /v1/skills/{skill_id}/run`
- `POST /v1/packages/{package_id}/run`
- `POST /v1/context/static`
- `GET /v1/runs/{run_id}`
- `POST /v1/disclosures/issue`
- `GET /v1/receipts/{receipt_id}`

Exact endpoint design may evolve, but the concepts are required.

### 17.4 Disclosure Tokens

The platform must support short-lived signed tokens that encode:

- tenant;
- capability;
- run ID;
- step or manifest scope;
- expiry;
- client execution mode;
- allowed tools or functions.

### 17.5 Package State Model

Packages must support persisted orchestration state such as:

- initialized;
- awaiting disclosure;
- in progress;
- awaiting approval;
- evaluation failed;
- completed;
- purged.

### 17.6 Machine-Readable Contracts

Existing skill schemas should evolve into publishable machine-readable contracts for:

- discovery;
- validation;
- orchestration;
- client-side runtime generation;
- SDK generation in the future.

### 17.7 SDK / Client Adapters

The system should eventually provide:

- JavaScript/TypeScript SDK;
- Python SDK;
- CLI wrapper;
- MCP adapter;
- OpenClaw-compatible adapter.

## 18. Security and Privacy Requirements

### 18.1 Tenant Isolation

Every run, stored context, usage record, and disclosure event must be scoped to a tenant and enforced through database policy plus server-side authorization.

### 18.2 Secret Handling

- Platform secrets remain server-side only.
- Client-supplied LLM keys should be encrypted at rest or accepted as per-run ephemeral credentials depending on policy.
- No secret should be embedded into disclosed skill fragments unless absolutely necessary and scoped to a specific run.

### 18.3 Static Context Protection

Client static context must be:

- encrypted at rest;
- tenant-isolated;
- versioned;
- access-controlled;
- auditable.

### 18.4 Zero-Retention / Low-Retention Task Data

The system should default transient evidence payloads to low-retention or zero-retention handling. If retention is disabled, the system should emit a receipt that confirms:

- the payload was processed;
- no durable content was retained;
- only metadata or hashes were logged if required.

### 18.5 Source Protection

The platform must not expose full internal skill/package source by default. Any disclosed fragment should be:

- scoped;
- signed;
- time limited;
- logged;
- minimized.

## 19. Quality Requirements

### 19.1 Skill Quality

Every published skill must preserve LiNKskills standards for:

- explicit workflow structure;
- contracts;
- versioning;
- scope boundaries;
- operating rules;
- validation.

### 19.2 Package Quality

Every package must define:

- package purpose;
- included skills;
- sequence or graph logic;
- gating behavior;
- failure recovery;
- evaluation criteria.

### 19.3 Output Quality

Outputs should be schema-validated and optionally scored or checked by evaluators before being considered complete for managed or hybrid modes.

## 20. Front-End Requirements

The front-end should allow a new user to understand and operate the product without needing repository access. It should include:

- marketing or landing pages explaining skills and packages;
- authenticated dashboard;
- skill/package catalog browser;
- pricing and plan visibility;
- API key management;
- tenant and workspace settings;
- static context upload and lifecycle controls;
- usage analytics;
- run history and receipts;
- package configuration and entitlement screens.

## 21. Migration Strategy from Current Repository

### 21.1 Phase 0: Documentation and Normalization

- Finalize the product model described in this PRD.
- Normalize terminology between current library concepts and future product concepts.
- Identify which current skills are V1 candidates for publication.

### 21.2 Phase 1: Registry Extraction

- Create a publishable metadata layer from current skills and tools.
- Add missing machine-readable public contract fields.
- Define publish states and visibility classes.

### 21.3 Phase 2: API and Auth Foundation

- Stand up the unified API gateway.
- Implement tenant model and authentication.
- Connect Supabase auth, database, and storage.
- Create first catalog and run endpoints.

### 21.4 Phase 3: Progressive Disclosure Runtime

- Implement disclosure token issuance.
- Implement run-scoped manifest generation.
- Implement policy-based fragment disclosure.
- Create client-side execution receipts.

### 21.5 Phase 4: First Published Atomic Skills

Select a small number of representative skills, for example:

- `market-analyst`
- `persistent-qa`
- `lead-engineer`
- `marketing-strategist`

Publish them with:

- public contracts;
- execution mode support;
- evaluation policy;
- metering.

### 21.6 Phase 5: First Department Package

Create one high-value package as a reference implementation, such as:

- `finance-dept`; or
- `engineering-dept`.

This package should demonstrate orchestration, disclosure policy, billing, and run-tracking end to end.

### 21.7 Phase 6: Client Adapters

- Build OpenClaw connector or skill wrapper.
- Build MCP adapter.
- Build CLI wrapper.
- Build basic SDK.

### 21.8 Phase 7: External Beta

- Onboard a small number of trusted third parties.
- Test pricing, disclosure policy, telemetry, and support workflows.
- Tune package boundaries and quality gates.

## 22. Risks and Constraints

### 22.1 IP Leakage Risk

Any client-side execution path increases the possibility of inspection or reverse engineering. This is an acceptable but managed risk, not something that can be eliminated entirely.

### 22.2 Orchestration Complexity

Department bundles can become complex quickly. Package design must remain strict or the product will become hard to debug and maintain.

### 22.3 Quality Drift

If client-side execution becomes too permissive, output quality may drift from LiNKskills standards. Strong evaluation contracts and policy gates are required.

### 22.4 Tool Compatibility

Some current tools are strongly repository- or environment-dependent. They may need new wrappers, remote modes, or client-side adapters to function in the product model.

### 22.5 Billing and Token Attribution

Supporting both managed and client-supplied keys increases complexity in accounting, observability, and support.

## 23. Success Criteria

The product should be considered successful when:

- internal OpenClaw instances no longer require full library copies to consume core capabilities;
- at least one atomic skill and one package can be consumed through API;
- progressive disclosure works end to end for at least one client-side execution flow;
- internal quality standards remain enforceable from the central source repository;
- tenant isolation and context security are demonstrably in place;
- the system can support both internal use and external paid access.

## 24. Open Questions

The following questions remain product decisions rather than blockers for the PRD:

- Which skills should be first to publish publicly versus internal-only?
- Which capabilities should allow client-side execution versus managed-only?
- What exact commercial packaging should exist for SMB versus enterprise?
- How much disclosure is acceptable for each trust tier?
- Which current tools need remote-server wrappers versus client-side adapters?
- What retention window is acceptable for operational metadata and audit logs?

## 25. Conclusion

LiNKskills Library today is a structured, governed, department-oriented repository of AI skills and tools designed to standardize how intelligent work is performed across a Venture Studio. Its next intended evolution is not to abandon that repository, but to elevate it into a centralized product platform: the LiNKskills Logic Engine. In that future architecture, the repository remains the authoring and standards source of truth, while a multi-tenant server layer exposes atomic skills and department packages through API and MCP interfaces to internal agents, IDEs, apps, and external customers. The defining characteristic of the target system is progressive disclosure: clients can discover and use capabilities through thin contracts and just-in-time run-scoped logic fragments, rather than receiving the full source of the skills upfront. This preserves central control, enables monetization, supports multiple execution and privacy tiers, and creates a path for LiNKskills to operate not only as a library for one environment, but as a productized intelligence service for many environments.
