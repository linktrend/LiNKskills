# Provider-only v0.2 contract foundation

This P0 slice is additive. It preserves the v0.1 schemas and records the
legacy surface; it does not change gateway, MCP, client, runtime, persistence,
publisher, evaluator, or consumer code.

## Legacy compatibility evidence

The machine-readable evidence is
[`fixtures/mcp/legacy-v0.1-compatibility.json`](../fixtures/mcp/legacy-v0.1-compatibility.json),
pinned to commit `66bc9c571424383ed336e2ef0656494f52976abf` and tree
`92655db825d6264f0cdecfa8f4084d1e2841cf6c`.

Verified from that baseline:

- HTTP operations use `POST /v1/{operation}`; liveness is `GET /health`.
  Evidence: `packages/gateway/linkskills_gateway/server.py:3-10,119-125,166-255`.
- The legacy operation set is the 15 names in
  `packages/gateway/linkskills_gateway/service.py:41-59`.
- The legacy MCP adapter is newline-delimited JSON-RPC over stdio, with
  `initialize`, `notifications/initialized`, `ping`, `tools/list`, and
  `tools/call`; it advertises the same 15 tools and no resources.
  Evidence: `packages/mcp_server/linkskills_mcp/server.py:38-56,105-123,200-304`.
- Production calls require a Platform-verifiable `Authorization: Bearer`
  token. An explicitly injected `default_actor` is test-only; caller-supplied
  claims cannot mint identity. Evidence:
  `packages/mcp_server/linkskills_mcp/server.py:6-12,167-198`.
- The package exposes `linkskills-mcp` and `linkskills-mcp-server` entrypoints,
  but its `pyproject.toml` has no Python MCP SDK dependency. Evidence:
  `packages/mcp_server/pyproject.toml:5-18`.

These facts are compatibility evidence, not a claim that v1 is production
ready or currently deployed.

## v0.2 policy

The v0.2 policy is transport-independent and deliberately does not implement a
new transport. It is stateless and sessionless, authenticates every request,
does not require or rely on `initialize` or a session, and has a closed tool
and resource map. Unsupported versions fail with `contract_incompatible`;
there is no silent downgrade to the v1 execution-era surface.

The provider exposes read-only guides, catalogue/release metadata, qualification,
entrypoint instructions, sections, and bounded resources as MCP **resources**.
Those resources are immutable-release URI templates and are deliberately not
tools: an actor can discover and load only the selected bounded material without
turning the provider into an executor or loading a full catalogue/pack. The
restricted v0.2 tool surface is `skills_release_verify`, use-report submit/status,
feedback submit/status, and optional Librarian status. It does not expose or alias
`skills_run_*` or `skills_tool_invoke` in v0.2. Legacy execution is a
separate capability (`skills.legacy_execute`), disabled by default and HTTP
410 by default when that separately governed capability is encountered.

## Metadata and legal-information boundary

`provider-metadata-v0.2.json` uses closed vocabularies and bounded opaque
references. `jurisdiction_or_venue` is generic applicability metadata; non-legal
skills use `UNSPECIFIED` rather than inheriting a legal rollout restriction.
Legal profiles carry exactly one qualified jurisdiction at a time. The legal
qualification order is:

1. Taiwan (`TW`)
2. Costa Rica (`CR`)
3. Singapore (`SG`)
4. United States (`US`)
5. United Kingdom (`GB`)

The order is policy metadata, not legal advice or a grant of authority. Legal
information remains informational and requires both matter-lawyer and
tenant-admin review (`required_human_gate:
matter_lawyer_and_tenant_admin_review`) where applicable. Reach metadata uses
generic `platform_class` / `channel_class` plus an opaque `channel_ref`, so
new channels do not require changing the authority model.

Skill Pack v0.1 is authoritative. OKF v0.2 is optional mapping only or
`not_applicable`; it never becomes a second source of truth.

## Telemetry boundary

Completed use requires integer score `0..10`. Score 10 retains exact skill
release, runtime, outcome, identity class, and opaque correlation references,
but has no issue/narrative fields. Scores 0..9 require a typed issue object
with no free-text narrative. Non-use is a separate `report_kind` with a
bounded `non_use_outcome` and no score/issue. A server-generated SHA-256
idempotency key is required; any client key is only an input to canonical
server derivation.

The contract rejects unbounded properties and forbidden secret/private-data
field names, including prompts, transcripts, credentials, consumer/case/lead
data, trading orders, portfolios, and raw input/output. Skills metadata is
informational: it cannot execute, select, grant identity/data access, approve,
escalate, or confer domain authority.

No MCP SDK is pinned. Official support for modern MCP `2026-07-28` was
verified in the [official Python SDK](https://github.com/modelcontextprotocol/python-sdk).
ED-02 implements the production HTTP and MCP adapters over the shared
`linkskills_core.provider_v2` domain (`POST /v2/{operation}`,
`linkskills-mcp-v2`). The Python MCP SDK remains unpinned.

## Production entrypoint (ED-02)

One installable domain (`SkillsApiV2` / `V2Provider`) is shared by:

- HTTP: `linkskills-gateway` serving `GET /health`, `GET /ready`,
  `GET /v2/openapi.json`, `GET /v2/capabilities`, `POST /v2/{operation}`
- MCP: `linkskills-mcp-v2` negotiating protocol `2026-07-28` sessionlessly

Business rules (gates, pagination snapshot, exact bytes/digests, privacy,
idempotency, legacy execution denial) live only in the core domain.

## Observed v0.1 compatibility adapter, removal gate, and rollback

The observed live compatibility adapter remains `POST /v1/{operation}` and
newline-delimited JSON-RPC MCP `2024-11-05` (`linkskills-mcp-server`) with the
15 legacy tools and no resources. Machine evidence:
`fixtures/mcp/legacy-v0.1-compatibility.json`.

On the v2 surface every `skills_run_*` and `skills_tool_*` name fails closed
with `legacy_execution_disabled` and HTTP 410. There is no provider execution
or tool-invoke route on v2.

Removal gate: drop the v0.1 adapter only after every admitted consumer uses
`skills.api.v0.2`, a rollback drill has restored the retained v0.1 image, and
no live v0.1 client remains. Until then v0.1 is preserved, observable, and
not a second long-term authority.

Rollback: drain the v2 candidate and restore the retained v0.1 image
`sha256:7cf2780a82c2c37c113b2d55b787a4e72a7098063cf434ea0654826c3719257f`
(release `7067716fef5189a1427a7cf9b0847cec898e19de`) and its compose
projection. Immutable releases are never rewritten. Live compose remains
Platform/Server 01 owned (ED-06/ED-08).
