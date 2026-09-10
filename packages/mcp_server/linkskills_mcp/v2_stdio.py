"""Stdio entrypoint for the production MCP ``skills.api.v0.2`` adapter."""

from __future__ import annotations

import json
import sys
from typing import Any, Mapping, Optional, TextIO

from linkskills_core.provider_v2 import V2Provider
from linkskills_gateway.auth import AuthConfigurationError, AuthError, resolve_claims_verifier
from linkskills_mcp.v2_provider import ModernSkillsMcpServer, TrustedIdentity


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
        )
    ):
        caps.add("skills.feedback")
        caps.add("skills.write")
    return TrustedIdentity(
        org_id=str(getattr(claims, "org_id", "") or ""),
        actor_id=str(getattr(claims, "actor_id", "") or ""),
        audience="lskills-api",
        capabilities=frozenset(caps),
        binding=str(getattr(claims, "credential_id", "") or getattr(claims, "actor_id", "") or "binding"),
        roles=frozenset(str(item) for item in (getattr(claims, "roles", None) or ())),
    )


def build_provider(verifier: Any | None = None, **kwargs: Any) -> Any:
    """Construct the shared domain bound to Platform-verified bearers.

    Production defaults load no releases. Exact retrieval then fails closed
    with ``catalog_unavailable`` until a real registry is supplied.
    """
    auth = verifier or resolve_claims_verifier()

    def _verify(token: str) -> TrustedIdentity:
        header = token if token.lower().startswith("bearer ") else f"Bearer {token}"
        claims = auth.verify(header, request_payload={}, required_operation="skills_list")
        return identity_from_claims(claims)

    kwargs.setdefault("releases", None)
    return V2Provider(_verify, **kwargs)


def serve_stdio(
    server: ModernSkillsMcpServer,
    stdin: Optional[TextIO] = None,
    stdout: Optional[TextIO] = None,
) -> None:
    """Newline-delimited JSON-RPC over stdio."""
    inn = stdin or sys.stdin
    out = stdout or sys.stdout
    for line in inn:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            out.write(
                json.dumps(
                    {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
                )
                + "\n"
            )
            out.flush()
            continue
        if not isinstance(message, Mapping):
            continue
        response = server.handle_rpc(message)
        if response is not None:
            out.write(json.dumps(response, sort_keys=True) + "\n")
            out.flush()


def main() -> None:
    try:
        provider = build_provider()
        serve_stdio(ModernSkillsMcpServer(provider))
    except AuthConfigurationError as exc:
        print(f"linkskills-mcp-v2 auth fail-closed: {exc.message}", file=sys.stderr)
        raise SystemExit(2) from exc
    except AuthError as exc:
        print(f"linkskills-mcp-v2 auth fail-closed: {exc.message}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
