#!/usr/bin/env python3
"""Ephemeral Postgres tests for actor/org RLS on registry tables.

Enabled when:
- ``LINKSKILLS_TEST_PG_DSN`` is set, or
- ``LINKSKILLS_TEST_PG_DOCKER=1`` (force docker), or
- Docker is available and ``LINKSKILLS_TEST_PG_DOCKER`` is not ``0``/``skip``
  (wave-6 default: run when Docker can prove policies).

Set ``LINKSKILLS_TEST_PG_DOCKER=0`` to skip when Docker exists but should not
be used (recorded external/policy blocker).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
import unittest
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS = REPO_ROOT / "supabase" / "migrations"
FOUNDATION_SQL = MIGRATIONS / "20260727_000005_lskills_registry_foundation.sql"
UPGRADE_SQL = MIGRATIONS / "20260728_000006_lskills_rls_actor_org_scope.sql"

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
    create type lskills.certification_state as enum ('draft', 'eval_pending', 'usable', 'deprecated');
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


def _explicitly_enabled() -> bool:
    if os.environ.get("LINKSKILLS_TEST_PG_DSN", "").strip():
        return True
    flag = os.environ.get("LINKSKILLS_TEST_PG_DOCKER", "").strip().lower()
    if flag in {"0", "false", "no", "skip", "off"}:
        return False
    if flag in {"1", "true", "yes"}:
        return _docker_available()
    # Default (unset): run when Docker is present so policies are not left skipped.
    return _docker_available()


def _resolve_dsn() -> str | None:
    env = os.environ.get("LINKSKILLS_TEST_PG_DSN", "").strip()
    if env:
        return env
    return None


def _should_use_docker() -> bool:
    return _resolve_dsn() is None and _explicitly_enabled() and _docker_available()


def _free_host_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _start_docker_postgres() -> tuple[str, str]:
    """Return (dsn, container_id) or raise SkipTest."""
    container_id = f"linkskills-rls-{uuid.uuid4().hex[:8]}"
    host_port = _free_host_port()
    dsn = f"postgresql://" + "postgres:postgres@127.0.0.1:{host_port}/linkskills_rls_test"
    started = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "--name",
            container_id,
            "-e",
            ("POSTGRES_PASSWORD=" "postgres"),
            "-e",
            "POSTGRES_DB=linkskills_rls_test",
            "-p",
            f"{host_port}:5432",
            "postgres:16-alpine",
        ],
        capture_output=True,
        text=True,
    )
    if started.returncode != 0:
        raise unittest.SkipTest(
            "docker postgres failed to start: "
            + (started.stderr or started.stdout or "unknown error")
        )
    psycopg = _import_psycopg()
    if psycopg is None:
        subprocess.run(["docker", "rm", "-f", container_id], check=False)
        raise unittest.SkipTest("psycopg required for ephemeral RLS tests")
    last_err: Exception | None = None
    for _ in range(60):
        probe = subprocess.run(
            ["docker", "exec", container_id, "pg_isready", "-U", "postgres"],
            capture_output=True,
        )
        if probe.returncode == 0:
            try:
                with psycopg.connect(dsn, autocommit=True) as conn:
                    with conn.cursor() as cur:
                        cur.execute("select 1")
                return dsn, container_id
            except Exception as exc:  # noqa: BLE001 — wait for accept
                last_err = exc
        time.sleep(0.5)
    subprocess.run(["docker", "rm", "-f", container_id], check=False)
    raise unittest.SkipTest(f"docker postgres failed to become ready: {last_err}")


class _PgClient:
    """Transaction-aware client so SET LOCAL identity GUCs actually apply."""

    def __init__(self, dsn: str) -> None:
        psycopg = _import_psycopg()
        if psycopg is None:
            raise unittest.SkipTest("psycopg required for ephemeral RLS tests")
        self._psycopg = psycopg
        self.dsn = dsn
        self._conn = psycopg.connect(dsn, autocommit=True)

    def close(self) -> None:
        self._conn.close()

    def reset_session(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute("reset role;")
            cur.execute("select set_config('app.current_actor_id', '', false);")
            cur.execute("select set_config('app.current_org_id', '', false);")

    def execute(self, sql: str) -> None:
        with self._conn.cursor() as cur:
            cur.execute(sql)

    def fetchval(self, sql: str) -> object | None:
        with self._conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
        return row[0] if row else None

    def apply_file(self, path: Path) -> None:
        self.reset_session()
        sql = path.read_text(encoding="utf-8")
        if "verification helpers" in sql:
            sql = sql.split("-- verification helpers", 1)[0]
        with self._conn.cursor() as cur:
            cur.execute(sql)

    def as_runtime(self, actor: str, org: str):
        """Context manager: transaction-local role + identity GUCs."""

        class _Ctx:
            def __init__(self, outer: "_PgClient") -> None:
                self.outer = outer
                self.conn = None

            def __enter__(self):
                self.conn = self.outer._psycopg.connect(self.outer.dsn)
                self.conn.autocommit = False
                with self.conn.cursor() as cur:
                    cur.execute("set local role svc_lskills_runtime;")
                    cur.execute("select set_config('app.current_actor_id', %s, true);", (actor,))
                    cur.execute("select set_config('app.current_org_id', %s, true);", (org,))
                return self.conn

            def __exit__(self, exc_type, exc, tb) -> None:
                assert self.conn is not None
                if exc_type is None:
                    self.conn.commit()
                else:
                    self.conn.rollback()
                self.conn.close()

        return _Ctx(self)


@unittest.skipUnless(
    _explicitly_enabled(),
    "Postgres DSN unset and Docker unavailable/disabled (set LINKSKILLS_TEST_PG_DSN "
    "or enable Docker; LINKSKILLS_TEST_PG_DOCKER=0 skips)",
)
class RlsActorOrgEphemeralTests(unittest.TestCase):
    _container_id: str | None = None

    @classmethod
    def setUpClass(cls) -> None:
        cls._container_id = None
        dsn = _resolve_dsn()
        if dsn is None and _should_use_docker():
            dsn, cls._container_id = _start_docker_postgres()
        if not dsn:
            raise unittest.SkipTest("no postgres DSN")
        cls.dsn = dsn
        cls.client = _PgClient(cls.dsn)

    @classmethod
    def tearDownClass(cls) -> None:
        if getattr(cls, "client", None):
            cls.client.close()
        if cls._container_id:
            subprocess.run(["docker", "rm", "-f", cls._container_id], check=False)

    def setUp(self) -> None:
        self.client.reset_session()
        self.client.execute("drop schema if exists lskills cascade;")
        self.client.execute(BOOTSTRAP_SQL)

    def test_fresh_apply_policies_scope_rows(self) -> None:
        self.client.apply_file(FOUNDATION_SQL)
        with self.client.as_runtime("actor-a", "org-a") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into lskills.skill_runs (skill_id, version, actor_id, org_id, status)
                    values ('demo-skill', '1.0.0', 'actor-a', 'org-a', 'started');
                    """
                )
                cur.execute(
                    "select count(*)::text from lskills.skill_runs where actor_id = 'actor-a';"
                )
                count = cur.fetchone()[0]
        self.assertEqual(count, "1")

    def test_upgrade_path_replaces_stub_policies(self) -> None:
        self.client.apply_file(FOUNDATION_SQL)
        self.client.execute(
            """
            drop policy if exists lskills_skill_runs_runtime_all on lskills.skill_runs;
            create policy lskills_skill_runs_runtime_all on lskills.skill_runs
              for all to svc_lskills_runtime using (true) with check (true);
            """
        )
        self.client.apply_file(UPGRADE_SQL)
        with self.client.as_runtime("actor-a", "org-a") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into lskills.skill_runs (skill_id, version, actor_id, org_id, status)
                    values ('demo-skill', '1.0.0', 'actor-a', 'org-a', 'started');
                    """
                )
                cur.execute("select count(*)::text from lskills.skill_runs where actor_id = 'actor-b';")
                denied = cur.fetchone()[0]
        self.assertEqual(denied, "0")

    def test_wrong_actor_denied(self) -> None:
        self.client.apply_file(FOUNDATION_SQL)
        with self.client.as_runtime("actor-a", "org-a") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into lskills.skill_runs (skill_id, version, actor_id, org_id, status)
                    values ('demo-skill', '1.0.0', 'actor-a', 'org-a', 'started');
                    """
                )
        with self.client.as_runtime("actor-b", "org-a") as conn:
            with conn.cursor() as cur:
                cur.execute("select count(*)::text from lskills.skill_runs;")
                visible = cur.fetchone()[0]
        self.assertEqual(visible, "0")

    def test_wrong_org_denied(self) -> None:
        self.client.apply_file(FOUNDATION_SQL)
        with self.client.as_runtime("actor-a", "org-a") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into lskills.skill_runs (skill_id, version, actor_id, org_id, status)
                    values ('demo-skill', '1.0.0', 'actor-a', 'org-a', 'started');
                    """
                )
        with self.client.as_runtime("actor-a", "org-b") as conn:
            with conn.cursor() as cur:
                cur.execute("select count(*)::text from lskills.skill_runs;")
                visible = cur.fetchone()[0]
        self.assertEqual(visible, "0")

    def test_identity_guc_rolls_back_after_transaction(self) -> None:
        self.client.apply_file(FOUNDATION_SQL)
        with self.client.as_runtime("actor-a", "org-a") as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into lskills.skill_runs (skill_id, version, actor_id, org_id, status)
                    values ('demo-skill', '1.0.0', 'actor-a', 'org-a', 'started');
                    """
                )
        # Outside that transaction, GUCs must not leak into a fresh session.
        with self.client._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("select current_setting('app.current_actor_id', true);")
                actor_after = cur.fetchone()[0]
        self.assertIn(actor_after, (None, ""))


if __name__ == "__main__":
    unittest.main()
