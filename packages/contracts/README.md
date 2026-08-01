# LiNKskills Contracts (v0.1)

Versioned JSON Schema draft-2020-12 contracts for Skill Pack publication, eval
certification, telemetry, and MCP/API envelopes.

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
