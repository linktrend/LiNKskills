#!/usr/bin/env python3
"""Ephemeral Postgres tests for actor/org RLS on registry tables.

Runs only when explicitly enabled:
- ``LINKSKILLS_TEST_PG_DSN`` set to a writable Postgres, or
- ``LINKSKILLS_TEST_PG_DOCKER=1`` and Docker available (spins postgres:16-alpine).

Default ``pytest`` skips this module so local proof stays deterministic.
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


def _explicitly_enabled() -> bool:
    if os.environ.get("LINKSKILLS_TEST_PG_DSN", "").strip():
        return True
    if os.environ.get("LINKSKILLS_TEST_PG_DOCKER", "").strip() in {"1", "true", "yes"}:
        return _docker_available()
    return False


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def _resolve_dsn() -> str | None:
    env = os.environ.get("LINKSKILLS_TEST_PG_DSN", "").strip()
    if env:
        return env
    if os.environ.get("LINKSKILLS_TEST_PG_DOCKER", "").strip() in {"1", "true", "yes"}:
        return "postgresql://postgres:postgres@127.0.0.1:54329/linkskills_rls_test"
    return None


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


@unittest.skipUnless(_explicitly_enabled(), "set LINKSKILLS_TEST_PG_DSN or LINKSKILLS_TEST_PG_DOCKER=1")
class RlsActorOrgEphemeralTests(unittest.TestCase):
    _container_id: str | None = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.dsn = _resolve_dsn()
        if not cls.dsn:
            raise unittest.SkipTest("no postgres DSN")
        if not os.environ.get("LINKSKILLS_TEST_PG_DSN", "").strip():
            cls._container_id = f"linkskills-rls-{uuid.uuid4().hex[:8]}"
            subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--rm",
                    "--name",
                    cls._container_id,
                    "-e",
                    "POSTGRES_PASSWORD=postgres",
                    "-e",
                    "POSTGRES_DB=linkskills_rls_test",
                    "-p",
                    "54329:5432",
                    "postgres:16-alpine",
                ],
                check=True,
                capture_output=True,
            )
            for _ in range(40):
                probe = subprocess.run(
                    ["docker", "exec", cls._container_id, "pg_isready", "-U", "postgres"],
                    capture_output=True,
                )
                if probe.returncode == 0:
                    break
                time.sleep(0.5)
            else:
                raise unittest.SkipTest("docker postgres failed to become ready")
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
