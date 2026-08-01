"""SQLite registry for immutable bundle publication and release rows."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from .bundle import build_skill_bundle

PUBLISHER_DB_NAME = "publisher.sqlite"
DEFAULT_STATE_DIRNAME = ".linkskills-state"


def resolve_state_dir(
    *,
    repo_root: Optional[Path] = None,
    state_dir: Optional[Path] = None,
) -> Path:
    if state_dir is not None:
        return Path(state_dir).expanduser().resolve()
    env = os.environ.get("LINKSKILLS_STATE_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    root = Path(repo_root) if repo_root else Path.cwd()
    return (root / DEFAULT_STATE_DIRNAME).resolve()


def publisher_db_path(state_dir: Path) -> Path:
    return Path(state_dir) / PUBLISHER_DB_NAME


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class PublishedRelease:
    skill_id: str
    version: str
    release_hash: str
    bundle_hash: str
    channel: str
    published_at: str
    manifest: Dict[str, Any]


class PublisherRegistry:
    """Local SQLite registry for hashed bundles and release registration."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    @classmethod
    def open(cls, *, repo_root: Optional[Path] = None, state_dir: Optional[Path] = None) -> "PublisherRegistry":
        resolved = resolve_state_dir(repo_root=repo_root, state_dir=state_dir)
        return cls(publisher_db_path(resolved))

    def close(self) -> None:
        self._conn.close()

    def _ensure_schema(self) -> None:
        self._conn.executescript(
            """
            pragma journal_mode = wal;
            create table if not exists bundles (
              bundle_hash text primary key,
              skill_id text not null,
              version text not null,
              content_hash text not null,
              manifest_json text not null,
              created_at text not null
            );
            create table if not exists releases (
              skill_id text not null,
              version text not null,
              release_hash text not null,
              bundle_hash text not null references bundles(bundle_hash),
              channel text not null default 'internal',
              published_at text not null,
              metadata_json text not null default '{}',
              primary key (skill_id, version)
            );
            create index if not exists releases_hash_idx on releases (release_hash);
            """
        )
        self._conn.commit()

    def publish_release(
        self,
        skill_dir: str | Path,
        *,
        channel: str = "internal",
        metadata: Optional[Mapping[str, Any]] = None,
        transactional: bool = True,
    ) -> PublishedRelease:
        """Build bundle manifest and register release atomically."""
        manifest = build_skill_bundle(skill_dir)
        skill_id = str(manifest["skill_id"])
        version = str(manifest["version"])
        bundle_hash = str(manifest["bundle_hash"])
        content_hash = str(manifest["content_hash"])
        release_hash = bundle_hash.removeprefix("sha256:")
        published_at = _utc_now()
        meta = dict(metadata or {})

        def _write() -> PublishedRelease:
            existing = self._conn.execute(
                """
                select release_hash, bundle_hash, channel, published_at, metadata_json
                from releases
                where skill_id = ? and version = ?
                """,
                (skill_id, version),
            ).fetchone()
            if existing is not None:
                if (
                    str(existing["bundle_hash"]) == bundle_hash
                    and str(existing["release_hash"]) == release_hash
                ):
                    # Exact-content replay is idempotent.
                    return PublishedRelease(
                        skill_id=skill_id,
                        version=version,
                        release_hash=str(existing["release_hash"]),
                        bundle_hash=str(existing["bundle_hash"]),
                        channel=str(existing["channel"]),
                        published_at=str(existing["published_at"]),
                        manifest=manifest,
                    )
                raise ValueError(
                    f"immutable publish conflict: ({skill_id}, {version}) already "
                    f"published with different content "
                    f"(existing_bundle={existing['bundle_hash']}, new_bundle={bundle_hash})"
                )

            self._conn.execute(
                """
                insert into bundles (
                  bundle_hash, skill_id, version, content_hash, manifest_json, created_at
                ) values (?, ?, ?, ?, ?, ?)
                on conflict(bundle_hash) do nothing
                """,
                (
                    bundle_hash,
                    skill_id,
                    version,
                    content_hash,
                    json.dumps(manifest, sort_keys=True),
                    published_at,
                ),
            )
            self._conn.execute(
                """
                insert into releases (
                  skill_id, version, release_hash, bundle_hash, channel, published_at, metadata_json
                ) values (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    skill_id,
                    version,
                    release_hash,
                    bundle_hash,
                    channel,
                    published_at,
                    json.dumps(meta, sort_keys=True),
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

        if transactional:
            with self._conn:
                return _write()
        return _write()

    def get_release(self, skill_id: str, version: str) -> Optional[PublishedRelease]:
        row = self._conn.execute(
            """
            select r.*, b.manifest_json
            from releases r
            join bundles b on b.bundle_hash = r.bundle_hash
            where r.skill_id = ? and r.version = ?
            """,
            (skill_id, version),
        ).fetchone()
        if row is None:
            return None
        return PublishedRelease(
            skill_id=row["skill_id"],
            version=row["version"],
            release_hash=row["release_hash"],
            bundle_hash=row["bundle_hash"],
            channel=row["channel"],
            published_at=row["published_at"],
            manifest=json.loads(row["manifest_json"]),
        )

    def list_releases(self, skill_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if skill_id:
            rows = self._conn.execute(
                "select * from releases where skill_id = ? order by published_at desc",
                (skill_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "select * from releases order by published_at desc"
            ).fetchall()
        return [dict(row) for row in rows]

    def backfill_from_manifests(self, manifests: List[Mapping[str, Any]]) -> int:
        """Register pre-built bundle manifests (e.g. catalog migration)."""
        count = 0
        with self._conn:
            for manifest in manifests:
                skill_id = str(manifest["skill_id"])
                version = str(manifest["version"])
                bundle_hash = str(manifest["bundle_hash"])
                content_hash = str(manifest.get("content_hash") or bundle_hash)
                published_at = str(manifest.get("published_at") or _utc_now())
                self._conn.execute(
                    """
                    insert into bundles (
                      bundle_hash, skill_id, version, content_hash, manifest_json, created_at
                    ) values (?, ?, ?, ?, ?, ?)
                    on conflict(bundle_hash) do nothing
                    """,
                    (
                        bundle_hash,
                        skill_id,
                        version,
                        content_hash,
                        json.dumps(dict(manifest), sort_keys=True),
                        published_at,
                    ),
                )
                release_hash = bundle_hash.removeprefix("sha256:")
                self._conn.execute(
                    """
                    insert into releases (
                      skill_id, version, release_hash, bundle_hash, channel, published_at
                    ) values (?, ?, ?, ?, 'internal', ?)
                    on conflict(skill_id, version) do nothing
                    """,
                    (skill_id, version, release_hash, bundle_hash, published_at),
                )
                count += 1
        return count
