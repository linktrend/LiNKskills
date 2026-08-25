"""Standard MCP v2 provider for bounded discovery and exact release reads.

The provider is deliberately a read-only adapter. It does not run skills or
invoke consumer tools. Catalog metadata is returned family-first and exact
release resources are returned only after all independent policy gates pass.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from hashlib import sha256 as _sha256
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import parse_qs, urlparse

try:  # The package is installed in production; fallback keeps source tests portable.
    from linkskills_core.mcp_v2 import ExactResource, GovernedRelease, gate_denials
except ModuleNotFoundError:  # pragma: no cover - only a bare source checkout path
    ExactResource = None  # type: ignore[assignment,misc]
    GovernedRelease = None  # type: ignore[assignment,misc]
    gate_denials = None  # type: ignore[assignment,misc]


PROTOCOL_VERSION = "2026-07-28"
RESOURCE_OPERATIONS = (
    "skills_capabilities_get", "skills_catalog_list", "skills_catalog_search",
    "skills_release_list", "skills_release_describe", "skills_qualification_get",
    "skills_release_entrypoint_get", "skills_release_sections_list",
    "skills_release_section_get", "skills_release_resources_list",
    "skills_release_resource_get", "skills_release_content_get",
    "skills_release_package_get",
)
TOOLS = (
    "skills_release_verify", "skills_use_report_submit", "skills_use_report_status_get",
    "skills_feedback_submit", "skills_feedback_status_get", "skills_librarian_status_get",
)
CATALOG_OPERATIONS = frozenset(("skills_capabilities_get", "skills_catalog_list", "skills_catalog_search"))
_URI_TEMPLATES: dict[str, tuple[str, ...]] = {
    "skills_capabilities_get": ("skills://guide/capabilities",),
    "skills_catalog_list": ("skills://catalog?cursor={cursor}&limit={limit}",),
    "skills_catalog_search": ("skills://catalog/search?query={query}&cursor={cursor}&limit={limit}",),
    "skills_release_list": ("skills://release/{skill_id}?cursor={cursor}&limit={limit}",),
    "skills_release_describe": ("skills://release/{skill_id}/{version}/summary",),
    "skills_qualification_get": ("skills://release/{skill_id}/{version}/qualification",),
    "skills_release_entrypoint_get": ("skills://release/{skill_id}/{version}/entrypoint",),
    "skills_release_sections_list": ("skills://release/{skill_id}/{version}/sections?cursor={cursor}&limit={limit}",),
    "skills_release_section_get": ("skills://release/{skill_id}/{version}/section/{section_id}?cursor={cursor}&limit={limit}",),
    "skills_release_resources_list": ("skills://release/{skill_id}/{version}/resources?cursor={cursor}&limit={limit}",),
    "skills_release_resource_get": ("skills://release/{skill_id}/{version}/resource/{resource_id}?cursor={cursor}&limit={limit}",),
    "skills_release_content_get": ("skills://release/{skill_id}/{version}/content/{content_id}",),
    "skills_release_package_get": ("skills://release/{skill_id}/{version}/package",),
}


@dataclass(frozen=True)
class TrustedIdentity:
    """Already-verified Platform identity and consumer policy context."""

    org_id: str
    actor_id: str
    audience: str
    capabilities: frozenset[str]
    binding: str
    roles: frozenset[str] = frozenset()
    task_classes: frozenset[str] = frozenset()
    runtime_profiles: frozenset[str] = frozenset()
    activated_release_ids: frozenset[str] = frozenset()
    tool_capabilities: frozenset[str] = frozenset()


def _resource_record(operation: str) -> dict[str, Any]:
    """Return the PKT-01 operation descriptor without redefining its schema."""
    templates = _URI_TEMPLATES[operation]
    return {"name": operation, "uri_templates": list(templates), "uri_template": templates[0]}


def _flag(value: Any, default: bool = True) -> bool:
    """Read a gate boolean from either a boolean or PKT-01 gate object."""
    if value is None:
        return default
    if isinstance(value, Mapping):
        return bool(value.get("status", False))
    return bool(value)


def _set(value: Any) -> frozenset[str]:
    """Normalize an optional policy field to a string set."""
    if value is None:
        return frozenset()
    if isinstance(value, str):
        return frozenset({value} if value else ())
    try:
        return frozenset(str(item) for item in value if item is not None and str(item))
    except TypeError:
        return frozenset({str(value)})


def _digest(body: bytes) -> str:
    """Return the repository digest spelling used by PKT-01 contracts."""
    return "sha256:" + _sha256(body).hexdigest()


def _normalize_resource(resource_id: str, value: Any, release: Mapping[str, Any]) -> Any:
    """Normalize fixture mappings without inventing provenance for exact reads."""
    if isinstance(value, ExactResource):
        return value
    if isinstance(value, bytes):
        metadata: Mapping[str, Any] = {}
        body = value
    elif isinstance(value, Mapping):
        metadata = value
        if not any(key in value for key in ("body", "bytes", "content")):
            raise ValueError("invalid_resource_body")
        raw = value.get("body", value.get("bytes", value.get("content")))
        body = raw.encode("utf-8") if isinstance(raw, str) else raw
    else:
        body = b""
        metadata = {}
    if not isinstance(body, bytes):
        raise ValueError("invalid_resource_body")
    declared_digest = metadata.get("content_digest")
    if declared_digest is not None and declared_digest != _digest(body):
        raise ValueError("integrity_mismatch")
    provenance = metadata.get("provenance", release.get("provenance", {}))
    licence = metadata.get("licence", metadata.get("license", release.get("licence", {})))
    return ExactResource(
        resource_id=str(metadata.get("resource_id", resource_id)), body=body,
        resource_kind=str(metadata.get("resource_kind", "entrypoint")),
        media_type=str(metadata.get("media_type", "text/markdown")),
        disclosure_level=int(metadata.get("disclosure_level", 3)),
        provenance=dict(provenance or {}), licence=dict(licence or {}),
    )


def _normalize_release(value: Any) -> Any:
    """Normalize a PKT-01-shaped release fixture to a governed immutable record."""
    if isinstance(value, GovernedRelease):
        return value
    if not isinstance(value, Mapping):
        raise ValueError("invalid_release")
    skill_id = str(value.get("skill_id", value.get("artifact_id", "")))
    version = str(value.get("version", ""))
    resources_value = value.get("resources", value.get("resource_bytes", value.get("files", {})))
    if isinstance(resources_value, Mapping):
        resources = tuple(_normalize_resource(str(resource_id), resource, value) for resource_id, resource in resources_value.items())
    elif isinstance(resources_value, Iterable) and not isinstance(resources_value, (str, bytes)):
        resources = tuple(
            _normalize_resource(str(resource.get("resource_id", "")) if isinstance(resource, Mapping) else "", resource, value)
            for resource in resources_value
        )
    else:
        resources = ()
    release = GovernedRelease(
        skill_id=skill_id, version=version, resources=resources,
        family_id=str(value.get("family_id", "")), subcategory_id=str(value.get("subcategory_id", "")),
        collection_id=str(value.get("collection_id", "")),
        lifecycle_state=str(value.get("lifecycle_state", value.get("lifecycle", "qualified"))),
        qualification=str(value.get("qualification", value.get("qualification_state", "qualified"))),
        platform_technical_eligibility=_flag(value.get("platform_technical_eligibility")),
        skills_release_selectability=_flag(value.get("skills_release_selectability")),
        consumer_profile_activation=_flag(value.get("consumer_profile_activation", value.get("profile_activation"))),
        consumer_tool_authority=_flag(value.get("consumer_tool_authority", value.get("tool_authority"))),
        roles=_set(value.get("roles", value.get("role_classes"))), task_classes=_set(value.get("task_classes")),
        runtime_profiles=_set(value.get("runtime_profiles", value.get("compatible_runtime_profiles"))),
        required_capabilities=_set(value.get("required_capabilities", value.get("required_capability_classes"))),
        provenance=dict(value.get("provenance", {})), applicability=dict(value.get("applicability", {})),
    )
    if not release.skill_id or not release.version:
        raise ValueError("invalid_release_identity")
    return release


class V2Provider:
    """Stateless, fail-closed MCP v2 provider over exact release fixtures."""

    def __init__(self, verifier: Callable[[str], TrustedIdentity] | None = None, *, catalog_version: str = "catalog-v2", families: Iterable[Mapping[str, Any]] | None = None, releases: Iterable[Any] | Mapping[str, Any] | None = None, contract_validator: Callable[[Mapping[str, Any]], Any] | None = None) -> None:
        self._verifier = verifier or (lambda _: (_ for _ in ()).throw(ValueError("verifier_required")))
        self._snapshot_id = "snapshot:" + _sha256(catalog_version.encode()).hexdigest()[:16]
        self._contract_validator = contract_validator
        self._registry: dict[str, Any] = {}
        if releases:
            values = releases.values() if isinstance(releases, Mapping) else releases
            for release in values:
                normalized = _normalize_release(release)
                self._registry[normalized.release_id] = normalized
        self._families = self._normalize_families(families)
        self._has_registry = bool(self._registry)

    def _normalize_families(self, families: Iterable[Mapping[str, Any]] | None) -> tuple[dict[str, Any], ...]:
        """Create bounded family metadata, deriving only identifiers from releases."""
        if families is not None:
            return tuple(
                {
                    "family_id": str(family.get("family_id", "")),
                    "display_name": str(family.get("display_name", family.get("family_id", ""))),
                    "description": str(family.get("description", "")),
                    "subcategories": tuple(
                        {"subcategory_id": str(item.get("subcategory_id", "")), "display_name": str(item.get("display_name", item.get("subcategory_id", ""))), "description": str(item.get("description", ""))}
                        for item in family.get("subcategories", ()) if isinstance(item, Mapping)
                    ),
                }
                for family in families if isinstance(family, Mapping) and family.get("family_id")
            )
        derived: dict[str, dict[str, Any]] = {}
        for release in self._registry.values():
            if release.family_id and release.family_id not in derived:
                derived[release.family_id] = {"family_id": release.family_id, "display_name": release.family_id.replace("-", " ").title(), "description": "Qualified LiNKskills releases.", "subcategories": ()}
        return tuple(derived.values())

    def resources(self) -> tuple[dict[str, Any], ...]:
        """Advertise the PKT-01 resource map."""
        return tuple(_resource_record(operation) for operation in RESOURCE_OPERATIONS)

    def tools(self) -> tuple[str, ...]:
        """Advertise bounded report/status tools, never run/invoke tools."""
        return TOOLS

    def _identity(self, authorization: Any) -> TrustedIdentity:
        """Resolve already-verified Platform identity and enforce read scope."""
        if not isinstance(authorization, str) or not authorization:
            raise ValueError("auth_required")
        try:
            identity = self._verifier(authorization)
        except Exception as exc:
            raise ValueError("auth_invalid") from exc
        if not isinstance(identity, TrustedIdentity) or not identity.org_id or not identity.actor_id or not identity.binding:
            raise ValueError("auth_invalid")
        if identity.audience != "lskills-api" or "skills.read" not in identity.capabilities:
            raise ValueError("forbidden")
        return identity

    def _cursor(self, cursor: Any) -> int:
        """Decode a cursor bound to this immutable snapshot and page offset."""
        if cursor is None:
            return 0
        if not isinstance(cursor, str):
            raise ValueError("cursor_invalid")
        parts = cursor.split(":")
        if len(parts) != 3 or f"{parts[0]}:{parts[1]}" != self._snapshot_id:
            raise ValueError("cursor_snapshot_mismatch")
        try:
            offset = int(parts[2])
        except ValueError as exc:
            raise ValueError("cursor_invalid") from exc
        if offset < 0:
            raise ValueError("cursor_invalid")
        return offset

    @staticmethod
    def _limit(value: Any) -> int:
        """Enforce a bounded page size."""
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 100:
            raise ValueError("validation_failed")
        return value

    def _page(self, items: list[dict[str, Any]], offset: int, limit: int) -> dict[str, Any]:
        """Return bounded items with a snapshot-bound continuation cursor."""
        page = items[offset:offset + limit]
        end = offset + len(page)
        return {"items": page, "has_more": end < len(items), "next_cursor": f"{self._snapshot_id}:{end}" if end < len(items) else None}

    def _release(self, skill_id: Any, version: Any) -> Any:
        """Resolve an exact release identity; never select a substitute."""
        if not isinstance(skill_id, str) or not skill_id or not isinstance(version, str) or not version:
            raise ValueError("exact_release_required")
        release = self._registry.get(f"{skill_id}@{version}")
        if self._has_registry and release is None:
            raise ValueError("not_found")
        return release

    def _authorize_release(self, release: Any, identity: TrustedIdentity, request: Mapping[str, Any]) -> None:
        """Apply independent Platform, Skills, profile, role, and tool gates."""
        if release is None:
            return
        denials = gate_denials(release, roles=request.get("role") or request.get("role_class") or identity.roles, task_class=request.get("task_class") or identity.task_classes, runtime_profile=request.get("runtime_profile") or identity.runtime_profiles, capabilities=identity.capabilities | identity.tool_capabilities, activated_release_ids=identity.activated_release_ids)
        if denials:
            raise ValueError(denials[0])

    def _descriptor(self, descriptor: Mapping[str, Any]) -> None:
        """Optionally validate against the PKT-01 descriptor contract."""
        if self._contract_validator is None:
            return
        result = self._contract_validator(descriptor)
        if (hasattr(result, "ok") and not result.ok) or result is False:
            raise ValueError("contract_invalid")

    def _resource_result(self, operation: str, release: Any, resource_id: str) -> dict[str, Any]:
        """Return one exact descriptor and exact bytes for a selected release."""
        if release is None:
            return {"ok": True, "resource_id": resource_id, "bytes": b"", "content_digest": _digest(b"")}
        resource = release.resource(resource_id)
        if resource is None:
            raise ValueError("not_found")
        descriptor = resource.descriptor(release.skill_id, release.version)
        self._descriptor(descriptor)
        return {"ok": True, "kind": "resource", "operation": operation, "skill_id": release.skill_id, "version": release.version, "resource_id": resource.resource_id, "resource_uri": descriptor["resource_uri"], "descriptor": descriptor, "bytes": resource.body, "byte_size": len(resource.body), "content_digest": resource.content_digest, "immutable": True}

    def handle(self, request: Mapping[str, Any]) -> dict[str, Any]:
        """Handle one stateless provider request with typed fail-closed errors."""
        if request.get("protocol_version") != PROTOCOL_VERSION:
            return {"ok": False, "error": "contract_incompatible"}
        if any(key in request for key in ("session", "session_id")):
            return {"ok": False, "error": "session_not_supported"}
        operation = request.get("operation")
        if not isinstance(operation, str):
            return {"ok": False, "error": "unsupported_operation"}
        if operation.startswith("skills_run_") or operation.startswith("skills_tool_"):
            return {"ok": False, "error": "legacy_execution_disabled"}
        if operation not in RESOURCE_OPERATIONS + TOOLS:
            return {"ok": False, "error": "unsupported_operation"}
        try:
            identity = self._identity(request.get("authorization"))
            if operation in TOOLS:
                return {"ok": True, "kind": "tool", "operation": operation}
            limit = self._limit(request.get("limit", 50))
            offset = self._cursor(request.get("cursor"))
            result: dict[str, Any] = {"ok": True, "kind": "resource", "operation": operation, "snapshot_id": self._snapshot_id, "cursor": f"{self._snapshot_id}:{offset}", "limit": limit, "no_fallback": True}
            if operation == "skills_capabilities_get":
                result.update({"capabilities": {"resources": True, "tools": True, "pagination": True}, "resources": list(self.resources()), "tools": list(self.tools())})
                return result
            if operation in {"skills_catalog_list", "skills_catalog_search"}:
                families = list(self._families)
                query = str(request.get("query", "")).strip().casefold()
                if operation == "skills_catalog_search" and query:
                    families = [family for family in families if query in " ".join(str(family.get(field, "")) for field in ("family_id", "display_name", "description")).casefold()]
                result.update(self._page([{"family_id": family["family_id"], "display_name": family["display_name"], "description": family["description"], "subcategory_count": len(family.get("subcategories", ())) } for family in families], offset, limit))
                return result
            if operation == "skills_release_list":
                family_id = request.get("family_id")
                if self._has_registry and family_id and not any(family.get("family_id") == family_id for family in self._families):
                    return {"ok": False, "error": "not_found"}
                entries = [{"skill_id": release.skill_id, "version": release.version, "release_id": release.release_id, "family_id": release.family_id, "subcategory_id": release.subcategory_id, "collection_id": release.collection_id, "lifecycle_state": release.lifecycle_state, "qualification": release.qualification} for release in self._registry.values() if not family_id or release.family_id == family_id]
                result.update(self._page(entries, offset, limit))
                return result
            release = self._release(request.get("skill_id"), request.get("version"))
            self._authorize_release(release, identity, request)
            if operation == "skills_release_describe":
                result.update({"skill_id": request["skill_id"], "version": request["version"], "release_id": f"{request['skill_id']}@{request['version']}"})
                if release is not None:
                    result.update({"family_id": release.family_id, "subcategory_id": release.subcategory_id, "lifecycle_state": release.lifecycle_state, "qualification": release.qualification, "provenance": dict(release.provenance)})
                return result
            if operation == "skills_qualification_get":
                return dict(result, qualification=(release.qualification if release else "qualified"))
            if operation in {"skills_release_resources_list", "skills_release_sections_list"}:
                descriptors = []
                if release is not None:
                    for resource in release.resources:
                        descriptor = resource.descriptor(release.skill_id, release.version)
                        self._descriptor(descriptor)
                        descriptors.append(descriptor)
                result.update(self._page(descriptors, offset, limit))
                return result
            if operation in {"skills_release_entrypoint_get", "skills_release_section_get", "skills_release_resource_get", "skills_release_content_get"}:
                resource_id = request.get("resource_id") or request.get("content_id")
                if operation == "skills_release_entrypoint_get":
                    resource_id = "entrypoint"
                if operation == "skills_release_section_get":
                    resource_id = request.get("section_id")
                if not isinstance(resource_id, str) or not resource_id:
                    return {"ok": False, "error": "exact_resource_required"}
                return self._resource_result(operation, release, resource_id)
            if operation == "skills_release_package_get":
                if release is None:
                    return dict(result, bytes=b"", byte_size=0, content_digest=_digest(b""), immutable=True)
                body = b"".join(resource.body for resource in release.resources)
                return dict(result, bytes=body, byte_size=len(body), content_digest=_digest(body), immutable=True, resource_count=len(release.resources))
            return {"ok": False, "error": "unsupported_operation"}
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}


class ModernSkillsMcpServer:
    """JSON-RPC MCP facade with initialize negotiation and stateless requests."""

    protocol_version = PROTOCOL_VERSION

    def __init__(self, provider: V2Provider) -> None:
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
            requested = params.get("protocolVersion", params.get("protocol_version"))
            authorization = self._authorization(params)
            if requested is None and authorization is None:
                return self._error(req_id, "session_not_supported")
            if requested not in (None, self.protocol_version):
                return self._result(req_id, {"ok": False, "error": "contract_incompatible"})
            if authorization is not None:
                auth = self.provider.handle({"protocol_version": self.protocol_version, "authorization": authorization, "operation": "skills_capabilities_get"})
                if not auth["ok"]:
                    return self._result(req_id, auth)
            self._initialized = True
            return self._result(req_id, {"protocolVersion": self.protocol_version, "capabilities": {"resources": {"listChanged": False, "subscribe": False}, "tools": {}}, "serverInfo": {"name": "linkskills-mcp-v2", "version": "2.0.0"}})
        if method == "notifications/initialized":
            self._initialized = True
            return None
        if method == "ping":
            return self._result(req_id, {})
        if method == "resources/list":
            auth = self.provider.handle({"protocol_version": self.protocol_version, "authorization": self._authorization(params), "operation": "skills_capabilities_get"})
            return self._result(req_id, {"resources": list(self.provider.resources())} if auth["ok"] else auth)
        if method == "tools/list":
            auth = self.provider.handle({"protocol_version": self.protocol_version, "authorization": self._authorization(params), "operation": "skills_capabilities_get"})
            return self._result(req_id, {"tools": list(self.provider.tools())} if auth["ok"] else auth)
        if method == "resources/read":
            request = dict(self._params_from_uri(params.get("uri")))
            request.update(params)
            request.update({"protocol_version": self.protocol_version, "authorization": self._authorization(params), "operation": request.get("operation") or self._operation_from_uri(request.get("uri"))})
            response = self.provider.handle(request)
            if not response["ok"]:
                return self._result(req_id, {"contents": [], "structuredContent": response, "isError": True})
            body = response.pop("bytes", None)
            contents = []
            if isinstance(body, bytes):
                contents.append({"uri": response.get("resource_uri", request.get("uri", "")), "mimeType": (response.get("descriptor") or {}).get("media_type", "application/octet-stream"), "blob": base64.b64encode(body).decode("ascii")})
            return self._result(req_id, {"contents": contents, "structuredContent": response})
        if method == "tools/call":
            response = self.provider.handle({"protocol_version": self.protocol_version, "authorization": self._authorization(params), "operation": params.get("name")})
            return self._result(req_id, {"structuredContent": response, "isError": not response["ok"]})
        return self._error(req_id, "unsupported_operation")

    @staticmethod
    def _operation_from_uri(uri: Any) -> str | None:
        """Map standard resource URIs to the provider operation name."""
        if not isinstance(uri, str) or not uri.startswith("skills://"):
            return None
        if uri.startswith("skills://catalog/search"):
            return "skills_catalog_search"
        if uri.startswith("skills://catalog"):
            return "skills_catalog_list"
        if uri.endswith("/entrypoint"):
            return "skills_release_entrypoint_get"
        if "/resource/" in uri:
            return "skills_release_resource_get"
        if "/content/" in uri:
            return "skills_release_content_get"
        if uri.endswith("/package"):
            return "skills_release_package_get"
        if uri.endswith("/resources"):
            return "skills_release_resources_list"
        if uri.endswith("/summary"):
            return "skills_release_describe"
        if uri.endswith("/qualification"):
            return "skills_qualification_get"
        return None

    @classmethod
    def _params_from_uri(cls, uri: Any) -> dict[str, Any]:
        """Extract exact resource identifiers from a standard Skills URI."""
        if not isinstance(uri, str) or not uri.startswith("skills://"):
            return {}
        parsed = urlparse(uri)
        parts = [part for part in (parsed.netloc, *parsed.path.split("/")) if part]
        values: dict[str, Any] = {}
        if len(parts) >= 3 and parts[0] == "release":
            values.update({"skill_id": parts[1], "version": parts[2]})
            if len(parts) >= 5:
                values[{"resource": "resource_id", "content": "content_id", "section": "section_id"}.get(parts[3], "resource_id")] = parts[4]
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


__all__ = ["CATALOG_OPERATIONS", "ModernSkillsMcpServer", "PROTOCOL_VERSION", "RESOURCE_OPERATIONS", "TOOLS", "TrustedIdentity", "V2Provider"]
