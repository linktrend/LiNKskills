"""Postgres-backed review queue adapter for the Librarian domain worker.

Selected when ``LINKSKILLS_LIBRARIAN_STORE=postgres`` and a DSN is present
(``LINKSKILLS_DATABASE_URL`` / ``DATABASE_URL`` / ``LINKSKILLS_EPHEMERAL_PG_URL``).

Maps to ``lskills.review_queue`` from migrations
``20260730_000008_lskills_review_queue.sql`` +
``20260730_000009_lskills_review_queue_actor_isolation.sql``
(additive; LiNKplatform applies live).

RLS identity is applied per transaction with:
  SET LOCAL ROLE svc_lskills_librarian;
  SET LOCAL via set_config('app.current_actor_id', ..., true);
  SET LOCAL via set_config('app.current_org_id', ..., true);

Actor/org GUCs are derived exclusively from ``bind_identity`` /
``identity()``. ``enqueue()`` stamps row ownership from that bound
context and rejects any non-empty item ``actor_id`` / ``org_id`` that
disagrees. Item fields never set RLS GUCs.

Default service scope is ``actor`` (actor + org isolation). Privileged
Librarian workers that must see/claim across actors within one org must
pass ``service_scope="org"`` (or env ``LINKSKILLS_LIBRARIAN_SERVICE_SCOPE=org``),
which sets transaction-local ``app.librarian_service_scope=org``. Runtime
role never receives this privilege. Privileged scope does not relax
enqueue identity honesty — forged item actor/org still fail.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Mapping, Optional, Tuple

try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
except ImportError:  # pragma: no cover
    psycopg = None  # type: ignore[assignment]
    dict_row = None  # type: ignore[assignment]
    Jsonb = None  # type: ignore[assignment]


REVIEW_QUEUE_TABLE = "lskills.review_queue"
DEFAULT_LIBRARIAN_ROLE = "svc_lskills_librarian"
ACTIVE_STATUSES = ("queued", "claimed", "in_progress", "failed")
ALLOWED_SERVICE_SCOPES = frozenset({"actor", "org"})


def resolve_librarian_service_scope(
    explicit: Optional[str] = None,
) -> str:
    """Resolve Librarian RLS service scope (default actor isolation).

    ``org`` is the explicit privileged cross-actor-within-org gate matching
    migration 000009 ``app.librarian_service_scope=org``.
    """
    raw = (
        explicit
        if explicit is not None
        else os.environ.get("LINKSKILLS_LIBRARIAN_SERVICE_SCOPE", "")
    )
    scope = str(raw or "actor").strip().lower() or "actor"
    if scope not in ALLOWED_SERVICE_SCOPES:
        raise ValueError(
            "LINKSKILLS_LIBRARIAN_SERVICE_SCOPE / service_scope must be "
            f"'actor' or 'org' (got {scope!r})"
        )
    return scope



def resolve_database_url() -> Optional[str]:
    for key in (
        "LINKSKILLS_DATABASE_URL",
        "DATABASE_URL",
        "LINKSKILLS_STORE_URL",
        "LINKSKILLS_POSTGRES_URL",
        "LINKSKILLS_EPHEMERAL_PG_URL",
    ):
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


def _payload_dict(row: Mapping[str, Any]) -> Dict[str, Any]:
    """Rebuild Protocol-compatible item from a review_queue row."""
    payload = row.get("payload") or {}
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        payload = {"raw": payload}
    item = dict(payload)
    item["review_id"] = str(row.get("review_id") or item.get("review_id") or "")
    item["kind"] = str(row.get("kind") or item.get("kind") or "general")
    item["status"] = str(row.get("status") or item.get("status") or "queued")
    item["actor_id"] = str(row.get("actor_id") or item.get("actor_id") or "")
    item["org_id"] = str(row.get("org_id") or item.get("org_id") or "")
    provenance = row.get("provenance")
    if isinstance(provenance, str):
        provenance = json.loads(provenance)
    if provenance is not None:
        item["provenance"] = dict(provenance) if isinstance(provenance, dict) else provenance
    if row.get("idempotency_key"):
        item["idempotency_key"] = row["idempotency_key"]
    if row.get("attempt_count") is not None:
        item["attempt_count"] = int(row["attempt_count"])
    if row.get("dead_letter_reason"):
        item["dead_letter_reason"] = row["dead_letter_reason"]
    if row.get("last_error"):
        item["last_error"] = row["last_error"]
    created = row.get("created_at")
    if created is not None and "at" not in item:
        item["at"] = created.strftime("%Y-%m-%dT%H:%M:%SZ") if hasattr(created, "strftime") else str(created)
    return item


class PostgresReviewQueueStore:
    """ReviewQueueStore adapter over ``lskills.review_queue`` (000008+000009)."""

    def __init__(
        self,
        dsn: str,
        *,
        require_table: bool = True,
        role: str = DEFAULT_LIBRARIAN_ROLE,
        rls: bool = True,
        service_scope: Optional[str] = None,
    ) -> None:
        _require_psycopg()
        self.dsn = dsn
        self.role = role
        self.rls = rls
        self.service_scope = resolve_librarian_service_scope(service_scope)
        self._lock = threading.RLock()
        self._conn = psycopg.connect(dsn, row_factory=dict_row, autocommit=False)
        self._identity = threading.local()
        if require_table and not self.table_exists():
            raise RuntimeError(
                f"{REVIEW_QUEUE_TABLE} is not present. Apply additive migrations "
                "20260730_000008_lskills_review_queue.sql and "
                "20260730_000009_lskills_review_queue_actor_isolation.sql "
                "via LiNKplatform (ephemeral proofs load those migration files)."
            )

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def bind_identity(self, actor_id: str, org_id: str) -> None:
        self._identity.actor_id = str(actor_id)
        self._identity.org_id = str(org_id or "")

    def clear_identity(self) -> None:
        self._identity.actor_id = None
        self._identity.org_id = None

    @contextmanager
    def identity(self, actor_id: str, org_id: str) -> Iterator["PostgresReviewQueueStore"]:
        previous = (
            getattr(self._identity, "actor_id", None),
            getattr(self._identity, "org_id", None),
        )
        self.bind_identity(actor_id, org_id)
        try:
            yield self
        finally:
            if previous[0] is None:
                self.clear_identity()
            else:
                self.bind_identity(str(previous[0]), str(previous[1] or ""))

    def _current_identity(self) -> Tuple[str, str]:
        """Return bound RLS identity only — never item/request fields."""
        bound_actor = getattr(self._identity, "actor_id", None)
        bound_org = getattr(self._identity, "org_id", None)
        return str(bound_actor or ""), str(bound_org or "")

    def _require_bound_identity(self) -> Tuple[str, str]:
        """Fail closed when enqueue/mutate paths lack bind_identity / identity()."""
        actor_id, org_id = self._current_identity()
        if not actor_id or not org_id:
            raise ValueError(
                "review_queue requires bound identity via bind_identity / "
                "identity(); actor_id and org_id must not be taken from "
                "untrusted item fields"
            )
        return actor_id, org_id

    def _assert_item_identity_agrees(
        self,
        item: Mapping[str, Any],
        *,
        bound_actor: str,
        bound_org: str,
    ) -> None:
        """Reject item actor/org that disagree with the bound identity.

        Omitted or empty item identity fields are allowed; bound identity is
        stamped onto the stored row. Non-empty values must match exactly.
        """
        item_actor = str(item.get("actor_id") or "").strip()
        item_org = str(item.get("org_id") or "").strip()
        if item_actor and item_actor != bound_actor:
            raise ValueError(
                f"review_queue item actor_id {item_actor!r} disagrees with "
                f"bound identity actor_id {bound_actor!r}"
            )
        if item_org and item_org != bound_org:
            raise ValueError(
                f"review_queue item org_id {item_org!r} disagrees with "
                f"bound identity org_id {bound_org!r}"
            )

    def _tx_idle(self) -> bool:
        status = self._conn.info.transaction_status
        idle = getattr(psycopg.pq, "TransactionStatus", None)
        if idle is not None:
            return status == idle.IDLE
        return int(status) == 0

    def _apply_session_identity(self, cur: Any, *, actor_id: str, org_id: str) -> None:
        if self.rls and self.role:
            cur.execute(f"set local role {self.role}")
        cur.execute(
            "select set_config('app.current_actor_id', %s, true)",
            (actor_id,),
        )
        cur.execute(
            "select set_config('app.current_org_id', %s, true)",
            (org_id,),
        )
        # Privileged org-wide claim path is explicit and transaction-local.
        # Default '' keeps actor+org isolation from migration 000009.
        scope_value = "org" if self.service_scope == "org" else ""
        cur.execute(
            "select set_config('app.librarian_service_scope', %s, true)",
            (scope_value,),
        )

    def _begin(self, *, actor_id: str, org_id: str) -> Any:
        if not self._tx_idle():
            self._conn.rollback()
        cur = self._conn.cursor()
        self._apply_session_identity(cur, actor_id=actor_id, org_id=org_id)
        return cur

    def table_exists(self) -> bool:
        with self._lock:
            if not self._tx_idle():
                self._conn.rollback()
            with self._conn.cursor() as cur:
                cur.execute(
                    """
                    select 1
                    from information_schema.tables
                    where table_schema = 'lskills' and table_name = 'review_queue'
                    """
                )
                found = cur.fetchone() is not None
            self._conn.commit()
            return found

    def probe_reachable(self) -> bool:
        with self._lock:
            if not self._tx_idle():
                self._conn.rollback()
            with self._conn.cursor() as cur:
                cur.execute("select 1")
                cur.fetchone()
            self._conn.commit()
        return True

    def enqueue(self, item: Mapping[str, Any]) -> Dict[str, Any]:
        stored = dict(item)
        review_id = str(stored.get("review_id") or uuid.uuid4())
        stored["review_id"] = review_id
        # RLS GUCs and row ownership come only from bind_identity / identity().
        # Item actor_id/org_id are never trusted for GUC setting.
        actor_id, org_id = self._require_bound_identity()
        self._assert_item_identity_agrees(
            stored, bound_actor=actor_id, bound_org=org_id
        )
        stored["actor_id"] = actor_id
        stored["org_id"] = org_id
        kind = str(stored.get("kind") or "general")
        status = str(stored.get("status") or "queued")
        provenance = stored.get("provenance")
        if provenance is None and isinstance(stored.get("payload"), Mapping):
            provenance = stored["payload"].get("provenance")  # type: ignore[index]
        provenance = dict(provenance) if isinstance(provenance, Mapping) else {}
        idempotency_key = stored.get("idempotency_key")
        idempotency_key = str(idempotency_key) if idempotency_key else None
        request_hash = str(stored.get("request_hash") or "")
        retain_until = stored.get("retain_until")
        with self._lock:
            try:
                cur = self._begin(actor_id=actor_id, org_id=org_id)
                if idempotency_key:
                    cur.execute(
                        """
                        select review_id, org_id, actor_id, kind, status, payload,
                               provenance, idempotency_key, attempt_count,
                               last_error, dead_letter_reason, created_at
                        from lskills.review_queue
                        where org_id = %s and actor_id = %s and idempotency_key = %s
                        """,
                        (org_id, actor_id, idempotency_key),
                    )
                    existing = cur.fetchone()
                    if existing is not None:
                        self._conn.commit()
                        return _payload_dict(existing)
                cur.execute(
                    """
                    insert into lskills.review_queue (
                      review_id, org_id, actor_id, kind, status, payload,
                      provenance, idempotency_key, request_hash, retain_until,
                      created_at
                    ) values (
                      %s, %s, %s, %s, %s::lskills.review_queue_status, %s,
                      %s, %s, %s, %s::timestamptz,
                      coalesce(%s::timestamptz, now())
                    )
                    on conflict (review_id) do update set
                      kind = excluded.kind,
                      status = excluded.status,
                      payload = excluded.payload,
                      provenance = excluded.provenance,
                      updated_at = now()
                    returning review_id, org_id, actor_id, kind, status, payload,
                              provenance, idempotency_key, attempt_count, created_at
                    """,
                    (
                        review_id,
                        org_id,
                        actor_id,
                        kind,
                        status,
                        _as_jsonb(stored),
                        _as_jsonb(provenance),
                        idempotency_key,
                        request_hash,
                        retain_until,
                        stored.get("at") or stored.get("created_at"),
                    ),
                )
                row = cur.fetchone()
                self._conn.commit()
                if row is not None:
                    return _payload_dict(row)
            except Exception:
                try:
                    self._conn.rollback()
                except Exception:  # pragma: no cover
                    pass
                raise
        return stored

    def list_queue(self, *, status: Optional[str] = None) -> List[Dict[str, Any]]:
        actor_id, org_id = self._current_identity()
        with self._lock:
            try:
                cur = self._begin(actor_id=actor_id, org_id=org_id)
                if status is None:
                    cur.execute(
                        """
                        select review_id, org_id, actor_id, kind, status, payload,
                               provenance, idempotency_key, attempt_count,
                               last_error, dead_letter_reason, created_at
                        from lskills.review_queue
                        order by created_at asc
                        """
                    )
                else:
                    cur.execute(
                        """
                        select review_id, org_id, actor_id, kind, status, payload,
                               provenance, idempotency_key, attempt_count,
                               last_error, dead_letter_reason, created_at
                        from lskills.review_queue
                        where status = %s::lskills.review_queue_status
                        order by created_at asc
                        """,
                        (status,),
                    )
                rows = cur.fetchall()
                self._conn.commit()
            except Exception:
                try:
                    self._conn.rollback()
                except Exception:  # pragma: no cover
                    pass
                raise
        return [_payload_dict(row) for row in rows]

    def depth(self) -> int:
        actor_id, org_id = self._current_identity()
        with self._lock:
            try:
                cur = self._begin(actor_id=actor_id, org_id=org_id)
                cur.execute(
                    """
                    select count(*)::int as c
                    from lskills.review_queue
                    where status = any(%s::lskills.review_queue_status[])
                    """,
                    (list(ACTIVE_STATUSES),),
                )
                row = cur.fetchone()
                self._conn.commit()
            except Exception:
                try:
                    self._conn.rollback()
                except Exception:  # pragma: no cover
                    pass
                raise
        return int(row["c"]) if row else 0

    def mark_failed(
        self,
        review_id: str,
        *,
        error: str,
        dead_letter: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Increment attempt; move to failed or dead_letter when exhausted."""
        actor_id, org_id = self._current_identity()
        with self._lock:
            try:
                cur = self._begin(actor_id=actor_id, org_id=org_id)
                cur.execute(
                    """
                    select attempt_count, max_attempts, status
                    from lskills.review_queue
                    where review_id = %s
                    for update
                    """,
                    (review_id,),
                )
                row = cur.fetchone()
                if row is None:
                    self._conn.rollback()
                    return None
                attempts = int(row["attempt_count"] or 0) + 1
                max_attempts = int(row["max_attempts"] or 5)
                to_dead = dead_letter or attempts >= max_attempts
                new_status = "dead_letter" if to_dead else "failed"
                cur.execute(
                    """
                    update lskills.review_queue
                    set status = %s::lskills.review_queue_status,
                        attempt_count = %s,
                        last_error = %s,
                        dead_letter_reason = case
                          when %s then coalesce(dead_letter_reason, %s)
                          else dead_letter_reason
                        end,
                        next_attempt_at = case
                          when %s then null
                          else now() + make_interval(secs => least(300, 5 * %s))
                        end,
                        updated_at = now(),
                        completed_at = case when %s then now() else completed_at end
                    where review_id = %s
                    returning review_id, org_id, actor_id, kind, status, payload,
                              provenance, attempt_count, last_error,
                              dead_letter_reason, created_at
                    """,
                    (
                        new_status,
                        attempts,
                        error,
                        to_dead,
                        error,
                        to_dead,
                        attempts,
                        to_dead,
                        review_id,
                    ),
                )
                updated = cur.fetchone()
                self._conn.commit()
                return _payload_dict(updated) if updated else None
            except Exception:
                try:
                    self._conn.rollback()
                except Exception:  # pragma: no cover
                    pass
                raise

    def recover_expired_leases(self) -> int:
        """Return claimed/in_progress rows with expired leases to queued."""
        actor_id, org_id = self._current_identity()
        with self._lock:
            try:
                cur = self._begin(actor_id=actor_id, org_id=org_id)
                cur.execute(
                    """
                    update lskills.review_queue
                    set status = 'queued'::lskills.review_queue_status,
                        claimed_by = null,
                        claimed_at = null,
                        lease_expires_at = null,
                        updated_at = now()
                    where status in (
                      'claimed'::lskills.review_queue_status,
                      'in_progress'::lskills.review_queue_status
                    )
                      and lease_expires_at is not null
                      and lease_expires_at < now()
                    """
                )
                count = cur.rowcount
                self._conn.commit()
                return int(count)
            except Exception:
                try:
                    self._conn.rollback()
                except Exception:  # pragma: no cover
                    pass
                raise


def open_postgres_review_queue_store(
    *,
    dsn: Optional[str] = None,
    require_table: bool = True,
    rls: bool = True,
    service_scope: Optional[str] = None,
) -> PostgresReviewQueueStore:
    """Open a Postgres review queue; raises if DSN or table is missing.

    ``service_scope`` defaults to actor isolation. Pass ``\"org\"`` (or set
    ``LINKSKILLS_LIBRARIAN_SERVICE_SCOPE=org``) only for approved Librarian
    service workers that must process the org-wide queue.
    """
    resolved = (dsn or resolve_database_url() or "").strip()
    if not resolved:
        raise ValueError(
            "Postgres review queue requires LINKSKILLS_DATABASE_URL, "
            "DATABASE_URL, or an explicit dsn="
        )
    return PostgresReviewQueueStore(
        resolved,
        require_table=require_table,
        rls=rls,
        service_scope=service_scope,
    )
