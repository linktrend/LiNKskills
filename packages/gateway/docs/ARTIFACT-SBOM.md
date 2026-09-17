# Artifact and SBOM description (provider-v2)

## Artifact identity

| Piece | Installable name | Role |
|---|---|---|
| Domain | `linkskills-core` (`SkillsApiV2`) | Transport-independent v2 rules |
| HTTP adapter | `linkskills-gateway` (`linkskills-gateway`) | `/health`, `/ready`, `/v2`, legacy `/v1` |
| MCP adapter | `linkskills-mcp` (`linkskills-mcp-v2`) | MCP `2026-07-28` |
| Client fixtures | `linkskills-client` | Exact-byte MCP/HTTP clients |

OpenAPI: `packages/contracts/fixtures/openapi/skills-api-v0.2.json`.
MCP capability: `packages/contracts/fixtures/mcp/v0.2-capabilities.json`.

## SBOM

Generate a source SBOM from the hash-locked lockfile and local package
metadata without publishing:

```bash
python3 - <<'PY'
import hashlib, json
from pathlib import Path
lock = Path("requirements-dev.lock").read_bytes()
print("requirements-dev.lock sha256", hashlib.sha256(lock).hexdigest())
PY
```

If `syft` or `cyclonedx-py` is present, run it against the installed venv
and retain the file locally. Do not upload the SBOM or an image from ED-02.
Hosted image build remains ED-06; this packet records a HOLD when Docker is
unavailable in the worker VM.

## What this packet does not ship

- Live registry push
- Server 01 compose change
- Production SecretRef values
