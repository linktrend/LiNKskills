"""Standard MCP v2 adapter over the transport-independent domain.

Business rules live in ``linkskills_core.provider_v2``. This module owns
JSON-RPC, URI mapping, and stdio/HTTP-neutral RPC dispatch.
"""

from __future__ import annotations

import base64
from typing import Any, Mapping
from urllib.parse import parse_qs, urlparse

from linkskills_core.provider_v2 import (
    CATALOG_OPERATIONS,
    CONTRACT_VERSION,
    MCP_SERVER_INFO,
    PROTOCOL_VERSION,
    RESOURCE_OPERATIONS,
    RESOURCE_READ_PARAM_KEYS,
    TOOLS,
    InMemoryProviderStore,
    SkillsApiV2,
    TrustedIdentity,
    V2Provider,
    bind_trusted_request,
    operation_from_resource_uri,
    strip_untrusted_identity,
)

__all__ = [
    "CATALOG_OPERATIONS",
    "CONTRACT_VERSION",
    "ModernSkillsMcpServer",
    "PROTOCOL_VERSION",
    "RESOURCE_OPERATIONS",
    "TOOLS",
    "TrustedIdentity",
    "V2Provider",
    "InMemoryProviderStore",
    "SkillsApiV2",
]


class ModernSkillsMcpServer:
    """JSON-RPC MCP facade with initialize negotiation and stateless requests."""

    protocol_version = PROTOCOL_VERSION

    def __init__(self, provider: SkillsApiV2) -> None:
        self.provider = provider
        self._initialized = False

    @staticmethod
    def _authorization(params: Mapping[str, Any]) -> Any:
        """Extract transport ``_meta`` authorization only; never caller claims."""
        meta = params.get("_meta")
        if not isinstance(meta, Mapping):
            return None
        return meta.get("authorization")

    def handle_rpc(self, message: Mapping[str, Any]) -> dict[str, Any] | None:
        """Handle one JSON-RPC request or return ``None`` for notifications."""
        req_id = message.get("id")
        method, raw_params = message.get("method"), message.get("params") or {}
        params = raw_params if isinstance(raw_params, Mapping) else {}
        if method == "initialize":
            requested = params.get("protocolVersion")
            authorization = self._authorization(params)
            if any(key in params for key in ("session", "session_id")):
                return self._error(req_id, "contract_incompatible")
            if requested != self.protocol_version:
                return self._result(req_id, {"ok": False, "error": "contract_incompatible"})
            if authorization is not None:
                auth = self.provider.handle(
                    {
                        "protocol_version": self.protocol_version,
                        "authorization": authorization,
                        "operation": "skills_capabilities_get",
                    }
                )
                if not auth["ok"]:
                    return self._result(req_id, auth)
            self._initialized = True
            return self._result(
                req_id,
                {
                    "protocolVersion": self.protocol_version,
                    "capabilities": {
                        "resources": {"listChanged": False, "subscribe": False},
                        "tools": {},
                    },
                    "serverInfo": dict(MCP_SERVER_INFO),
                },
            )
        if method == "notifications/initialized":
            self._initialized = True
            return None
        if method == "ping":
            return self._result(req_id, {})
        if method == "resources/list":
            auth = self.provider.handle(
                {
                    "protocol_version": self.protocol_version,
                    "authorization": self._authorization(params),
                    "operation": "skills_capabilities_get",
                }
            )
            return self._result(req_id, {"resources": list(self.provider.resources())} if auth["ok"] else auth)
        if method == "tools/list":
            auth = self.provider.handle(
                {
                    "protocol_version": self.protocol_version,
                    "authorization": self._authorization(params),
                    "operation": "skills_capabilities_get",
                }
            )
            return self._result(req_id, {"tools": list(self.provider.tools())} if auth["ok"] else auth)
        if method == "resources/read":
            uri = params.get("uri")
            operation = operation_from_resource_uri(uri)
            if operation is None:
                return self._result(
                    req_id,
                    {
                        "contents": [],
                        "structuredContent": {"ok": False, "error": "unsupported_operation"},
                        "isError": True,
                    },
                )
            extras = {
                key: params[key]
                for key in RESOURCE_READ_PARAM_KEYS
                if key in params and key != "uri"
            }
            request = bind_trusted_request(
                {**self._params_from_uri(uri), **extras},
                operation=operation,
                authorization=self._authorization(params),
                protocol_version=self.protocol_version,
            )
            response = self.provider.handle(request)
            if not response["ok"]:
                return self._result(req_id, {"contents": [], "structuredContent": response, "isError": True})
            body = response.pop("bytes", None)
            contents = []
            if isinstance(body, bytes):
                contents.append(
                    {
                        "uri": response.get("resource_uri", request.get("uri", "")),
                        "mimeType": (response.get("descriptor") or {}).get(
                            "media_type", "application/octet-stream"
                        ),
                        "blob": base64.b64encode(body).decode("ascii"),
                    }
                )
            return self._result(req_id, {"contents": contents, "structuredContent": response})
        if method == "tools/call":
            arguments = params.get("arguments") if isinstance(params.get("arguments"), Mapping) else {}
            cleaned = strip_untrusted_identity(arguments)
            request = bind_trusted_request(
                cleaned,
                operation=str(params.get("name") or ""),
                authorization=self._authorization(params),
                protocol_version=self.protocol_version,
            )
            response = self.provider.handle(request)
            return self._result(req_id, {"structuredContent": response, "isError": not response["ok"]})
        return self._error(req_id, "unsupported_operation")

    @staticmethod
    def _operation_from_uri(uri: Any) -> str | None:
        """Map standard resource URIs using the server-owned template table."""
        return operation_from_resource_uri(uri)

    @classmethod
    def _params_from_uri(cls, uri: Any) -> dict[str, Any]:
        """Extract exact resource identifiers from a standard Skills URI."""
        if not isinstance(uri, str) or not uri.startswith("skills://"):
            return {}
        parsed = urlparse(uri)
        parts = [part for part in (parsed.netloc, *parsed.path.split("/")) if part]
        values: dict[str, Any] = {"uri": uri}
        if parts and parts[0] == "guide" and len(parts) >= 3 and parts[1] == "domains":
            values["domain"] = parts[2]
        if len(parts) >= 2 and parts[0] == "release":
            if len(parts) == 2:
                values["skill_id"] = parts[1]
            elif len(parts) >= 3:
                values.update({"skill_id": parts[1], "version": parts[2]})
            if len(parts) >= 5:
                values[
                    {
                        "resource": "resource_id",
                        "content": "content_id",
                        "section": "section_id",
                        "fragment": "fragment_id",
                    }.get(parts[3], "resource_id")
                ] = parts[4]
            if len(parts) >= 4 and parts[3] == "manifest":
                values["manifest"] = True
        query = parse_qs(parsed.query)
        for key in ("cursor", "limit", "query"):
            if key in query:
                values[key] = query[key][0]
        if isinstance(values.get("limit"), str) and values["limit"].isdigit():
            values["limit"] = int(values["limit"])
        return values

    @staticmethod
    def _result(req_id: object, value: object) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "result": value}

    @staticmethod
    def _error(req_id: object, code: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": code}}
