"""Sessionless, provider-only MCP v2 facade.

This is intentionally a contract adapter: it exposes resource identifiers and
validates request shape; it does not execute a Skill Pack or select one.
"""
from __future__ import annotations

RESOURCE_OPERATIONS = (
    "skills_capabilities_get", "skills_catalog_list", "skills_catalog_search",
    "skills_release_list", "skills_release_describe", "skills_qualification_get",
    "skills_release_entrypoint_get", "skills_release_sections_list", "skills_release_section_get",
    "skills_release_resources_list", "skills_release_resource_get", "skills_release_content_get",
    "skills_release_package_get",
)
TOOLS = (
    "skills_release_verify", "skills_use_report_submit", "skills_use_report_status_get",
    "skills_feedback_submit", "skills_feedback_status_get", "skills_librarian_status_get",
)

class V2Provider:
    """Pure request gate for MCP 2026-07-28 semantics."""
    def resources(self) -> tuple[str, ...]: return RESOURCE_OPERATIONS
    def tools(self) -> tuple[str, ...]: return TOOLS
    def handle(self, request: dict) -> dict:
        if request.get("protocol_version") != "2026-07-28": return {"ok": False, "error": "contract_incompatible"}
        if not request.get("authorization"): return {"ok": False, "error": "auth_required"}
        if any(k in request for k in ("session", "session_id")) or request.get("operation") == "initialize": return {"ok": False, "error": "session_not_supported"}
        op = request.get("operation", "")
        if op.startswith("skills_run_") or op.startswith("skills_tool_"): return {"ok": False, "error": "legacy_execution_disabled"}
        if op not in RESOURCE_OPERATIONS + TOOLS: return {"ok": False, "error": "unsupported_operation"}
        if op in RESOURCE_OPERATIONS:
            version = request.get("version")
            if not isinstance(version, str) or not version: return {"ok": False, "error": "exact_release_required"}
            cursor, limit = request.get("cursor"), request.get("limit", 50)
            if not isinstance(limit, int) or not 1 <= limit <= 100: return {"ok": False, "error": "validation_failed"}
            return {"ok": True, "kind": "resource", "operation": op, "version": version, "cursor": cursor, "limit": limit, "no_fallback": True}
        return {"ok": True, "kind": "tool", "operation": op}


class ModernSkillsMcpServer:
    """Stateless MCP 2026-07-28 JSON-RPC adapter for the v2 provider facade.

    It intentionally has no ``initialize`` handshake or mutable session. Every
    request conveys authorization in its request metadata.
    """
    protocol_version = "2026-07-28"
    def __init__(self, provider: V2Provider | None = None) -> None: self.provider = provider or V2Provider()
    def handle_rpc(self, message: dict) -> dict | None:
        req_id = message.get("id"); method = message.get("method"); params = message.get("params") or {}
        if req_id is None: return None
        if method == "initialize": return self._error(req_id, "session_not_supported")
        auth = (params.get("_meta") or {}).get("authorization") or params.get("authorization")
        if method == "resources/list":
            response = self.provider.handle({"protocol_version":self.protocol_version,"authorization":auth,"operation":"skills_capabilities_get","version":"catalogue"})
            return self._result(req_id, {"resources": list(self.provider.resources())} if response["ok"] else response)
        if method == "tools/list":
            response = self.provider.handle({"protocol_version":self.protocol_version,"authorization":auth,"operation":"skills_release_verify"})
            return self._result(req_id, {"tools": list(self.provider.tools())} if response["ok"] else response)
        if method == "resources/read":
            uri = str(params.get("uri") or ""); operation = str(params.get("operation") or "")
            response = self.provider.handle({"protocol_version":self.protocol_version,"authorization":auth,"operation":operation,"version":params.get("version"),"cursor":params.get("cursor"),"limit":params.get("limit",50),"session_id":params.get("session_id")})
            return self._result(req_id, {"contents":[{"uri":uri,"text":""}],"structuredContent":response,"isError":not response["ok"]})
        if method == "tools/call":
            response = self.provider.handle({"protocol_version":self.protocol_version,"authorization":auth,"operation":params.get("name")})
            return self._result(req_id, {"structuredContent":response,"isError":not response["ok"]})
        return self._error(req_id, "unsupported_operation")
    @staticmethod
    def _result(req_id: object, value: object) -> dict: return {"jsonrpc":"2.0","id":req_id,"result":value}
    @staticmethod
    def _error(req_id: object, code: str) -> dict: return {"jsonrpc":"2.0","id":req_id,"error":{"code":-32602,"message":code}}
