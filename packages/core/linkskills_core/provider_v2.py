"""Transport-independent production ``skills.api.v0.2`` domain.

HTTP and MCP adapters call this module. They must not reimplement gates,
pagination, digest verification, or legacy-execution denial. Bytes stay
immutable; identity comes only from a trusted verifier result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256 as _sha256
from typing import Any, Callable, Iterable, Mapping, Protocol

from .hashing import request_hash
from .mcp_v2 import ExactResource, GovernedRelease, gate_denials
from .payload_guard import PayloadValidationError, allowlist_and_redact, reject_forbidden_privacy
from .release_v2 import sha256 as release_sha256

PROTOCOL_VERSION = "2026-07-28"
CONTRACT_VERSION = "skills.api.v0.2"
RESOURCE_OPERATIONS = (
    "skills_capabilities_get",
    "skills_catalog_list",
    "skills_catalog_search",
    "skills_release_list",
    "skills_release_describe",
    "skills_qualification_get",
    "skills_release_entrypoint_get",
    "skills_release_sections_list",
    "skills_release_section_get",
    "skills_release_resources_list",
    "skills_release_resource_get",
    "skills_release_content_get",
    "skills_release_package_get",
)
TOOLS = (
    "skills_release_verify",
    "skills_use_report_submit",
    "skills_use_report_status_get",
    "skills_feedback_submit",
    "skills_feedback_status_get",
    "skills_librarian_status_get",
)
CATALOG_OPERATIONS = frozenset(
    ("skills_capabilities_get", "skills_catalog_list", "skills_catalog_search")
)
WRITE_TOOLS = frozenset({"skills_use_report_submit", "skills_feedback_submit"})
LEGACY_EXECUTION_PREFIXES = ("skills_run_", "skills_tool_")
_URI_TEMPLATES: dict[str, tuple[str, ...]] = {
    "skills_capabilities_get": (
        "skills://guide/capabilities",
        "skills://guide/domains/{domain}",
    ),
    "skills_catalog_list": ("skills://catalog?cursor={cursor}&limit={limit}",),
    "skills_catalog_search": (
        "skills://catalog/search?query={query}&cursor={cursor}&limit={limit}",
    ),
    "skills_release_list": ("skills://release/{skill_id}?cursor={cursor}&limit={limit}",),
    "skills_release_describe": ("skills://release/{skill_id}/{version}/summary",),
    "skills_qualification_get": (
        "skills://release/{skill_id}/{version}/qualification",
    ),
    "skills_release_entrypoint_get": (
        "skills://release/{skill_id}/{version}/manifest",
        "skills://release/{skill_id}/{version}/entrypoint",
    ),
    "skills_release_sections_list": (
        "skills://release/{skill_id}/{version}/sections?cursor={cursor}&limit={limit}",
    ),
    "skills_release_section_get": (
        "skills://release/{skill_id}/{version}/section/{section_id}?cursor={cursor}&limit={limit}",
        "skills://release/{skill_id}/{version}/fragment/{fragment_id}?cursor={cursor}&limit={limit}",
    ),
    "skills_release_resources_list": (
        "skills://release/{skill_id}/{version}/resources?cursor={cursor}&limit={limit}",
    ),
    "skills_release_resource_get": (
        "skills://release/{skill_id}/{version}/resource/{resource_id}?cursor={cursor}&limit={limit}",
    ),
    "skills_release_content_get": (
        "skills://release/{skill_id}/{version}/content/{content_id}",
    ),
    "skills_release_package_get": ("skills://release/{skill_id}/{version}/package",),
}
_TYPED_GATE = {
    "release_not_qualified": "not_qualified",
    "release_not_selectable": "not_qualified",
}
USE_REPORT_KEYS = {
    "schema_version",
    "report_kind",
    "report_id",
    "occurred_at",
    "skill_id",
    "skill_release_ref",
    "consumer_class",
    "actor_ref",
    "actor_class",
    "runtime_profile_ref",
    "outcome",
    "opaque_refs",
    "idempotency_source",
    "server_idempotency_key",
    "client_idempotency_key",
    "score",
    "issue",
    "non_use_outcome",
}
FEEDBACK_V2_KEYS = {
    "skill_id",
    "skill_release_ref",
    "feedback_id",
    "kind",
    "rating",
    "outcome",
    "client_idempotency_key",
    "opaque_refs",
}
_REDACTED = "[redacted]"


class ProviderV2Store(Protocol):
    """Minimal durable receipt surface used by v2 tools. Never returns secrets."""

    def probe(self) -> Mapping[str, Any]:
        """Return a non-secret reachability snapshot or raise."""

    def put(self, kind: str, receipt_id: str, record: Mapping[str, Any]) -> Mapping[str, Any]:
        """Insert or replay a receipt. Conflict must fail closed."""

    def get(self, kind: str, receipt_id: str) -> Mapping[str, Any] | None:
        """Return a previously stored receipt, or ``None``."""


class InMemoryProviderStore:
    """Ephemeral receipts for source proof. Not a production store."""

    def __init__(self) -> None:
        self._rows: dict[tuple[str, str], dict[str, Any]] = {}
        self.available = True

    def probe(self) -> Mapping[str, Any]:
        if not self.available:
            raise RuntimeError("OperationalError")
        return {"ready": False, "code": "store_memory_not_production", "fail_closed": True}

    def put(self, kind: str, receipt_id: str, record: Mapping[str, Any]) -> Mapping[str, Any]:
        if not self.available:
            raise RuntimeError("OperationalError")
        key = (kind, receipt_id)
        existing = self._rows.get(key)
        if existing is not None:
            if existing.get("request_hash") != record.get("request_hash"):
                raise ValueError("idempotency_conflict")
            return existing
        stored = dict(record)
        self._rows[key] = stored
        return stored

    def get(self, kind: str, receipt_id: str) -> Mapping[str, Any] | None:
        if not self.available:
            raise RuntimeError("OperationalError")
        return self._rows.get((kind, receipt_id))


def diagnose_store_failure(exc: BaseException) -> dict[str, Any]:
    """Sanitise a store fault without importing persistence (optional overlay)."""
    try:
        from linkskills_persistence.readiness import diagnose_store_exception

        return dict(diagnose_store_exception(exc))
    except Exception:
        name = type(exc).__name__
        if "OperationalError" in name or "OperationalError" in str(exc):
            code = "store_unreachable"
        else:
            code = "store_not_ready"
        return {
            "ready": False,
            "fail_closed": True,
            "live_apply": False,
            "code": code,
            "redacted_error": name,
            "does_not_include": "dsn_credentials_host_or_sqlstate_detail",
        }


def _resource_record(operation: str) -> dict[str, Any]:
    """Return the PKT-01 operation descriptor without redefining its schema."""
    templates = _URI_TEMPLATES[operation]
    return {
        "name": operation,
        "uri_templates": list(templates),
        "uri_template": templates[0],
    }


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


def server_idempotency_key(
    *,
    actor_id: str,
    org_id: str,
    operation: str,
    client_key: str,
    canonical: Mapping[str, Any],
) -> str:
    """Derive the only authoritative idempotency key; client keys are inputs."""
    digest = request_hash(
        {
            "actor_id": actor_id,
            "org_id": org_id,
            "operation": operation,
            "client_key": client_key,
            "canonical": dict(canonical),
        }
    )
    return "sha256:" + digest


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
        resource_id=str(metadata.get("resource_id", resource_id)),
        body=body,
        resource_kind=str(metadata.get("resource_kind", "entrypoint")),
        media_type=str(metadata.get("media_type", "text/markdown")),
        disclosure_level=int(metadata.get("disclosure_level", 3)),
        provenance=dict(provenance or {}),
        licence=dict(licence or {}),
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
        resources = tuple(
            _normalize_resource(str(resource_id), resource, value)
            for resource_id, resource in resources_value.items()
        )
    elif isinstance(resources_value, Iterable) and not isinstance(resources_value, (str, bytes)):
        resources = tuple(
            _normalize_resource(
                str(resource.get("resource_id", "")) if isinstance(resource, Mapping) else "",
                resource,
                value,
            )
            for resource in resources_value
        )
    else:
        resources = ()
    release = GovernedRelease(
        skill_id=skill_id,
        version=version,
        resources=resources,
        family_id=str(value.get("family_id", "")),
        subcategory_id=str(value.get("subcategory_id", "")),
        collection_id=str(value.get("collection_id", "")),
        lifecycle_state=str(value.get("lifecycle_state", value.get("lifecycle", "qualified"))),
        qualification=str(value.get("qualification", value.get("qualification_state", "qualified"))),
        platform_technical_eligibility=_flag(value.get("platform_technical_eligibility")),
        skills_release_selectability=_flag(value.get("skills_release_selectability")),
        consumer_profile_activation=_flag(
            value.get("consumer_profile_activation", value.get("profile_activation"))
        ),
        consumer_tool_authority=_flag(
            value.get("consumer_tool_authority", value.get("tool_authority"))
        ),
        roles=_set(value.get("roles", value.get("role_classes"))),
        task_classes=_set(value.get("task_classes")),
        runtime_profiles=_set(value.get("runtime_profiles", value.get("compatible_runtime_profiles"))),
        required_capabilities=_set(
            value.get("required_capabilities", value.get("required_capability_classes"))
        ),
        provenance=dict(value.get("provenance", {})),
        applicability=dict(value.get("applicability", {})),
    )
    if not release.skill_id or not release.version:
        raise ValueError("invalid_release_identity")
    return release


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


@dataclass
class SkillsApiV2:
    """Stateless, fail-closed production provider-v2 domain.

    ``V2Provider`` is the historical name retained as an alias.
    """

    verifier: Callable[[str], TrustedIdentity]
    catalog_version: str = "catalog-v2"
    families: Iterable[Mapping[str, Any]] | None = None
    releases: Iterable[Any] | Mapping[str, Any] | None = None
    contract_validator: Callable[[Mapping[str, Any]], Any] | None = None
    store: ProviderV2Store | None = field(default=None)
    production_store: bool = False

    def __post_init__(self) -> None:
        if self.verifier is None:
            raise ValueError("verifier_required")
        object.__setattr__(
            self,
            "_snapshot_id",
            "snapshot:" + _sha256(self.catalog_version.encode()).hexdigest()[:16],
        )
        registry: dict[str, Any] = {}
        if self.releases:
            values = self.releases.values() if isinstance(self.releases, Mapping) else self.releases
            for release in values:
                normalized = _normalize_release(release)
                registry[normalized.release_id] = normalized
        object.__setattr__(self, "_registry", registry)
        object.__setattr__(self, "_has_registry", bool(registry))
        object.__setattr__(self, "_families", self._normalize_families(self.families))
        object.__setattr__(self, "_store", self.store if self.store is not None else InMemoryProviderStore())

    def _normalize_families(
        self, families: Iterable[Mapping[str, Any]] | None
    ) -> tuple[dict[str, Any], ...]:
        """Create bounded family metadata, deriving only identifiers from releases."""
        if families is not None:
            return tuple(
                {
                    "family_id": str(family.get("family_id", "")),
                    "display_name": str(family.get("display_name", family.get("family_id", ""))),
                    "description": str(family.get("description", "")),
                    "subcategories": tuple(
                        {
                            "subcategory_id": str(item.get("subcategory_id", "")),
                            "display_name": str(
                                item.get("display_name", item.get("subcategory_id", ""))
                            ),
                            "description": str(item.get("description", "")),
                        }
                        for item in family.get("subcategories", ())
                        if isinstance(item, Mapping)
                    ),
                }
                for family in families
                if isinstance(family, Mapping) and family.get("family_id")
            )
        derived: dict[str, dict[str, Any]] = {}
        for release in self._registry.values():
            if release.family_id and release.family_id not in derived:
                derived[release.family_id] = {
                    "family_id": release.family_id,
                    "display_name": release.family_id.replace("-", " ").title(),
                    "description": "Qualified LiNKskills releases.",
                    "subcategories": (),
                }
        return tuple(derived.values())

    def resources(self) -> tuple[dict[str, Any], ...]:
        """Advertise the PKT-01 resource map."""
        return tuple(_resource_record(operation) for operation in RESOURCE_OPERATIONS)

    def tools(self) -> tuple[str, ...]:
        """Advertise bounded report/status tools, never run/invoke tools."""
        return TOOLS

    def store_status(self) -> dict[str, Any]:
        """Sanitised store probe used by readiness and Librarian status."""
        try:
            snapshot = dict(self._store.probe())
        except Exception as exc:
            return diagnose_store_failure(exc)
        if self.production_store and snapshot.get("ready"):
            return {"ready": True, "fail_closed": True, "code": "store_ready"}
        if snapshot.get("code") == "store_memory_not_production":
            return dict(snapshot)
        if not snapshot.get("ready", True):
            return {
                "ready": False,
                "fail_closed": True,
                "code": str(snapshot.get("code") or "store_not_ready"),
            }
        return {"ready": True, "fail_closed": True, "code": "store_ready"}

    def _identity(self, authorization: Any) -> TrustedIdentity:
        """Resolve already-verified Platform identity and enforce read scope."""
        if not isinstance(authorization, str) or not authorization:
            raise ValueError("auth_required")
        try:
            identity = self.verifier(authorization)
        except Exception as exc:
            raise ValueError("auth_invalid") from exc
        if (
            not isinstance(identity, TrustedIdentity)
            or not identity.org_id
            or not identity.actor_id
            or not identity.binding
        ):
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
        page = items[offset : offset + limit]
        end = offset + len(page)
        return {
            "items": page,
            "has_more": end < len(items),
            "next_cursor": f"{self._snapshot_id}:{end}" if end < len(items) else None,
        }

    def _release(self, skill_id: Any, version: Any) -> Any:
        """Resolve an exact release identity; never select a substitute."""
        if not isinstance(skill_id, str) or not skill_id or not isinstance(version, str) or not version:
            raise ValueError("exact_release_required")
        release = self._registry.get(f"{skill_id}@{version}")
        if self._has_registry and release is None:
            raise ValueError("not_found")
        return release

    def _authorize_release(
        self, release: Any, identity: TrustedIdentity, request: Mapping[str, Any]
    ) -> None:
        """Apply independent Platform, Skills, profile, role, and tool gates."""
        if release is None:
            return
        if release.lifecycle_state in {"revoked", "withdrawn"}:
            raise ValueError("revoked_release")
        if release.lifecycle_state == "expired":
            raise ValueError("expired_release")
        denials = gate_denials(
            release,
            roles=request.get("role") or request.get("role_class") or identity.roles,
            task_class=request.get("task_class") or identity.task_classes,
            runtime_profile=request.get("runtime_profile") or identity.runtime_profiles,
            capabilities=identity.capabilities | identity.tool_capabilities,
            activated_release_ids=identity.activated_release_ids,
        )
        if denials:
            raise ValueError(_TYPED_GATE.get(denials[0], denials[0]))

    def _descriptor(self, descriptor: Mapping[str, Any]) -> None:
        """Optionally validate against the PKT-01 descriptor contract."""
        if self.contract_validator is None:
            return
        result = self.contract_validator(descriptor)
        if (hasattr(result, "ok") and not result.ok) or result is False:
            raise ValueError("contract_invalid")

    def _resource_result(
        self,
        operation: str,
        release: Any,
        resource_id: str,
        expected_digest: Any = None,
    ) -> dict[str, Any]:
        """Return one exact descriptor and exact bytes for a selected release."""
        if release is None:
            body = b""
            digest = _digest(body)
            if expected_digest not in (None, "", digest):
                raise ValueError("integrity_mismatch")
            return {
                "ok": True,
                "resource_id": resource_id,
                "bytes": body,
                "content_digest": digest,
            }
        resource = release.resource(resource_id)
        if resource is None:
            raise ValueError("not_found")
        descriptor = resource.descriptor(release.skill_id, release.version)
        self._descriptor(descriptor)
        if expected_digest not in (None, "", resource.content_digest):
            raise ValueError("integrity_mismatch")
        return {
            "ok": True,
            "kind": "resource",
            "operation": operation,
            "skill_id": release.skill_id,
            "version": release.version,
            "resource_id": resource.resource_id,
            "resource_uri": descriptor["resource_uri"],
            "descriptor": descriptor,
            "bytes": resource.body,
            "byte_size": len(resource.body),
            "content_digest": resource.content_digest,
            "immutable": True,
        }

    def _store_call(self, fn: Callable[[], Any]) -> Any:
        """Run a store mutator/read and fail closed with a sanitised error."""
        try:
            return fn()
        except ValueError as exc:
            if str(exc) == "idempotency_conflict":
                raise
            raise ValueError("validation_failed") from exc
        except Exception as exc:
            diagnosis = diagnose_store_failure(exc)
            error = ValueError("store_unavailable")
            error.diagnosis = diagnosis  # type: ignore[attr-defined]
            raise error from exc

    def _handle_tool(
        self, operation: str, request: Mapping[str, Any], identity: TrustedIdentity
    ) -> dict[str, Any]:
        """Bounded verify / use / feedback / Librarian tools. No execution route."""
        if operation in WRITE_TOOLS:
            write_caps = identity.capabilities | identity.tool_capabilities
            if not write_caps.intersection({"skills.feedback", "skills.write", "skills.read"}):
                raise ValueError("forbidden")
        if operation == "skills_librarian_status_get":
            status = self.store_status()
            return {
                "ok": True,
                "kind": "tool",
                "operation": operation,
                "librarian": {
                    "state": "available" if status.get("ready") and self.production_store else "degraded",
                    "store": {
                        "code": status.get("code"),
                        "ready": bool(status.get("ready")),
                        "fail_closed": True,
                    },
                    "does_not_prove": "consumer_execution_or_production_readiness",
                    "contract_version": CONTRACT_VERSION,
                },
            }
        if operation == "skills_release_verify":
            release = self._release(request.get("skill_id"), request.get("version"))
            self._authorize_release(release, identity, request)
            if release is None:
                body = b""
                digest = _digest(body)
            else:
                body = b"".join(resource.body for resource in release.resources)
                digest = _digest(body)
                release.verify_inventory()
            expected = request.get("expected_digest") or request.get("package_digest")
            if expected not in (None, "", digest):
                raise ValueError("integrity_mismatch")
            return {
                "ok": True,
                "kind": "tool",
                "operation": operation,
                "verified": True,
                "content_digest": digest,
                "byte_size": len(body),
                "package_digest": release_sha256(
                    {
                        "release_id": f"{request.get('skill_id')}@{request.get('version')}",
                        "content_digest": digest,
                    }
                ),
            }
        kind = "use" if operation.startswith("skills_use_") else "feedback"
        allowed = USE_REPORT_KEYS if kind == "use" else FEEDBACK_V2_KEYS
        if operation.endswith("_status_get"):
            receipt_id = request.get("report_id") or request.get("feedback_id") or request.get("receipt_id")
            if not isinstance(receipt_id, str) or not receipt_id:
                raise ValueError("validation_failed")
            record = self._store_call(lambda: self._store.get(kind, receipt_id))
            if record is None:
                raise ValueError("not_found")
            return {
                "ok": True,
                "kind": "tool",
                "operation": operation,
                "status": "accepted",
                "receipt": dict(record),
            }
        wrapped = request.get("report") if kind == "use" else request.get("feedback")
        if isinstance(wrapped, Mapping):
            payload = dict(wrapped)
        else:
            payload = {key: request[key] for key in allowed if key in request}
        try:
            reject_forbidden_privacy(payload)
            cleaned = allowlist_and_redact(
                {k: v for k, v in payload.items() if k in allowed},
                allowed_keys=allowed,
            )
        except PayloadValidationError as exc:
            raise ValueError("validation_failed") from exc
        if kind == "use":
            report_kind = cleaned.get("report_kind")
            score = cleaned.get("score")
            if report_kind == "completed_use" and score == 10 and "issue" in cleaned:
                raise ValueError("validation_failed")
            if report_kind == "completed_use" and isinstance(score, int) and 0 <= score <= 9 and "issue" not in cleaned:
                raise ValueError("validation_failed")
            if report_kind == "non_use" and ("score" in cleaned or "issue" in cleaned):
                raise ValueError("validation_failed")
        receipt_id = str(
            cleaned.get("report_id")
            or cleaned.get("feedback_id")
            or request.get("report_id")
            or request.get("feedback_id")
            or ""
        )
        if not receipt_id:
            raise ValueError("validation_failed")
        client_key = str(request.get("client_idempotency_key") or cleaned.get("client_idempotency_key") or "")
        canonical = {k: cleaned[k] for k in sorted(cleaned) if k != "server_idempotency_key"}
        key = server_idempotency_key(
            actor_id=identity.actor_id,
            org_id=identity.org_id,
            operation=operation,
            client_key=client_key,
            canonical=canonical,
        )
        record = {
            "receipt_id": receipt_id,
            "kind": kind,
            "actor_id": identity.actor_id,
            "org_id": identity.org_id,
            "server_idempotency_key": key,
            "request_hash": key,
            "payload": canonical,
        }
        previous = self._store_call(lambda: self._store.get(kind, receipt_id))
        stored = self._store_call(lambda: self._store.put(kind, receipt_id, record))
        return {
            "ok": True,
            "kind": "tool",
            "operation": operation,
            "status": "accepted",
            "receipt_id": receipt_id,
            "server_idempotency_key": stored.get("server_idempotency_key", key),
            "replay": previous is not None,
        }

    def handle(self, request: Mapping[str, Any]) -> dict[str, Any]:
        """Handle one stateless provider request with typed fail-closed errors."""
        if request.get("protocol_version") != PROTOCOL_VERSION:
            return {"ok": False, "error": "contract_incompatible"}
        if any(key in request for key in ("session", "session_id")):
            return {"ok": False, "error": "session_not_supported"}
        operation = request.get("operation")
        if not isinstance(operation, str):
            return {"ok": False, "error": "unsupported_operation"}
        if operation.startswith(LEGACY_EXECUTION_PREFIXES):
            return {"ok": False, "error": "legacy_execution_disabled"}
        if operation not in RESOURCE_OPERATIONS + TOOLS:
            return {"ok": False, "error": "unsupported_operation"}
        try:
            identity = self._identity(request.get("authorization"))
            if operation in TOOLS:
                return self._handle_tool(operation, request, identity)
            limit = self._limit(request.get("limit", 50))
            offset = self._cursor(request.get("cursor"))
            result: dict[str, Any] = {
                "ok": True,
                "kind": "resource",
                "operation": operation,
                "contract_version": CONTRACT_VERSION,
                "snapshot_id": self._snapshot_id,
                "cursor": f"{self._snapshot_id}:{offset}",
                "limit": limit,
                "no_fallback": True,
            }
            if operation == "skills_capabilities_get":
                domain = request.get("domain")
                result.update(
                    {
                        "capabilities": {
                            "resources": True,
                            "tools": True,
                            "pagination": True,
                            "protocol": PROTOCOL_VERSION,
                            "contract_version": CONTRACT_VERSION,
                        },
                        "resources": list(self.resources()),
                        "tools": list(self.tools()),
                        "legacy_execution": False,
                    }
                )
                if domain:
                    result["domain"] = str(domain)
                    result["guide"] = {
                        "domain": str(domain),
                        "disclosure": "bounded_guide_only",
                        "bytes": None,
                    }
                return result
            if operation in {"skills_catalog_list", "skills_catalog_search"}:
                families = list(self._families)
                query = str(request.get("query", "")).strip().casefold()
                if operation == "skills_catalog_search" and query:
                    families = [
                        family
                        for family in families
                        if query
                        in " ".join(
                            str(family.get(field, ""))
                            for field in ("family_id", "display_name", "description")
                        ).casefold()
                    ]
                result.update(
                    self._page(
                        [
                            {
                                "family_id": family["family_id"],
                                "display_name": family["display_name"],
                                "description": family["description"],
                                "subcategory_count": len(family.get("subcategories", ())),
                            }
                            for family in families
                        ],
                        offset,
                        limit,
                    )
                )
                return result
            if operation == "skills_release_list":
                family_id = request.get("family_id")
                skill_id = request.get("skill_id")
                if self._has_registry and family_id and not any(
                    family.get("family_id") == family_id for family in self._families
                ):
                    return {"ok": False, "error": "not_found"}
                entries = [
                    {
                        "skill_id": release.skill_id,
                        "version": release.version,
                        "release_id": release.release_id,
                        "family_id": release.family_id,
                        "subcategory_id": release.subcategory_id,
                        "collection_id": release.collection_id,
                        "lifecycle_state": release.lifecycle_state,
                        "qualification": release.qualification,
                    }
                    for release in self._registry.values()
                    if (not family_id or release.family_id == family_id)
                    and (not skill_id or release.skill_id == skill_id)
                ]
                result.update(self._page(entries, offset, limit))
                return result
            release = self._release(request.get("skill_id"), request.get("version"))
            self._authorize_release(release, identity, request)
            if operation == "skills_release_describe":
                result.update(
                    {
                        "skill_id": request["skill_id"],
                        "version": request["version"],
                        "release_id": f"{request['skill_id']}@{request['version']}",
                    }
                )
                if release is not None:
                    result.update(
                        {
                            "family_id": release.family_id,
                            "subcategory_id": release.subcategory_id,
                            "lifecycle_state": release.lifecycle_state,
                            "qualification": release.qualification,
                            "provenance": dict(release.provenance),
                        }
                    )
                return result
            if operation == "skills_qualification_get":
                return dict(
                    result,
                    qualification=(release.qualification if release else "qualified"),
                )
            if operation in {"skills_release_resources_list", "skills_release_sections_list"}:
                descriptors = []
                if release is not None:
                    wanted_kind = "section" if operation == "skills_release_sections_list" else None
                    for resource in release.resources:
                        if wanted_kind and resource.resource_kind not in {wanted_kind, "entrypoint"}:
                            continue
                        descriptor = resource.descriptor(release.skill_id, release.version)
                        self._descriptor(descriptor)
                        descriptors.append(descriptor)
                result.update(self._page(descriptors, offset, limit))
                return result
            if operation in {
                "skills_release_entrypoint_get",
                "skills_release_section_get",
                "skills_release_resource_get",
                "skills_release_content_get",
            }:
                resource_id = request.get("resource_id") or request.get("content_id")
                if operation == "skills_release_entrypoint_get":
                    resource_id = request.get("resource_id") or "entrypoint"
                    if request.get("manifest"):
                        resource_id = "manifest"
                if operation == "skills_release_section_get":
                    resource_id = request.get("section_id") or request.get("fragment_id")
                if not isinstance(resource_id, str) or not resource_id:
                    return {"ok": False, "error": "exact_resource_required"}
                return self._resource_result(
                    operation,
                    release,
                    resource_id,
                    expected_digest=request.get("expected_digest") or request.get("content_digest"),
                )
            if operation == "skills_release_package_get":
                if release is None:
                    body = b""
                else:
                    body = b"".join(resource.body for resource in release.resources)
                digest = _digest(body)
                expected = request.get("expected_digest") or request.get("content_digest")
                if expected not in (None, "", digest):
                    raise ValueError("integrity_mismatch")
                return dict(
                    result,
                    bytes=body,
                    byte_size=len(body),
                    content_digest=digest,
                    immutable=True,
                    resource_count=0 if release is None else len(release.resources),
                )
            return {"ok": False, "error": "unsupported_operation"}
        except ValueError as exc:
            payload = {"ok": False, "error": str(exc)}
            diagnosis = getattr(exc, "diagnosis", None)
            if isinstance(diagnosis, Mapping):
                payload["store"] = {
                    "code": diagnosis.get("code"),
                    "redacted_error": diagnosis.get("redacted_error"),
                    "fail_closed": True,
                }
            return payload


def V2Provider(
    verifier: Callable[[str], TrustedIdentity] | None = None,
    *,
    catalog_version: str = "catalog-v2",
    families: Iterable[Mapping[str, Any]] | None = None,
    releases: Iterable[Any] | Mapping[str, Any] | None = None,
    contract_validator: Callable[[Mapping[str, Any]], Any] | None = None,
    store: ProviderV2Store | None = None,
    production_store: bool = False,
) -> SkillsApiV2:
    """Historical constructor used by MCP/HTTP adapters and existing tests."""
    if verifier is None:
        def _missing(_: str) -> TrustedIdentity:
            raise ValueError("verifier_required")

        verifier = _missing
    return SkillsApiV2(
        verifier=verifier,
        catalog_version=catalog_version,
        families=families,
        releases=releases,
        contract_validator=contract_validator,
        store=store,
        production_store=production_store,
    )


__all__ = [
    "CATALOG_OPERATIONS",
    "CONTRACT_VERSION",
    "InMemoryProviderStore",
    "PROTOCOL_VERSION",
    "ProviderV2Store",
    "RESOURCE_OPERATIONS",
    "SkillsApiV2",
    "TOOLS",
    "TrustedIdentity",
    "V2Provider",
    "WRITE_TOOLS",
    "diagnose_store_failure",
    "server_idempotency_key",
]
