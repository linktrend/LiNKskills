"""LiNKskills MCP adapter — JSON-RPC tools over SkillsGatewayService.

No duplicated business logic: every tool call routes to the shared gateway
service used by the HTTP API (in-process import of linkskills_gateway.service).

Authentication accepts only:
- Platform-verifiable ``Authorization`` bearers, or
- an explicitly injected test/canary ``default_actor`` (never caller-minted
  claims from the tool body).
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from typing import Any, Dict, List, Mapping, Optional, TextIO

from linkskills_gateway.auth import (
    ActorClaims,
    AuthError,
    PlatformClaimsVerifier,
)
from linkskills_gateway.service import (
    OPERATIONS,
    ServiceError,
    SkillsGatewayService,
)


PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "linkskills-mcp"
SERVER_VERSION = "0.1.0"


def _tool_schema(operation: str) -> Dict[str, Any]:
    return {
        "name": operation,
        "description": f"LiNKskills domain operation {operation}",
        "inputSchema": {
            "type": "object",
            "properties": {
                "params": {"type": "object"},
                "idempotency_key": {"type": "string"},
                "request_id": {"type": "string"},
            },
            "additionalProperties": True,
        },
    }


def resolve_canary_default_actor(
    *,
    environ: Optional[Mapping[str, str]] = None,
    verifier: Optional[PlatformClaimsVerifier] = None,
) -> Optional[ActorClaims]:
    """When LINKSKILLS_CANARY is set, require a Platform-verifiable injected bearer.

    Never mints identity from caller-supplied claims. The host must inject
    ``LINKSKILLS_CANARY_AUTHORIZATION`` or ``GATEWAY_TOKEN`` containing a
    Platform AuthClaims bearer that verifies under ``PlatformClaimsVerifier``.
    """
    env = environ if environ is not None else os.environ
    flag = str(env.get("LINKSKILLS_CANARY") or "").strip().lower()
    if flag not in {"1", "true", "yes"}:
        return None
    token = (
        str(env.get("LINKSKILLS_CANARY_AUTHORIZATION") or "").strip()
        or str(env.get("GATEWAY_TOKEN") or "").strip()
    )
    if not token:
        raise SystemExit(
            "LINKSKILLS_CANARY requires LINKSKILLS_CANARY_AUTHORIZATION or "
            "GATEWAY_TOKEN (Platform-verifiable bearer); refusing caller-minted identity"
        )
    auth = token if token.lower().startswith("bearer ") else f"Bearer {token}"
    return (verifier or PlatformClaimsVerifier()).verify(auth)


class SkillsMcpServer:
    """Minimal JSON-RPC MCP server facade for skills_* tools."""

    def __init__(
        self,
        service: Optional[SkillsGatewayService] = None,
        verifier: Optional[PlatformClaimsVerifier] = None,
        *,
        default_actor: Optional[ActorClaims] = None,
    ) -> None:
        self.service = service or SkillsGatewayService()
        self.verifier = verifier or PlatformClaimsVerifier()
        self.default_actor = default_actor
        self._initialized = False

    def list_tools(self) -> List[Dict[str, Any]]:
        return [_tool_schema(op) for op in OPERATIONS]

    def call_tool(
        self,
        name: str,
        arguments: Optional[Mapping[str, Any]] = None,
        *,
        authorization: Optional[str] = None,
    ) -> Dict[str, Any]:
        if name not in OPERATIONS:
            raise ServiceError("unknown_operation", f"Unknown tool: {name}", http_status=404)

        args = dict(arguments or {})
        if "params" in args and isinstance(args["params"], dict):
            params = dict(args["params"])
        else:
            params = {
                k: v
                for k, v in args.items()
                if k
                not in {
                    "params",
                    "idempotency_key",
                    "request_id",
                    "authorization",
                    "actor_claims",
                }
            }

        # Build verification payload including any spoof vectors (rejected).
        verify_payload: Dict[str, Any] = dict(args)

        actor = self._resolve_actor(
            authorization=authorization or args.get("authorization"),
            request_payload=verify_payload,
        )
        return self.service.dispatch(
            name,
            params,
            actor=actor,
            request_id=str(args.get("request_id") or uuid.uuid4()),
            idempotency_key=args.get("idempotency_key"),
        )

    def _resolve_actor(
        self,
        *,
        authorization: Optional[str],
        request_payload: Mapping[str, Any],
    ) -> ActorClaims:
        if authorization:
            return self.verifier.verify(
                authorization
                if authorization.lower().startswith("bearer ")
                else f"Bearer {authorization}",
                request_payload=request_payload,
            )
        if self.default_actor is not None:
            # Explicitly injected test/canary identity only — still reject spoof keys.
            self.verifier._reject_spoof(self.default_actor, request_payload)
            return self.default_actor
        # Caller-supplied actor_claims must never mint Platform identity.
        if isinstance(request_payload.get("actor_claims"), Mapping) or isinstance(
            request_payload.get("claims"), Mapping
        ):
            raise AuthError(
                "auth_claims_mint_forbidden",
                "Caller-supplied actor_claims cannot mint Platform identity; "
                "provide Authorization or use an injected default_actor",
            )
        raise AuthError(
            "auth_missing",
            "Authorization required (Platform-verifiable bearer)",
        )

    def handle_rpc(self, message: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle one JSON-RPC request; notifications return None."""
        method = message.get("method")
        req_id = message.get("id", None)
        params = message.get("params") or {}

        def result(payload: Any) -> Dict[str, Any]:
            return {"jsonrpc": "2.0", "id": req_id, "result": payload}

        def error(code: int, msg: str, data: Any = None) -> Dict[str, Any]:
            err: Dict[str, Any] = {"code": code, "message": msg}
            if data is not None:
                err["data"] = data
            return {"jsonrpc": "2.0", "id": req_id, "error": err}

        try:
            if method == "initialize":
                self._initialized = True
                return result(
                    {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": SERVER_NAME,
                            "version": SERVER_VERSION,
                        },
                    }
                )
            if method == "notifications/initialized":
                return None
            if method == "ping":
                return result({})
            if method == "tools/list":
                return result({"tools": self.list_tools()})
            if method == "tools/call":
                name = str(params.get("name") or "")
                arguments = params.get("arguments") or {}
                meta = params.get("_meta") or {}
                authorization = meta.get("authorization") or params.get("authorization")
                # Ignore meta/params actor_claims — never mint identity from them.
                envelope = self.call_tool(
                    name,
                    arguments if isinstance(arguments, Mapping) else {},
                    authorization=authorization,
                )
                return result(
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(envelope, sort_keys=True),
                            }
                        ],
                        "structuredContent": envelope,
                        "isError": envelope.get("error") is not None,
                    }
                )
            if req_id is None:
                return None
            return error(-32601, f"Method not found: {method}")
        except AuthError as exc:
            if req_id is None:
                return None
            return error(-32001, exc.message, {"code": exc.code})
        except ServiceError as exc:
            if req_id is None:
                return None
            return error(-32000, exc.message, {"code": exc.code})
        except Exception as exc:  # noqa: BLE001 — boundary
            if req_id is None:
                return None
            return error(-32603, f"Internal error: {exc}")

    def serve_stdio(
        self,
        stdin: Optional[TextIO] = None,
        stdout: Optional[TextIO] = None,
    ) -> None:
        """Newline-delimited JSON-RPC over stdio (test/dev convenience)."""
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
                        {
                            "jsonrpc": "2.0",
                            "id": None,
                            "error": {"code": -32700, "message": "Parse error"},
                        }
                    )
                    + "\n"
                )
                out.flush()
                continue
            response = self.handle_rpc(message)
            if response is not None:
                out.write(json.dumps(response, sort_keys=True) + "\n")
                out.flush()


def main() -> None:
    default_actor = resolve_canary_default_actor()
    SkillsMcpServer(default_actor=default_actor).serve_stdio()


if __name__ == "__main__":
    main()
