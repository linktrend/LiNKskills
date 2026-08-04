#!/usr/bin/env python3
"""Native Postgres proofs under restricted svc_lskills_gateway (no BYPASSRLS).

Reproduces the stage DSN shape: connect as svc_lskills_gateway (LOGIN,
NOSUPERUSER, NOBYPASSRLS), SET LOCAL ROLE svc_lskills_runtime, bind PACI
actor/org GUCs. Admin/superuser DSN is used only for schema apply and asserts.

Enabled when LINKSKILLS_EPHEMERAL_PG_URL / LINKSKILLS_TEST_PG_DSN is set, or
Docker is available and LINKSKILLS_TEST_PG_DOCKER is not skip/0.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import unittest
import uuid
from pathlib import Path
from urllib.parse import quote, urlparse, urlunparse

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "gateway"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "core"))

MIGRATIONS = REPO_ROOT / "supabase" / "migrations"
FOUNDATION_SQL = MIGRATIONS / "20260727_000005_lskills_registry_foundation.sql"
UPGRADE_SQL = MIGRATIONS / "20260728_000006_lskills_rls_actor_org_scope.sql"
GATEWAY_SQL = MIGRATIONS / "20260730_000007_lskills_gateway_persistence.sql"
GATEWAY_ROLE_SQL = MIGRATIONS / "20260804_000011_lskills_gateway_role_rls_contract.sql"

GATEWAY_PASSWORD = "gw-test-not-for-prod"
GATEWAY_ROLE = "svc_lskills_gateway"

BOOTSTRAP_SQL = """
create extension if not exists "pgcrypto";
create schema if not exists platform;
create schema if not exists lskills;
create table if not exists platform.organizations (
  id uuid primary key default gen_random_uuid()
);
do $$
begin
  if not exists (
    select 1 from pg_type
    where typname = 'member_role' and typnamespace = 'platform'::regnamespace
  ) then
    create type platform.member_role as enum ('viewer', 'member', 'admin');
  end if;
end $$;
do $$
begin
  if not exists (
    select 1 from pg_type
    where typname = 'certification_state' and typnamespace = 'lskills'::regnamespace
  ) then
    create type lskills.certification_state as enum (
      'draft', 'eval_pending', 'usable', 'deprecated'
    );
  end if;
end $$;
create or replace function platform.has_org_access(org uuid, min_role platform.member_role)
returns boolean language sql stable as $$ select true $$;
"""


def _import_psycopg():
    try:
        import psycopg  # type: ignore

        return psycopg
    except ImportError:
        return None


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def _resolve_dsn() -> str | None:
    for key in ("LINKSKILLS_EPHEMERAL_PG_URL", "LINKSKILLS_TEST_PG_DSN"):
        env = os.environ.get(key, "").strip()
        if env:
            return env
    return None


def _explicitly_enabled() -> bool:
    if _resolve_dsn():
        return True
    flag = os.environ.get("LINKSKILLS_TEST_PG_DOCKER", "").strip().lower()
    if flag in {"0", "false", "no", "skip", "off"}:
        return False
    if flag in {"1", "true", "yes"}:
        return _docker_available()
    return _docker_available()


def _should_use_docker() -> bool:
    return _resolve_dsn() is None and _explicitly_enabled() and _docker_available()


def _free_host_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _start_docker_postgres() -> tuple[str, str]:
    container_id = f"linkskills-gw-rls-{uuid.uuid4().hex[:8]}"
    host_port = _free_host_port()
    dsn = f"postgresql://postgres:postgres@127.0.0.1:{host_port}/linkskills_gw_rls"
    started = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            container_id,
            "-e",
            "POSTGRES_PASSWORD=postgres",
            "-e",
            "POSTGRES_DB=linkskills_gw_rls",
            "-p",
            f"{host_port}:5432",
            "postgres:16-alpine",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if started.returncode != 0:
        raise unittest.SkipTest(f"docker run failed: {started.stderr}")
    psycopg = _import_psycopg()
    assert psycopg is not None
    last_err: Exception | None = None
    for _ in range(60):
        probe = subprocess.run(
            [
                "docker",
                "exec",
                container_id,
                "pg_isready",
                "-U",
                "postgres",
                "-d",
                "linkskills_gw_rls",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            try:
                with psycopg.connect(dsn, autocommit=True) as conn:
                    with conn.cursor() as cur:
                        cur.execute("select 1")
                return dsn, container_id
            except Exception as exc:  # noqa: BLE001
                last_err = exc
        time.sleep(0.5)
    subprocess.run(["docker", "rm", "-f", container_id], check=False)
    raise unittest.SkipTest(f"docker postgres failed to become ready: {last_err}")


def _strip_verification(sql: str) -> str:
    if "verification helpers" in sql:
        return sql.split("-- verification helpers", 1)[0]
    return sql


def _rewrite_user(dsn: str, *, user: str, password: str) -> str:
    parsed = urlparse(dsn)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 5432
    db = (parsed.path or "/postgres").lstrip("/") or "postgres"
    netloc = f"{quote(user)}:{quote(password)}@{host}:{port}"
    return urlunparse(("postgresql", netloc, f"/{db}", "", "", ""))


@unittest.skipUnless(
    _explicitly_enabled(),
    "Postgres DSN unset and Docker unavailable/disabled "
    "(set LINKSKILLS_EPHEMERAL_PG_URL / LINKSKILLS_TEST_PG_DSN, or enable Docker)",
)
class GatewayRestrictedRoleRlsEphemeralTests(unittest.TestCase):
    """Stage-shaped RLS proofs under svc_lskills_gateway LOGIN (no BYPASSRLS)."""

    _container_id: str | None = None
    admin_dsn: str
    gateway_dsn: str
    psycopg: object

    @classmethod
    def setUpClass(cls) -> None:
        cls._container_id = None
        psycopg = _import_psycopg()
        if psycopg is None:
            raise unittest.SkipTest("psycopg required")
        cls.psycopg = psycopg
        dsn = _resolve_dsn()
        if dsn is None and _should_use_docker():
            dsn, cls._container_id = _start_docker_postgres()
        if not dsn:
            raise unittest.SkipTest("no postgres DSN")
        cls.admin_dsn = dsn
        cls.gateway_dsn = _rewrite_user(
            dsn, user=GATEWAY_ROLE, password=GATEWAY_PASSWORD
        )

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._container_id:
            subprocess.run(["docker", "rm", "-f", cls._container_id], check=False)

    def _apply_schema(self) -> None:
        with self.psycopg.connect(self.admin_dsn, autocommit=True) as conn:  # type: ignore[attr-defined]
            with conn.cursor() as cur:
                cur.execute("drop schema if exists lskills cascade;")
                # Keep gateway role across setUp cycles — DROP ROLE fails once
                # CONNECT / membership dependencies exist. Reconfigure in place.
                cur.execute(
                    f"""
                    do $$ begin
                      if exists (select 1 from pg_roles where rolname = '{GATEWAY_ROLE}') then
                        revoke all on schema public from {GATEWAY_ROLE};
                      end if;
                    end $$;
                    """
                )
                cur.execute(BOOTSTRAP_SQL)
                for path in (FOUNDATION_SQL, UPGRADE_SQL, GATEWAY_SQL, GATEWAY_ROLE_SQL):
                    cur.execute(_strip_verification(path.read_text(encoding="utf-8")))
                # Promote gateway group role to LOGIN for DSN proofs (Platform
                # owns LOGIN on stage; migration creates NOLOGIN when absent).
                # ALTER ROLE ... PASSWORD does not accept query parameters.
                cur.execute(
                    f"""
                    alter role {GATEWAY_ROLE} login password '{GATEWAY_PASSWORD}'
                      nosuperuser nobypassrls nocreatedb nocreaterole
                    """
                )
                cur.execute("select current_database()")
                dbname = cur.fetchone()[0]
                cur.execute(f'grant connect on database "{dbname}" to {GATEWAY_ROLE}')
                cur.execute(f"grant usage on schema lskills to {GATEWAY_ROLE}")
                # Assert no BYPASSRLS and runtime membership from 000011.
                cur.execute(
                    """
                    select rolbypassrls, rolcanlogin,
                      exists (
                        select 1 from pg_auth_members m
                        join pg_roles g on g.oid = m.roleid
                        where m.member = r.oid and g.rolname = 'svc_lskills_runtime'
                      ) as has_runtime
                    from pg_roles r
                    where rolname = %s
                    """,
                    (GATEWAY_ROLE,),
                )
                row = cur.fetchone()
                assert row is not None
                bypass, can_login, has_runtime = row[0], row[1], row[2]
                assert bypass is False
                assert can_login is True
                assert has_runtime is True

    def setUp(self) -> None:
        self._apply_schema()

    def _admin_count(
        self,
        table: str,
        *,
        actor_id: str | None = None,
        org_id: str | None = None,
        key: str | None = None,
    ) -> int:
        clauses: list[str] = []
        params: list[object] = []
        if actor_id is not None:
            clauses.append("actor_id = %s")
            params.append(actor_id)
        if org_id is not None:
            clauses.append("org_id = %s")
            params.append(org_id)
        if key is not None:
            clauses.append("idempotency_key = %s")
            params.append(key)
        where = (" where " + " and ".join(clauses)) if clauses else ""
        with self.psycopg.connect(self.admin_dsn, autocommit=True) as conn:  # type: ignore[attr-defined]
            with conn.cursor() as cur:
                cur.execute(
                    f"select count(*)::int from lskills.{table}{where}",
                    params,
                )
                row = cur.fetchone()
                return int(row[0])

    def _open_store(self):
        from linkskills_gateway.postgres_store import PostgresGatewayStore

        return PostgresGatewayStore(
            self.gateway_dsn, rls=True, role="svc_lskills_runtime"
        )

    def test_restricted_role_idempotency_insert_success(self) -> None:
        store = self._open_store()
        try:
            with store.identity("actor-a", "org-a"):
                reserved = store.reserve_idempotency(
                    "actor-a", "skills_run_start", "k-ok", "h-ok"
                )
                self.assertEqual(reserved.outcome, "reserved")
            self.assertEqual(
                self._admin_count(
                    "idempotency", actor_id="actor-a", org_id="org-a", key="k-ok"
                ),
                1,
            )
        finally:
            store.close()

    def test_restricted_role_atomic_start_update_complete(self) -> None:
        from linkskills_gateway.service import SkillRun

        store = self._open_store()
        run_id = str(uuid.uuid4())
        try:
            with store.identity("actor-a", "org-a"):

                def start():
                    store.save_run(
                        SkillRun(
                            run_id=run_id,
                            skill_id="demo",
                            version="1.0.0",
                            release_hash="rel",
                            profile_hash="prof",
                            actor_id="actor-a",
                            org_id="org-a",
                            status="started",
                            created_at="2026-08-04T00:00:00Z",
                            updated_at="2026-08-04T00:00:00Z",
                        )
                    )
                    return {"operation": "skills_run_start", "data": {"run_id": run_id}}

                started = store.run_atomic_idempotent(
                    "actor-a", "skills_run_start", "k-start", "h-start", start
                )
                self.assertEqual(started.outcome, "replay")
                self.assertEqual(store.get_run(run_id)["status"], "started")

                def update():
                    store.save_run(
                        SkillRun(
                            run_id=run_id,
                            skill_id="demo",
                            version="1.0.0",
                            release_hash="rel",
                            profile_hash="prof",
                            actor_id="actor-a",
                            org_id="org-a",
                            status="in_progress",
                            created_at="2026-08-04T00:00:00Z",
                            updated_at="2026-08-04T00:01:00Z",
                        )
                    )
                    return {"operation": "skills_run_update", "data": {"run_id": run_id}}

                updated = store.run_atomic_idempotent(
                    "actor-a", "skills_run_update", "k-upd", "h-upd", update
                )
                self.assertEqual(updated.outcome, "replay")
                self.assertEqual(store.get_run(run_id)["status"], "in_progress")

                def complete():
                    store.save_run(
                        SkillRun(
                            run_id=run_id,
                            skill_id="demo",
                            version="1.0.0",
                            release_hash="rel",
                            profile_hash="prof",
                            actor_id="actor-a",
                            org_id="org-a",
                            status="completed",
                            created_at="2026-08-04T00:00:00Z",
                            updated_at="2026-08-04T00:02:00Z",
                            outcome={"ok": True},
                        )
                    )
                    return {
                        "operation": "skills_run_complete",
                        "data": {"run_id": run_id, "status": "completed"},
                    }

                completed = store.run_atomic_idempotent(
                    "actor-a", "skills_run_complete", "k-done", "h-done", complete
                )
                self.assertEqual(completed.outcome, "replay")
                self.assertEqual(store.get_run(run_id)["status"], "completed")
                store.append_event(
                    {
                        "type": "run_completed",
                        "run_id": run_id,
                        "actor_id": "actor-a",
                        "org_id": "org-a",
                    }
                )
            self.assertEqual(
                self._admin_count("skill_runs", actor_id="actor-a", org_id="org-a"), 1
            )
            self.assertEqual(
                self._admin_count("gateway_events", actor_id="actor-a", org_id="org-a"),
                1,
            )
            self.assertEqual(
                self._admin_count("idempotency", actor_id="actor-a", org_id="org-a"), 3
            )
        finally:
            store.close()

    def test_denied_missing_and_partial_identity(self) -> None:
        store = self._open_store()
        try:
            with self.assertRaises(ValueError) as missing:
                store.reserve_idempotency("actor-a", "op", "k-miss", "h1")
            self.assertIn("postgres RLS requires", str(missing.exception))

            store.bind_identity("actor-a", "")
            with self.assertRaises(ValueError) as empty_org:
                store.reserve_idempotency("actor-a", "op", "k-org", "h1")
            self.assertIn("postgres RLS requires", str(empty_org.exception))
            store.clear_identity()

            store.bind_identity("", "org-a")
            with self.assertRaises(ValueError) as empty_actor:
                store.reserve_idempotency("actor-a", "op", "k-actor", "h1")
            self.assertIn("postgres RLS requires", str(empty_actor.exception))
            store.clear_identity()

            with self.assertRaises(ValueError):
                with store.identity("actor-a", "   "):
                    store.reserve_idempotency("actor-a", "op", "k-ws", "h1")

            self.assertEqual(self._admin_count("idempotency"), 0)
        finally:
            store.close()

    def test_denied_raw_sql_empty_guc_rls_violation(self) -> None:
        """DB policy fail-closed without Python guards (matches stage error)."""
        with self.psycopg.connect(self.gateway_dsn) as conn:  # type: ignore[attr-defined]
            conn.autocommit = False
            with conn.cursor() as cur:
                cur.execute("set local role svc_lskills_runtime")
                cur.execute("select set_config('app.current_actor_id', '', true)")
                cur.execute("select set_config('app.current_org_id', 'org-a', true)")
                with self.assertRaises(Exception) as ctx:
                    cur.execute(
                        """
                        insert into lskills.idempotency (
                          actor_id, org_id, operation, idempotency_key, request_hash,
                          status, fence_token, fence_generation
                        ) values (
                          'actor-a', 'org-a', 'op', 'k-raw', 'h',
                          'reserved', 'fence', 1
                        )
                        """
                    )
                msg = str(ctx.exception).lower()
                self.assertTrue(
                    "row-level security" in msg or "insufficientprivilege" in msg
                    or "permission" in msg,
                    msg,
                )
                conn.rollback()
        self.assertEqual(
            self._admin_count("idempotency", actor_id="actor-a", key="k-raw"), 0
        )

    def test_membership_without_set_role_still_requires_gucs(self) -> None:
        """INHERIT membership applies runtime policies without SET ROLE.

        Empty GUCs must still fail WITH CHECK (stage-shaped RLS error).
        """
        with self.psycopg.connect(self.gateway_dsn) as conn:  # type: ignore[attr-defined]
            conn.autocommit = False
            with conn.cursor() as cur:
                # No SET LOCAL ROLE — rely on GRANT svc_lskills_runtime TO gateway.
                cur.execute(
                    "select set_config('app.current_actor_id', '', true)"
                )
                cur.execute("select set_config('app.current_org_id', 'org-a', true)")
                with self.assertRaises(Exception) as ctx:
                    cur.execute(
                        """
                        insert into lskills.idempotency (
                          actor_id, org_id, operation, idempotency_key, request_hash,
                          status, fence_token, fence_generation
                        ) values (
                          'actor-a', 'org-a', 'op', 'k-inherit-empty', 'h',
                          'reserved', 'fence', 1
                        )
                        """
                    )
                msg = str(ctx.exception).lower()
                self.assertTrue(
                    "row-level security" in msg
                    or "insufficientprivilege" in msg
                    or "permission" in msg,
                    msg,
                )
                conn.rollback()

                cur.execute(
                    "select set_config('app.current_actor_id', 'actor-a', true)"
                )
                cur.execute("select set_config('app.current_org_id', 'org-a', true)")
                cur.execute(
                    """
                    insert into lskills.idempotency (
                      actor_id, org_id, operation, idempotency_key, request_hash,
                      status, fence_token, fence_generation
                    ) values (
                      'actor-a', 'org-a', 'op', 'k-inherit-ok', 'h',
                      'reserved', 'fence', 1
                    )
                    """
                )
                conn.commit()
        self.assertEqual(
            self._admin_count("idempotency", key="k-inherit-empty"), 0
        )
        self.assertEqual(
            self._admin_count(
                "idempotency", actor_id="actor-a", org_id="org-a", key="k-inherit-ok"
            ),
            1,
        )

    def test_direct_table_grant_without_membership_denied(self) -> None:
        """Table INSERT grant alone (no runtime membership) must not pass RLS."""
        with self.psycopg.connect(self.admin_dsn, autocommit=True) as conn:  # type: ignore[attr-defined]
            with conn.cursor() as cur:
                cur.execute("revoke svc_lskills_runtime from svc_lskills_gateway")
                cur.execute(
                    "grant select, insert, update on lskills.idempotency "
                    "to svc_lskills_gateway"
                )
        try:
            with self.psycopg.connect(self.gateway_dsn) as conn:  # type: ignore[attr-defined]
                conn.autocommit = False
                with conn.cursor() as cur:
                    cur.execute(
                        "select set_config('app.current_actor_id', 'actor-a', true)"
                    )
                    cur.execute(
                        "select set_config('app.current_org_id', 'org-a', true)"
                    )
                    with self.assertRaises(Exception) as ctx:
                        cur.execute(
                            """
                            insert into lskills.idempotency (
                              actor_id, org_id, operation, idempotency_key,
                              request_hash, status, fence_token, fence_generation
                            ) values (
                              'actor-a', 'org-a', 'op', 'k-direct', 'h',
                              'reserved', 'fence', 1
                            )
                            """
                        )
                    msg = str(ctx.exception).lower()
                    self.assertTrue(
                        "row-level security" in msg
                        or "insufficientprivilege" in msg
                        or "permission" in msg,
                        msg,
                    )
                    conn.rollback()
            self.assertEqual(self._admin_count("idempotency", key="k-direct"), 0)
        finally:
            with self.psycopg.connect(self.admin_dsn, autocommit=True) as conn:  # type: ignore[attr-defined]
                with conn.cursor() as cur:
                    cur.execute(
                        "revoke select, insert, update on lskills.idempotency "
                        "from svc_lskills_gateway"
                    )
                    cur.execute("grant svc_lskills_runtime to svc_lskills_gateway")

    def test_denied_wrong_actor_org_and_forge(self) -> None:
        store = self._open_store()
        try:
            with store.identity("actor-a", "org-a"):
                reserved = store.reserve_idempotency("actor-a", "op", "k-x", "h1")
                self.assertEqual(reserved.outcome, "reserved")
                store.complete_idempotency(
                    "actor-a",
                    "op",
                    "k-x",
                    "h1",
                    {"ok": True},
                    fence_token=reserved.fence_token or "",
                )
            with store.identity("actor-b", "org-a"):
                self.assertIsNone(store.get_idempotent("actor-a", "op", "k-x"))
            with store.identity("actor-a", "org-b"):
                self.assertIsNone(store.get_idempotent("actor-a", "op", "k-x"))
            with store.identity("actor-a", "org-a"):
                with self.assertRaises(ValueError) as forge:
                    store.reserve_idempotency("actor-b", "op", "k-forge", "h2")
                self.assertIn("disagrees", str(forge.exception))
            self.assertEqual(
                self._admin_count("idempotency", actor_id="actor-b", key="k-forge"), 0
            )
        finally:
            store.close()

    def test_atomic_rollback_and_pool_reuse(self) -> None:
        from linkskills_gateway.service import SkillRun

        store = self._open_store()
        run_id = str(uuid.uuid4())
        try:
            store._crash_after_mutation = True
            with store.identity("actor-a", "org-a"):

                def boom():
                    store.save_run(
                        SkillRun(
                            run_id=run_id,
                            skill_id="demo",
                            version="1.0.0",
                            release_hash="rel",
                            profile_hash="prof",
                            actor_id="actor-a",
                            org_id="org-a",
                            status="started",
                            created_at="2026-08-04T00:00:00Z",
                            updated_at="2026-08-04T00:00:00Z",
                        )
                    )
                    return {"ok": False}

                with self.assertRaises(RuntimeError):
                    store.run_atomic_idempotent(
                        "actor-a", "skills_run_start", "k-crash", "h-crash", boom
                    )
            store._crash_after_mutation = False
            self.assertEqual(self._admin_count("skill_runs", actor_id="actor-a"), 0)
            self.assertEqual(
                self._admin_count("idempotency", actor_id="actor-a", key="k-crash"), 0
            )

            # GUC non-leakage after rollback + successful reuse as another tenant.
            with store._lock:
                with store._conn.cursor() as cur:
                    cur.execute(
                        "select current_setting('app.current_actor_id', true) as actor_guc, "
                        "current_setting('app.current_org_id', true) as org_guc"
                    )
                    row = cur.fetchone()
                store._conn.commit()
            if isinstance(row, dict):
                actor_guc, org_guc = row.get("actor_guc"), row.get("org_guc")
            else:
                actor_guc, org_guc = row[0], row[1]
            self.assertIn(actor_guc or "", ("", None))
            self.assertIn(org_guc or "", ("", None))

            with store.identity("actor-b", "org-b"):
                ok = store.reserve_idempotency("actor-b", "op", "k-reuse", "h-reuse")
                self.assertEqual(ok.outcome, "reserved")
                self.assertIsNone(store.get_idempotent("actor-a", "op", "k-crash"))
        finally:
            store.close()

    def test_denied_without_runtime_membership(self) -> None:
        with self.psycopg.connect(self.admin_dsn, autocommit=True) as conn:  # type: ignore[attr-defined]
            with conn.cursor() as cur:
                cur.execute("revoke svc_lskills_runtime from svc_lskills_gateway")
        store = self._open_store()
        try:
            with store.identity("actor-a", "org-a"):
                with self.assertRaises(Exception):
                    store.reserve_idempotency("actor-a", "op", "k-nomem", "h1")
            self.assertEqual(self._admin_count("idempotency", key="k-nomem"), 0)
        finally:
            store.close()
            with self.psycopg.connect(self.admin_dsn, autocommit=True) as conn:  # type: ignore[attr-defined]
                with conn.cursor() as cur:
                    cur.execute("grant svc_lskills_runtime to svc_lskills_gateway")

    def test_gateway_events_anonymous_insert_denied_by_policy(self) -> None:
        with self.psycopg.connect(self.gateway_dsn) as conn:  # type: ignore[attr-defined]
            conn.autocommit = False
            with conn.cursor() as cur:
                cur.execute("set local role svc_lskills_runtime")
                cur.execute(
                    "select set_config('app.current_actor_id', 'actor-a', true)"
                )
                cur.execute("select set_config('app.current_org_id', 'org-a', true)")
                with self.assertRaises(Exception):
                    cur.execute(
                        """
                        insert into lskills.gateway_events (actor_id, org_id, payload)
                        values (null, null, '{}'::jsonb)
                        """
                    )
                conn.rollback()
        self.assertEqual(self._admin_count("gateway_events"), 0)


if __name__ == "__main__":
    unittest.main()
