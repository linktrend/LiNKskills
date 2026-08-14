# LiNKskills Contracts (v0.1 and additive v0.2)

Versioned JSON Schema draft-2020-12 contracts for Skill Pack publication, eval
certification, telemetry, and MCP/API envelopes. v0.2 adds provider-only
metadata, stateless/sessionless MCP policy, compatibility evidence, and bounded
use telemetry without changing v0.1 files or transport behavior.

## Schema versions

All launch schemas are **v0.1** (`schema_version: "0.1"`). Filenames use the
`-v0.1.json` suffix under `schemas/`.

| Schema | File | Purpose |
|---|---|---|
| Skill Pack | `skill-pack-v0.1.json` | Published skill metadata, routing, execution, typed dependencies, eval/telemetry refs |
| Skill Fragment | `skill-fragment-v0.1.json` | Progressive-disclosure fragment (levels 0–6) |
| Dependency Types | `dependency-types-v0.1.json` | Typed dependency buckets (replaces untyped `dependencies[]`) |
| Tool Descriptor | `tool-descriptor-v0.1.json` | Packaged tool registry descriptor with exact-hash fields |
| Runtime Profile | `runtime-profile-v0.1.json` | Bounded actor runtime capability profile |
| Execution Profile | `execution-profile-v0.1.json` | Certification unit: pack + suite + toolchain + adapter + runtime |
| Eval Suite | `eval-suite-v0.1.json` | Certification-ready eval definition (executed evidence required) |
| Run Event | `run-event-v0.1.json` | Telemetry event spine envelope |
| Feedback | `feedback-v0.1.json` | Actor feedback / trace-to-eval candidate |
| Release Record | `release-record-v0.1.json` | Immutable published release metadata |
| Error Envelope | `error-envelope-v0.1.json` | Safe structured error response |
| MCP/API Envelope | `mcp-api-envelope-v0.1.json` | Common success envelope for `skills_*` MCP/HTTP |

## Additive v0.2 contracts

| Schema | File | Purpose |
|---|---|---|
| Provider metadata | `provider-metadata-v0.2.json` | Bounded vocabularies, opaque scope refs, jurisdiction order inputs, informational authority, and Skill Pack/OKF compatibility |
| MCP policy | `mcp-policy-v0.2.json` | Frozen transport-independent stateless/sessionless policy, per-request auth, tools/resources, typed errors, and no dual-era downgrade |
| Use report | `use-report-v0.2.json` | Completed-use score/typed-issue variants and separate non-use outcomes with server-canonical idempotency |
| Compatibility evidence | `compatibility-evidence-v0.2.json` | Baseline-pinned v1 HTTP/MCP endpoint, transport, tools/resources, auth, and SDK-pin evidence |

The implementation and evidence boundary is documented in
[`docs/provider-v0.2-contract.md`](docs/provider-v0.2-contract.md). No Python
MCP SDK is pinned in P0; modern-MCP support has been officially verified, while
transport implementation remains a later, separately tested slice.

## Fixtures

`fixtures/` contains valid and intentionally invalid examples used by unit tests:

- `fixtures/skill-pack/valid-minimal.json`
- `fixtures/skill-pack/invalid-missing-telemetry.json`
- `fixtures/eval-suite/valid-minimal.json`
- `fixtures/eval-suite/invalid-empty-cases.json`

## Python validator

`linkskills_contracts` provides a stdlib-friendly loader and lightweight
required/type validator. It intentionally does **not** require the `jsonschema`
package.

```python
from linkskills_contracts import validate_instance, load_schema

result = validate_instance(payload, "skill-pack")
assert result.ok
```

Compatibility fixtures and schema files are the source of truth for Phase 1–2
behavior before service/database expansion.
