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
    PROTOCOL_VERSION,
    RESOURCE_OPERATIONS,
    TOOLS,
    InMemoryProviderStore,
    SkillsApiV2,
    TrustedIdentity,
    V2Provider,
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
        """Extract transport metadata authorization, never caller claims."""
        meta = params.get("_meta")
        return meta.get("authorization") if isinstance(meta, Mapping) else params.get("authorization")

    def handle_rpc(self, message: Mapping[str, Any]) -> dict[str, Any] | None:
        """Handle one JSON-RPC request or return ``None`` for notifications."""
        req_id = message.get("id")
        method, raw_params = message.get("method"), message.get("params") or {}
        params = raw_params if isinstance(raw_params, Mapping) else {}
        if method == "initialize":
            requested = params.get("protocolVersion")
            authorization = self._authorization(params)
            if any(key in params for key in ("session", "session_id")):
                return self._error(req_id, "session_not_supported")
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
                    "serverInfo": {"name": "linkskills-mcp-v2", "version": "2.0.0"},
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
            request = dict(self._params_from_uri(params.get("uri")))
            request.update(params)
            request.update(
                {
                    "protocol_version": self.protocol_version,
                    "authorization": self._authorization(params),
                    "operation": request.get("operation") or self._operation_from_uri(request.get("uri")),
                }
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
            request = {"protocol_version": self.protocol_version, "authorization": self._authorization(params)}
            request.update(arguments)
            request["operation"] = params.get("name")
            response = self.provider.handle(request)
            return self._result(req_id, {"structuredContent": response, "isError": not response["ok"]})
        return self._error(req_id, "unsupported_operation")

    @staticmethod
    def _operation_from_uri(uri: Any) -> str | None:
        """Map standard resource URIs to the provider operation name."""
        if not isinstance(uri, str) or not uri.startswith("skills://"):
            return None
        if uri.startswith("skills://guide/domains/"):
            return "skills_capabilities_get"
        if uri.startswith("skills://guide/capabilities"):
            return "skills_capabilities_get"
        if uri.startswith("skills://catalog/search"):
            return "skills_catalog_search"
        if uri.startswith("skills://catalog"):
            return "skills_catalog_list"
        if uri.endswith("/entrypoint") or uri.endswith("/manifest"):
            return "skills_release_entrypoint_get"
        if "/section/" in uri or "/fragment/" in uri:
            return "skills_release_section_get"
        if "/resource/" in uri:
            return "skills_release_resource_get"
        if "/content/" in uri:
            return "skills_release_content_get"
        if uri.endswith("/package"):
            return "skills_release_package_get"
        if "/sections" in uri:
            return "skills_release_sections_list"
        if uri.endswith("/resources") or "/resources?" in uri:
            return "skills_release_resources_list"
        if uri.endswith("/summary"):
            return "skills_release_describe"
        if uri.endswith("/qualification"):
            return "skills_qualification_get"
        if uri.startswith("skills://release/"):
            return "skills_release_list"
        return None

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
