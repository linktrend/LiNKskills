"""Persistent review queue for the Librarian domain worker."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Protocol, runtime_checkable

DEFAULT_STATE_DIRNAME = ".linkskills-state"
LIBRARIAN_DB_NAME = "librarian.sqlite"


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


def librarian_db_path(state_dir: Path) -> Path:
    return Path(state_dir) / LIBRARIAN_DB_NAME


@runtime_checkable
class ReviewQueueStore(Protocol):
    def enqueue(self, item: Mapping[str, Any]) -> Dict[str, Any]:
        ...

    def list_queue(self, *, status: Optional[str] = None) -> List[Dict[str, Any]]:
        ...

    def depth(self) -> int:
        ...


class InMemoryReviewQueueStore:
    def __init__(self) -> None:
        self._queue: List[Dict[str, Any]] = []

    def enqueue(self, item: Mapping[str, Any]) -> Dict[str, Any]:
        stored = dict(item)
        self._queue.append(stored)
        return stored

    def list_queue(self, *, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if status is None:
            return [dict(item) for item in self._queue]
        return [dict(item) for item in self._queue if item.get("status") == status]

    def depth(self) -> int:
        return len(self._queue)


class SqliteReviewQueueStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def close(self) -> None:
        self._conn.close()

    def _ensure_schema(self) -> None:
        self._conn.executescript(
            """
            pragma journal_mode = wal;
            create table if not exists review_queue (
              review_id text primary key,
              kind text not null,
              status text not null default 'queued',
              payload_json text not null,
              created_at text not null
            );
            create index if not exists review_queue_status_idx on review_queue (status);
            """
        )
        self._conn.commit()

    def enqueue(self, item: Mapping[str, Any]) -> Dict[str, Any]:
        stored = dict(item)
        self._conn.execute(
            """
            insert into review_queue (review_id, kind, status, payload_json, created_at)
            values (?, ?, ?, ?, ?)
            """,
            (
                str(stored.get("review_id")),
                str(stored.get("kind") or "general"),
                str(stored.get("status") or "queued"),
                json.dumps(stored, sort_keys=True),
                str(stored.get("at") or stored.get("created_at") or ""),
            ),
        )
        self._conn.commit()
        return stored

    def list_queue(self, *, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if status is None:
            rows = self._conn.execute(
                "select payload_json from review_queue order by created_at asc"
            ).fetchall()
        else:
            rows = self._conn.execute(
                "select payload_json from review_queue where status = ? order by created_at asc",
                (status,),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def depth(self) -> int:
        row = self._conn.execute("select count(*) as c from review_queue").fetchone()
        return int(row["c"]) if row else 0


def open_review_queue_store(
    *,
    repo_root: Optional[Path] = None,
    state_dir: Optional[Path] = None,
    store_path: Optional[Path] = None,
) -> ReviewQueueStore:
    if store_path is not None:
        return SqliteReviewQueueStore(store_path)
    if state_dir is not None or os.environ.get("LINKSKILLS_LIBRARIAN_DURABLE", "").strip() in {
        "1",
        "true",
        "yes",
    }:
        resolved = resolve_state_dir(repo_root=repo_root, state_dir=state_dir)
        return SqliteReviewQueueStore(librarian_db_path(resolved))
    return InMemoryReviewQueueStore()
