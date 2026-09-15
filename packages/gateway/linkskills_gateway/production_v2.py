"""Postgres-backed v2 runtime; publication and activation stay operator-owned."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from contextlib import contextmanager
from dataclasses import replace
from typing import Any, Mapping

from linkskills_core.provider_v2 import PROTOCOL_VERSION, RESOURCE_OPERATIONS, V2Provider, WRITE_TOOLS


def manifest_digest(value: Mapping[str, Any]) -> str:
    """Hash the immutable JSON publication document, including resource digests."""
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def decode_release(row: Mapping[str, Any]) -> dict[str, Any]:
    """Reject corrupted or unqualified publication records before serving bytes."""
    manifest = row["manifest"]
    if not isinstance(manifest, dict) or manifest_digest(manifest) != row["manifest_sha256"]:
        raise ValueError("integrity_mismatch")
    if manifest.get("qualification") != "qualified":
        raise ValueError("not_qualified")
    if row["release_id"] != f"{manifest.get('skill_id')}@{manifest.get('version')}":
        raise ValueError("integrity_mismatch")
    release = dict(manifest)
    resources = {}
    for name, resource in manifest.get("resources", {}).items():
        body = base64.b64decode(resource["content_b64"], validate=True)
        if "sha256:" + hashlib.sha256(body).hexdigest() != resource["content_digest"]:
            raise ValueError("integrity_mismatch")
        resources[name] = {**resource, "body": body}
    if not resources:
        raise ValueError("catalog_unavailable")
    release["resources"] = resources
    release["lifecycle_state"] = row["lifecycle"]
    return release


class PostgresProviderStore:
    """Open bounded transactions with verified actor/org identity and a fixed role."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    @contextmanager
    def transaction(self, *, org_id: str = "", actor_id: str = ""):
        """Never accept a caller-selected SQL role or expose connection errors."""
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(self._dsn, row_factory=dict_row, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("set local role svc_lskills_runtime")
                cur.execute("set local statement_timeout = '5s'")
                cur.execute("select set_config('app.current_org_id', %s, true)", (org_id,))
                cur.execute("select set_config('app.current_actor_id', %s, true)", (actor_id,))
                yield cur

    def probe(self) -> Mapping[str, Any]:
        """Verify all three runtime tables are reachable under the runtime role."""
        with self.transaction() as cur:
            for table in ("provider_releases", "provider_bindings", "provider_receipts"):
                cur.execute(f"select 1 from lskills.{table} limit 1")
        return {"ready": True, "code": "store_ready"}

    def snapshot(self, claims: Any) -> tuple[list[dict[str, Any]], Mapping[str, Any]]:
        """Refresh revocation and exact consumer activation on every request."""
        with self.transaction(org_id=claims.org_id, actor_id=claims.actor_id) as cur:
            cur.execute(
                "select runtime_profile, release_ids from lskills.provider_bindings "
                "where org_id=%s and actor_id=%s and runtime_binding_id=%s and enabled",
                (claims.org_id, claims.actor_id, claims.runtime_binding_id),
            )
            binding = cur.fetchone()
            if not binding or not binding["release_ids"]:
                raise ValueError("forbidden")
            cur.execute(
                "select release_id, manifest, manifest_sha256, lifecycle "
                "from lskills.provider_releases where release_id = any(%s) order by release_id",
                (binding["release_ids"],),
            )
            releases = [decode_release(row) for row in cur.fetchall()]
            if {f"{r['skill_id']}@{r['version']}" for r in releases} != set(binding["release_ids"]):
                raise ValueError("catalog_unavailable")
            return releases, binding

    def get(self, kind: str, receipt_id: str, *, org_id: str, actor_id: str):
        """Read a receipt only within the authenticated actor's organization."""
        with self.transaction(org_id=org_id, actor_id=actor_id) as cur:
            cur.execute(
                "select record from lskills.provider_receipts "
                "where org_id=%s and actor_id=%s and kind=%s and receipt_id=%s",
                (org_id, actor_id, kind, receipt_id),
            )
            row = cur.fetchone()
            return row["record"] if row else None

    def put(self, kind: str, receipt_id: str, record: Mapping[str, Any], *, org_id: str, actor_id: str):
        """Insert once; concurrent retries replay and conflicting payloads fail."""
        from psycopg.types.json import Jsonb

        if not org_id or not actor_id or record.get("org_id") != org_id or record.get("actor_id") != actor_id:
            raise ValueError("validation_failed")
        with self.transaction(org_id=org_id, actor_id=actor_id) as cur:
            cur.execute(
                "insert into lskills.provider_receipts (org_id,actor_id,kind,receipt_id,request_hash,record) "
                "values (%s,%s,%s,%s,%s,%s) on conflict do nothing",
                (org_id, actor_id, kind, receipt_id, record["request_hash"], Jsonb(dict(record))),
            )
            cur.execute(
                "select request_hash, record from lskills.provider_receipts "
                "where org_id=%s and actor_id=%s and kind=%s and receipt_id=%s",
                (org_id, actor_id, kind, receipt_id),
            )
            stored = cur.fetchone()
            if stored is None or stored["request_hash"] != record["request_hash"]:
                raise ValueError("idempotency_conflict")
            return stored["record"]


class ProductionV2Provider:
    """Share live registry, identity, and receipt behavior between HTTP and MCP."""

    def __init__(self, verifier: Any, store: PostgresProviderStore) -> None:
        self.verifier, self.store = verifier, store
        self._advertisement = V2Provider(lambda token: None)

    def resources(self):
        """Return the core resource contract."""
        return self._advertisement.resources()

    def tools(self):
        """Return the core tool contract."""
        return self._advertisement.tools()

    @property
    def catalog_ready(self) -> bool:
        """Report publication presence without exposing release bodies."""
        try:
            with self.store.transaction() as cur:
                cur.execute("select 1 from lskills.provider_releases where lifecycle='qualified' limit 1")
                return cur.fetchone() is not None
        except Exception:
            return False

    def store_status(self):
        """Return a sanitized production-store readiness result."""
        try:
            return dict(self.store.probe())
        except Exception:
            return {"ready": False, "code": "store_unavailable", "fail_closed": True}

    def handle(self, request: Mapping[str, Any]) -> dict[str, Any]:
        """Verify current identity before reading registry state or writing receipts."""
        from .v2_http import identity_from_claims

        operation = str(request.get("operation", ""))
        # Core handles protocol/legacy errors without touching the live database.
        if (operation not in self.tools() + RESOURCE_OPERATIONS
                or request.get("protocol_version") != PROTOCOL_VERSION
                or "session" in request or "session_id" in request):
            return self._advertisement.handle(request)
        token = request.get("authorization")
        if not isinstance(token, str) or not token:
            return {"ok": False, "error": "auth_required"}
        try:
            claims = self.verifier.verify(
                token if token.lower().startswith("bearer ") else f"Bearer {token}",
                request_payload={},
                required_operation="skills_feedback_submit" if operation in WRITE_TOOLS else "skills_list",
            )
            if not claims.org_id or not claims.runtime_binding_id:
                return {"ok": False, "error": "forbidden"}
        except Exception:
            return {"ok": False, "error": "auth_invalid"}
        try:
            releases, binding = self.store.snapshot(claims)
            identity = replace(
                identity_from_claims(claims),
                runtime_profiles=frozenset({binding["runtime_profile"]}),
                activated_release_ids=frozenset(binding["release_ids"]),
            )
            provider = V2Provider(
                lambda token: identity, releases=releases, store=self.store, production_store=True,
                catalog_version=manifest_digest({"releases": [
                    {"id": f"{r['skill_id']}@{r['version']}", "state": r["lifecycle_state"],
                     "resources": {k: v["content_digest"] for k, v in r["resources"].items()}}
                    for r in releases
                ]}),
            )
            return provider.handle(request)
        except ValueError as exc:
            code = str(exc)
            return {"ok": False, "error": code if code in {
                "forbidden", "catalog_unavailable", "integrity_mismatch", "not_qualified"
            } else "catalog_unavailable"}
        except Exception:
            return {"ok": False, "error": "store_unavailable"}


def production_provider(verifier: Any) -> ProductionV2Provider:
    """Require explicit Postgres configuration; never fall back to an empty fixture."""
    from .auth import AuthConfigurationError
    from .postgres_store import resolve_database_url

    dsn = resolve_database_url()
    if os.environ.get("LINKSKILLS_GATEWAY_STORE") != "postgres" or not dsn:
        raise AuthConfigurationError("production v2 requires the Postgres runtime store")
    return ProductionV2Provider(verifier, PostgresProviderStore(dsn))
