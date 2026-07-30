"""Postgres-backed review queue adapter for the Librarian domain worker.

Selected when ``LINKSKILLS_LIBRARIAN_STORE=postgres`` and a DSN is present
(``LINKSKILLS_DATABASE_URL`` / ``DATABASE_URL`` / ``LINKSKILLS_EPHEMERAL_PG_URL``).

Maps to ``lskills.review_queue`` when that table exists (additive future
migration or ephemeral test DDL). Does not invent a live migration here —
use ``tests/helpers/ephemeral_review_queue_ddl.sql`` for ephemeral proofs only.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from .store import ReviewQueueStore

try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
except ImportError:  # pragma: no cover
    psycopg = None  # type: ignore[assignment]
    dict_row = None  # type: ignore[assignment]
    Jsonb = None  # type: ignore[assignment]


REVIEW_QUEUE_TABLE = "lskills.review_queue"


def resolve_database_url() -> Optional[str]:
    for key in ("LINKSKILLS_DATABASE_URL", "DATABASE_URL", "LINKSKILLS_EPHEMERAL_PG_URL"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return None


def _require_psycopg() -> Any:
    if psycopg is None:
        raise ImportError(
            "psycopg (v3) is required for PostgresReviewQueueStore. "
            "Install via: pip install 'psycopg[binary]>=3.1' "
            "(listed as optional in requirements-dev.txt)."
        )
    return psycopg


def _as_jsonb(value: Any) -> Any:
    if Jsonb is None:
        return json.dumps(value)
    return Jsonb(value)


class PostgresReviewQueueStore:
    """ReviewQueueStore adapter over ``lskills.review_queue``."""

    def __init__(self, dsn: str, *, require_table: bool = True) -> None:
        _require_psycopg()
        self.dsn = dsn
        self._lock = threading.RLock()
        self._conn = psycopg.connect(dsn, row_factory=dict_row, autocommit=True)
        if require_table and not self.table_exists():
            raise RuntimeError(
                f"{REVIEW_QUEUE_TABLE} is not present. Apply an additive migration "
                "via LiNKplatform, or load tests/helpers/ephemeral_review_queue_ddl.sql "
                "for ephemeral proofs only."
            )

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def table_exists(self) -> bool:
        with self._lock:
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    select 1
                    from information_schema.tables
                    where table_schema = 'lskills' and table_name = 'review_queue'
                    """
                )
                return cur.fetchone() is not None

    def enqueue(self, item: Mapping[str, Any]) -> Dict[str, Any]:
        stored = dict(item)
        with self._lock:
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    insert into lskills.review_queue (
                      review_id, kind, status, payload, created_at
                    ) values (
                      %s, %s, %s, %s, coalesce(%s::timestamptz, now())
                    )
                    on conflict (review_id) do update set
                      kind = excluded.kind,
                      status = excluded.status,
                      payload = excluded.payload
                    returning review_id
                    """,
                    (
                        str(stored.get("review_id")),
                        str(stored.get("kind") or "general"),
                        str(stored.get("status") or "queued"),
                        _as_jsonb(stored),
                        stored.get("at") or stored.get("created_at"),
                    ),
                )
        return stored

    def list_queue(self, *, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock:
            with self._conn.cursor() as cur:
                if status is None:
                    cur.execute(
                        """
                        select payload from lskills.review_queue
                        order by created_at asc
                        """
                    )
                else:
                    cur.execute(
                        """
                        select payload from lskills.review_queue
                        where status = %s
                        order by created_at asc
                        """,
                        (status,),
                    )
                rows = cur.fetchall()
        out: List[Dict[str, Any]] = []
        for row in rows:
            payload = row["payload"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            out.append(dict(payload))
        return out

    def depth(self) -> int:
        with self._lock:
            with self._conn.cursor() as cur:
                cur.execute("select count(*)::int as c from lskills.review_queue")
                row = cur.fetchone()
        return int(row["c"]) if row else 0


def open_postgres_review_queue_store(
    *,
    dsn: Optional[str] = None,
    require_table: bool = True,
) -> PostgresReviewQueueStore:
    """Open a Postgres review queue; raises if DSN or table is missing."""
    resolved = (dsn or resolve_database_url() or "").strip()
    if not resolved:
        raise ValueError(
            "Postgres review queue requires LINKSKILLS_DATABASE_URL, "
            "DATABASE_URL, or an explicit dsn="
        )
    return PostgresReviewQueueStore(resolved, require_table=require_table)
