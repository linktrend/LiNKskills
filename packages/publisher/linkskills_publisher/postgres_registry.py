"""Postgres publisher registry adapter over ``lskills.releases`` / ``lskills.bundles``.

Minimal publish + get-by-hash / get-by-(skill,version) against the Phase 2
registry foundation schema. Schema differs from the local SQLite publisher
(bundles hang off ``release_id``; manifest lives in ``content_manifest``).

Selected via ``LINKSKILLS_PUBLISHER_STORE=postgres`` + database URL env vars.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from .bundle import build_skill_bundle
from .registry import PublishedRelease

try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
except ImportError:  # pragma: no cover
    psycopg = None  # type: ignore[assignment]
    dict_row = None  # type: ignore[assignment]
    Jsonb = None  # type: ignore[assignment]


DEFAULT_LIBRARIAN_ROLE = "svc_lskills_librarian"


def resolve_database_url() -> Optional[str]:
    for key in ("LINKSKILLS_DATABASE_URL", "DATABASE_URL", "LINKSKILLS_EPHEMERAL_PG_URL"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return None


def _require_psycopg() -> Any:
    if psycopg is None:
        raise ImportError(
            "psycopg (v3) is required for PostgresPublisherRegistry. "
            "Install via: pip install 'psycopg[binary]>=3.1' "
            "(listed as optional in requirements-dev.txt)."
        )
    return psycopg


def _as_jsonb(value: Any) -> Any:
    if Jsonb is None:
        return json.dumps(value)
    return Jsonb(value)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class PostgresPublisherRegistry:
    """Minimal Postgres registry: publish + get by skill/version or hash."""

    def __init__(
        self,
        dsn: str,
        *,
        role: str = DEFAULT_LIBRARIAN_ROLE,
        rls: bool = True,
        org_id: str = "publisher",
    ) -> None:
        _require_psycopg()
        self.dsn = dsn
        self.role = role
        self.rls = rls
        self.org_id = org_id
        self._lock = threading.RLock()
        self._conn = psycopg.connect(dsn, row_factory=dict_row, autocommit=False)

    @classmethod
    def open(
        cls,
        *,
        dsn: Optional[str] = None,
        org_id: str = "publisher",
    ) -> "PostgresPublisherRegistry":
        resolved = (dsn or resolve_database_url() or "").strip()
        if not resolved:
            raise ValueError(
                "PostgresPublisherRegistry requires LINKSKILLS_DATABASE_URL, "
                "DATABASE_URL, or an explicit dsn="
            )
        return cls(resolved, org_id=org_id)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def _apply_identity(self, cur: Any) -> None:
        if self.rls and self.role:
            cur.execute(f"set local role {self.role}")
        cur.execute(
            "select set_config('app.current_actor_id', %s, true)",
            ("publisher",),
        )
        cur.execute(
            "select set_config('app.current_org_id', %s, true)",
            (self.org_id,),
        )

    def publish_release(
        self,
        skill_dir: str | Path,
        *,
        channel: str = "internal",
        metadata: Optional[Mapping[str, Any]] = None,
        transactional: bool = True,
    ) -> PublishedRelease:
        """Build bundle manifest and register release + bundle atomically."""
        manifest = build_skill_bundle(skill_dir)
        skill_id = str(manifest["skill_id"])
        version = str(manifest["version"])
        bundle_hash = str(manifest["bundle_hash"])
        release_hash = bundle_hash.removeprefix("sha256:")
        published_at = _utc_now()
        meta = dict(metadata or {})

        def _write() -> PublishedRelease:
            with self._conn.cursor() as cur:
                self._apply_identity(cur)
                cur.execute(
                    """
                    select release_id, release_hash, channel, published_at, metadata
                    from lskills.releases
                    where skill_id = %s and version = %s
                    """,
                    (skill_id, version),
                )
                existing = cur.fetchone()
                if existing is not None:
                    cur.execute(
                        """
                        select bundle_hash from lskills.bundles
                        where release_id = %s
                        order by created_at asc
                        limit 1
                        """,
                        (existing["release_id"],),
                    )
                    bundle_row = cur.fetchone()
                    existing_bundle = (
                        str(bundle_row["bundle_hash"]) if bundle_row else ""
                    )
                    if (
                        existing_bundle == bundle_hash
                        and str(existing["release_hash"]) == release_hash
                    ):
                        return PublishedRelease(
                            skill_id=skill_id,
                            version=version,
                            release_hash=str(existing["release_hash"]),
                            bundle_hash=existing_bundle,
                            channel=str(existing["channel"]),
                            published_at=str(existing["published_at"]),
                            manifest=manifest,
                        )
                    raise ValueError(
                        f"immutable publish conflict: ({skill_id}, {version}) already "
                        f"published with different content "
                        f"(existing_bundle={existing_bundle}, new_bundle={bundle_hash})"
                    )

                cur.execute(
                    """
                    insert into lskills.releases (
                      skill_id, version, release_hash, channel,
                      content_manifest, published_at, metadata
                    ) values (
                      %s, %s, %s, %s::lskills.release_channel,
                      %s, %s::timestamptz, %s
                    )
                    returning release_id, published_at
                    """,
                    (
                        skill_id,
                        version,
                        release_hash,
                        channel,
                        _as_jsonb(manifest),
                        published_at,
                        _as_jsonb(meta),
                    ),
                )
                release_row = cur.fetchone()
                assert release_row is not None
                release_id = release_row["release_id"]
                cur.execute(
                    """
                    insert into lskills.bundles (
                      release_id, bundle_hash, format_profile, metadata
                    ) values (%s, %s, %s, %s)
                    """,
                    (
                        release_id,
                        bundle_hash,
                        str(manifest.get("format_profile") or "heavy"),
                        _as_jsonb({"content_hash": manifest.get("content_hash")}),
                    ),
                )
                return PublishedRelease(
                    skill_id=skill_id,
                    version=version,
                    release_hash=release_hash,
                    bundle_hash=bundle_hash,
                    channel=channel,
                    published_at=published_at,
                    manifest=manifest,
                )

        with self._lock:
            try:
                result = _write()
                if transactional:
                    self._conn.commit()
                else:
                    self._conn.commit()
                return result
            except Exception:
                self._conn.rollback()
                raise

    def get_release(self, skill_id: str, version: str) -> Optional[PublishedRelease]:
        with self._lock:
            try:
                with self._conn.cursor() as cur:
                    self._apply_identity(cur)
                    cur.execute(
                        """
                        select r.skill_id, r.version, r.release_hash, r.channel,
                               r.published_at, r.content_manifest, b.bundle_hash
                        from lskills.releases r
                        left join lateral (
                          select bundle_hash
                          from lskills.bundles
                          where release_id = r.release_id
                          order by created_at asc
                          limit 1
                        ) b on true
                        where r.skill_id = %s and r.version = %s
                        """,
                        (skill_id, version),
                    )
                    row = cur.fetchone()
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
        if row is None:
            return None
        manifest = row["content_manifest"] or {}
        if isinstance(manifest, str):
            manifest = json.loads(manifest)
        return PublishedRelease(
            skill_id=row["skill_id"],
            version=row["version"],
            release_hash=row["release_hash"],
            bundle_hash=str(row["bundle_hash"] or ""),
            channel=str(row["channel"]),
            published_at=str(row["published_at"]),
            manifest=dict(manifest),
        )

    def get_by_hash(self, release_or_bundle_hash: str) -> Optional[PublishedRelease]:
        """Lookup by ``release_hash`` or ``bundle_hash``."""
        needle = str(release_or_bundle_hash).strip()
        bare = needle.removeprefix("sha256:")
        with self._lock:
            try:
                with self._conn.cursor() as cur:
                    self._apply_identity(cur)
                    cur.execute(
                        """
                        select r.skill_id, r.version, r.release_hash, r.channel,
                               r.published_at, r.content_manifest, b.bundle_hash
                        from lskills.releases r
                        left join lateral (
                          select bundle_hash
                          from lskills.bundles
                          where release_id = r.release_id
                          order by created_at asc
                          limit 1
                        ) b on true
                        where r.release_hash in (%s, %s)
                           or b.bundle_hash in (%s, %s, %s)
                        limit 1
                        """,
                        (needle, bare, needle, bare, f"sha256:{bare}"),
                    )
                    row = cur.fetchone()
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
        if row is None:
            return None
        manifest = row["content_manifest"] or {}
        if isinstance(manifest, str):
            manifest = json.loads(manifest)
        return PublishedRelease(
            skill_id=row["skill_id"],
            version=row["version"],
            release_hash=row["release_hash"],
            bundle_hash=str(row["bundle_hash"] or ""),
            channel=str(row["channel"]),
            published_at=str(row["published_at"]),
            manifest=dict(manifest),
        )

    def list_releases(self, skill_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            try:
                with self._conn.cursor() as cur:
                    self._apply_identity(cur)
                    if skill_id:
                        cur.execute(
                            """
                            select skill_id, version, release_hash, channel, published_at
                            from lskills.releases
                            where skill_id = %s
                            order by published_at desc
                            """,
                            (skill_id,),
                        )
                    else:
                        cur.execute(
                            """
                            select skill_id, version, release_hash, channel, published_at
                            from lskills.releases
                            order by published_at desc
                            """
                        )
                    rows = cur.fetchall()
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
        return [dict(row) for row in rows]


def open_publisher_registry(
    *,
    repo_root: Optional[Path] = None,
    state_dir: Optional[Path] = None,
    dsn: Optional[str] = None,
) -> Any:
    """Open SQLite or Postgres publisher registry based on env."""
    backend = os.environ.get("LINKSKILLS_PUBLISHER_STORE", "").strip().lower()
    if backend == "postgres":
        return PostgresPublisherRegistry.open(dsn=dsn)
    from .registry import PublisherRegistry

    return PublisherRegistry.open(repo_root=repo_root, state_dir=state_dir)
