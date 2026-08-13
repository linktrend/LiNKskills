# LiNKskills provider v2 source-candidate handoff

## Candidate identity

This handoff applies only to the source candidate commit that contains this
file.  Source validation is evidence for repository behavior only; it is not
stage, consumer, deployment, or production evidence.

## Provider contract

- Canonical schemas and fixtures: `packages/contracts/schemas/`,
  `packages/contracts/fixtures/metadata/`, and
  `packages/contracts/docs/provider-v0.2-contract.md`.
- MCP boundary: `packages/mcp_server/linkskills_mcp/v2_provider.py` implements
  MCP `2026-07-28` as stateless/sessionless.  Every request requires a trusted
  verifier result bound to an organization, actor, audience, capability, and
  runtime binding.  Payload identity fields do not override that result.
- Supported v2 surface is the explicit `skills_*` resource and bounded-tool
  registry in that module: capability/catalogue discovery first, then exact
  release/summary/section/resource/package material.  It does not expose or
  alias `skills_run_*` or `skills_tool_*`; those fail closed.
- Exact packages use `packages/core/linkskills_core/release_v2.py` and
  `packages/publisher/linkskills_publisher/release_v2.py`.  A consumer pins
  the exact version and verifies inventory/package digests, lifecycle,
  qualification, dependency closure, and trusted ES256 attestation claims.
  There is no latest, similarly named, native, stale, or automatic substitute.
- `packages/librarian_domain/linkskills_librarian/telemetry_v2.py` accepts
  bounded reports only.  Completed uses require score 0--10; score 10 carries
  no diagnostic body, while 0--9 requires a typed issue.  Rejections retain
  only a reason, byte count, and digest; they do not retain raw report content.

## Authority and applicability

Skills supplies qualified reusable methods and provider facts only.  Consumers
select and execute locally; LiNKskills does not mutate consumer Ledgers,
Issues, Gates, Runs, legal matters, trading state, channels, or deployments.
Platform remains identity and authorization authority.  Controlled applicability
metadata is informational and covers domain/scope/locale/jurisdiction/channel,
sensitivity, allowed data/tool classes, human review, citation, expiry,
compatibility, and integrity.  The Skill Pack is authoritative; OKF v0.2 is
only an optional mapping for portable public knowledge/reference artifacts.

For future consumers, Legal rollout order is the policy input `TW`, `CR`,
`SG`, `US`, then `GB`; promotion remains outside Skills and shared legal
knowledge needs the external lawyer plus tenant-administrator approvals.
Trading execution/risk authority is categorically outside Skills.  Reach
channel metadata is extensible and grants no channel authority.

## Consumer conformance required before a live canary

An authorized consumer must prove: paginated catalogue discovery; external
selection; summary then selected section/resource retrieval; exact release and
digest verification; local execution; minimal telemetry and idempotent receipt.
For mandatory skills, unavailable, revoked, quarantined, incompatible,
tampered, unsupported, or stale/unknown-freshness material must stop the
dependent consumer action with no fallback.  Consumer configuration, Platform
claims/JWKS, release keys, migrations, hosted endpoint, queues, and live
canaries remain external HOLDs.

## Source validation and explicit HOLDs

Focused v2 MCP, release/attestation, and telemetry tests are in
`tests/mcp_server/test_v2_provider.py`, `tests/core/test_release_v2.py`,
`tests/publisher/test_release_v2.py`, and
`tests/librarian_domain/test_telemetry_v2.py`.  The repository-wide test suite
must be rerun against the exact candidate in a Python >=3.11 environment with
the declared dev dependencies.  The host Python 3.9 is not package-compatible;
the bundled Python 3.12 runtime is suitable when used with a disposable venv.

This document makes no claim that a stage endpoint exists, Platform identity
verification is live, a migration has been applied, a consumer is configured,
or a consumer/production canary has passed.
