"""HTTP adapter for production ``skills.api.v0.2``.

The Gateway process remains the installable HTTP entrypoint. ``POST /v2/{operation}``
calls the same domain as MCP. Legacy ``POST /v1/{operation}`` is the observed
v0.1 compatibility adapter and is not a second long-term authority.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Mapping, Optional

from linkskills_core.provider_v2 import (
    CONTRACT_VERSION,
    DENIED_ON_V2,
    MCP_SERVER_INFO,
    PROTOCOL_VERSION,
    PUBLIC_TYPED_ERRORS,
    RESOURCE_OPERATIONS,
    TOOLS,
    SkillsApiV2,
    TrustedIdentity,
    V2Provider,
    bind_trusted_request,
)

LEGACY_REMOVAL_GATE = {
    "legacy_adapter": "POST /v1/{operation} plus newline JSON-RPC MCP 2024-11-05",
    "legacy_execution_on_v2": "legacy_execution_disabled",
    "removal_criterion": (
        "Remove the v0.1 adapter only after every admitted consumer uses "
        "skills.api.v0.2, Server 01 has rolled back or drained the v0.1 "
        "image at least once, and no live v0.1 client remains."
    ),
    "rollback": (
        "Drain the v2 candidate and restore the retained v0.1 image/compose "
        "projection. Immutable releases are never rewritten."
    ),
    "retained_v0_1_image": "sha256:7cf2780a82c2c37c113b2d55b787a4e72a7098063cf434ea0654826c3719257f",
    "retained_v0_1_release": "7067716fef5189a1427a7cf9b0847cec898e19de",
}


def identity_from_claims(claims: Any) -> TrustedIdentity:
    """Map Gateway ActorClaims onto the v2 trusted identity record."""
    caps = {"skills.read"}
    scopes = set(getattr(claims, "scopes", ()) or ())
    permitted = set(getattr(claims, "permitted_operations", ()) or ())
    tokens = scopes | permitted
    if any(
        token in tokens
        for token in (
            "skills:write",
            "skills:feedback",
            "skills.write",
            "skills.feedback",
            "execute",
            "skills:run",
        )
    ):
        caps.add("skills.feedback")
        caps.add("skills.write")
    return TrustedIdentity(
        org_id=str(getattr(claims, "org_id", "") or ""),
        actor_id=str(getattr(claims, "actor_id", "") or ""),
        audience="lskills-api",
        capabilities=frozenset(caps),
        binding=str(
            getattr(claims, "credential_id", "") or getattr(claims, "actor_id", "") or "binding"
        ),
        roles=frozenset(str(item) for item in (getattr(claims, "roles", None) or ())),
    )


def encode_v2_result(result: Mapping[str, Any]) -> dict[str, Any]:
    """JSON-safe v2 envelope; exact bytes travel as base64 plus digest."""
    out = dict(result)
    body = out.pop("bytes", None)
    if isinstance(body, bytes):
        out["content_b64"] = base64.b64encode(body).decode("ascii")
        out["byte_size"] = len(body)
        out.setdefault("content_digest", "sha256:" + __import__("hashlib").sha256(body).hexdigest())
    out.setdefault("contract_version", CONTRACT_VERSION)
    out.setdefault("protocol_version", PROTOCOL_VERSION)
    return out


def provider_from_verifier(verifier: Any, **kwargs: Any) -> SkillsApiV2:
    """Bind a Gateway claims verifier to the shared v2 domain.

    Production defaults load no releases. Exact retrieval then fails closed
    with ``catalog_unavailable`` until a real registry is supplied.
    """

    def _verify(token: str) -> TrustedIdentity:
        header = token if token.lower().startswith("bearer ") else f"Bearer {token}"
        claims = verifier.verify(
            header,
            request_payload={},
            required_operation="skills_list",
        )
        return identity_from_claims(claims)

    kwargs.setdefault("releases", None)
    return V2Provider(_verify, **kwargs)


def load_openapi() -> dict[str, Any]:
    """Load the authoritative OpenAPI record from the contracts package when present."""
    candidates = [
        Path(__file__).resolve().parents[2] / "contracts" / "fixtures" / "openapi" / "skills-api-v0.2.json",
        Path(__file__).resolve().parents[3] / "packages" / "contracts" / "fixtures" / "openapi" / "skills-api-v0.2.json",
    ]
    for path in candidates:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    return {
        "openapi": "3.1.0",
        "info": {"title": "LiNKskills skills.api.v0.2", "version": CONTRACT_VERSION},
        "paths": {
            "/health": {"get": {"summary": "Liveness"}},
            "/ready": {"get": {"summary": "Readiness; never proves consumer execution"}},
            "/v2/capabilities": {"get": {"summary": "HTTP/MCP capability record"}},
            "/v2/mcp-capabilities": {"get": {"summary": "Same capability record as /v2/capabilities"}},
            "/v2/{operation}": {"post": {"summary": "skills.api.v0.2 operations"}},
        },
    }


def capability_record(provider: SkillsApiV2) -> dict[str, Any]:
    """Machine-readable MCP/HTTP capability advertisement."""
    resources = [item["name"] for item in provider.resources()]
    tools = list(provider.tools())
    return {
        "contract_version": CONTRACT_VERSION,
        "mcp_protocol": PROTOCOL_VERSION,
        "sessionless": True,
        "initialize_required": False,
        "initialize_protocol_version": PROTOCOL_VERSION,
        "legacy_execution": False,
        "serverInfo": dict(MCP_SERVER_INFO),
        "resources": resources,
        "tools": tools,
        "denied_on_v2": list(DENIED_ON_V2),
        "uri_templates": {
            item["name"]: item["uri_templates"] for item in provider.resources()
        },
        "typed_errors": list(PUBLIC_TYPED_ERRORS),
        "compatibility": LEGACY_REMOVAL_GATE,
        "operations": list(RESOURCE_OPERATIONS + TOOLS),
        "catalog_ready": bool(provider.catalog_ready),
    }
