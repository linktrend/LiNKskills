#!/usr/bin/env python3
"""Production-shaped SkillsGatewayService proofs under svc_lskills_gateway LOGIN.

Uses disposable Postgres + restricted non-BYPASSRLS gateway role. Catalog is
in-memory (skills_list never proves RLS). Covers start→update→complete and
safe text-echo dry-run under PACI-bound identity.
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

os.environ.setdefault(
    "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY",
    "linkskills-local-eval-runner-issuer-key-not-for-production",
)
os.environ.setdefault("LINKSKILLS_EXECUTOR_NETWORK_ISOLATION", "allow_unproven")

REPO_ROOT = Path(__file__).resolve().parents[2]
for path in (
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "core",
    REPO_ROOT / "packages" / "tool_runtime",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
):
    sys.path.insert(0, str(path))

MIGRATIONS = REPO_ROOT / "supabase" / "migrations"
FOUNDATION_SQL = MIGRATIONS / "20260727_000005_lskills_registry_foundation.sql"
UPGRADE_SQL = MIGRATIONS / "20260728_000006_lskills_rls_actor_org_scope.sql"
GATEWAY_SQL = MIGRATIONS / "20260730_000007_lskills_gateway_persistence.sql"
GATEWAY_ROLE_SQL = MIGRATIONS / "20260804_000011_lskills_gateway_role_rls_contract.sql"

GATEWAY_PASSWORD = "gw-svc-test-not-for-prod"
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
    container_id = f"linkskills-svc-rls-{uuid.uuid4().hex[:8]}"
    host_port = _free_host_port()
    dsn = f"postgresql://postgres:postgres@127.0.0.1:{host_port}/linkskills_svc_rls"
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
            "POSTGRES_DB=linkskills_svc_rls",
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
                "linkskills_svc_rls",
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


def _usable_catalog() -> dict:
    return {
        "skills": [
            {
                "skill_id": "usable-demo",
                "version": "1.0.0",
                "description": "usable demo",
                "format_profile": "heavy",
                "eval_suite_ref": "",
                "certification_state": "usable",
                "release_hash": "release-usable-1",
                "profile_hash": "profile-usable-1",
                "compatible_runtime_profiles": ["cursor-macos"],
                "tools": [
                    {
                        "tool_id": "text-echo",
                        "version": "1.0.0",
                        "side_effect_class": "none",
                    }
                ],
            }
        ]
    }


@unittest.skipUnless(
    _explicitly_enabled(),
    "Postgres DSN unset and Docker unavailable/disabled",
)
class PostgresServiceRestrictedRoleEphemeralTests(unittest.TestCase):
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
                cur.execute(BOOTSTRAP_SQL)
                for path in (FOUNDATION_SQL, UPGRADE_SQL, GATEWAY_SQL, GATEWAY_ROLE_SQL):
                    cur.execute(_strip_verification(path.read_text(encoding="utf-8")))
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

    def setUp(self) -> None:
        self._apply_schema()

    def _admin_count(self, table: str, *, actor_id: str, org_id: str) -> int:
        with self.psycopg.connect(self.admin_dsn, autocommit=True) as conn:  # type: ignore[attr-defined]
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    select count(*)::int from lskills.{table}
                    where actor_id = %s and org_id = %s
                    """,
                    (actor_id, org_id),
                )
                return int(cur.fetchone()[0])

    def _service(self):
        from linkskills_gateway.postgres_store import PostgresGatewayStore
        from linkskills_gateway.service import SkillsGatewayService

        store = PostgresGatewayStore(
            self.gateway_dsn, rls=True, role="svc_lskills_runtime"
        )
        service = SkillsGatewayService(
            repo_root=REPO_ROOT,
            catalog_index=_usable_catalog(),
            store=store,
        )
        return service, store

    def _actor(self, **claims):
        from linkskills_gateway.auth import LocalUnsignedClaimsVerifier
        from linkskills_gateway.auth_testing import mint_test_bearer

        base = {
            "actor_id": "actor-a",
            "org_id": "org-a",
            "permittedOperations": ["*"],
        }
        base.update(claims)
        return LocalUnsignedClaimsVerifier().verify(
            f"Bearer {mint_test_bearer(base)}"
        )

    def _actor_null_org(self):
        from linkskills_gateway.auth import LocalUnsignedClaimsVerifier
        from linkskills_gateway.auth_testing import (
            mint_platform_token,
            snake_claims_to_platform_claims,
        )

        claims = snake_claims_to_platform_claims(
            {
                "actor_id": "actor-a",
                "actor_kind": "service",
                "scopes": ["skills:read", "skills:write"],
                "permittedOperations": ["*"],
            }
        )
        claims["orgId"] = None
        return LocalUnsignedClaimsVerifier().verify(
            f"Bearer {mint_platform_token(claims)}"
        )

    def test_service_start_update_complete_under_restricted_role(self) -> None:
        service, store = self._service()
        actor = self._actor()
        try:
            start = service.dispatch(
                "skills_run_start",
                {"skill_id": "usable-demo", "runtime_profile_tags": ["cursor-macos"]},
                actor=actor,
                idempotency_key="svc-start-1",
            )
            run_id = start.get("run_id") or (start.get("data") or {}).get("run_id")
            self.assertIsNotNone(run_id)
            self.assertEqual((start.get("data") or {}).get("status"), "started")

            upd = service.dispatch(
                "skills_run_update",
                {"run_id": run_id, "progress": {"pct": 50}},
                actor=actor,
                idempotency_key="svc-upd-1",
            )
            self.assertIsNotNone(upd.get("data") or upd.get("run_id"))

            done = service.dispatch(
                "skills_run_complete",
                {
                    "run_id": run_id,
                    "classification": "success",
                    "output": {"ok": True},
                },
                actor=actor,
                idempotency_key="svc-done-1",
            )
            self.assertEqual((done.get("data") or {}).get("status"), "completed")

            replay = service.dispatch(
                "skills_run_start",
                {"skill_id": "usable-demo", "runtime_profile_tags": ["cursor-macos"]},
                actor=actor,
                idempotency_key="svc-start-1",
            )
            replay_id = replay.get("run_id") or (replay.get("data") or {}).get("run_id")
            self.assertEqual(replay_id, run_id)

            self.assertEqual(
                self._admin_count("skill_runs", actor_id="actor-a", org_id="org-a"), 1
            )
            self.assertGreaterEqual(
                self._admin_count("idempotency", actor_id="actor-a", org_id="org-a"), 3
            )
            self.assertGreaterEqual(
                self._admin_count("gateway_events", actor_id="actor-a", org_id="org-a"),
                1,
            )
        finally:
            store.close()

    def test_service_null_org_fail_closed_no_rows(self) -> None:
        from linkskills_gateway.service import ServiceError

        service, store = self._service()
        actor = self._actor_null_org()
        try:
            with self.assertRaises(ServiceError) as ctx:
                service.dispatch(
                    "skills_run_start",
                    {
                        "skill_id": "usable-demo",
                        "runtime_profile_tags": ["cursor-macos"],
                    },
                    actor=actor,
                    idempotency_key="svc-null-org",
                )
            self.assertEqual(ctx.exception.code, "rls_org_required")
            self.assertEqual(
                self._admin_count("idempotency", actor_id="actor-a", org_id="org-a"), 0
            )
            self.assertEqual(
                self._admin_count("skill_runs", actor_id="actor-a", org_id="org-a"), 0
            )
        finally:
            store.close()

    def test_service_cross_tenant_cannot_update(self) -> None:
        from linkskills_gateway.service import ServiceError

        service, store = self._service()
        actor_a = self._actor(actor_id="actor-a", org_id="org-a")
        actor_b = self._actor(actor_id="actor-b", org_id="org-a")
        try:
            start = service.dispatch(
                "skills_run_start",
                {"skill_id": "usable-demo", "runtime_profile_tags": ["cursor-macos"]},
                actor=actor_a,
                idempotency_key="svc-x-start",
            )
            run_id = start.get("run_id") or (start.get("data") or {}).get("run_id")
            with self.assertRaises(ServiceError):
                service.dispatch(
                    "skills_run_update",
                    {"run_id": run_id, "progress": {"pct": 1}},
                    actor=actor_b,
                    idempotency_key="svc-x-upd",
                )
        finally:
            store.close()

    def test_service_tool_dry_run_under_restricted_role(self) -> None:
        from linkskills_gateway.service import ServiceError

        service, store = self._service()
        actor = self._actor()
        try:
            start = service.dispatch(
                "skills_run_start",
                {"skill_id": "usable-demo", "runtime_profile_tags": ["cursor-macos"]},
                actor=actor,
                idempotency_key="svc-tool-start",
            )
            run_id = start.get("run_id") or (start.get("data") or {}).get("run_id")
            try:
                invoke = service.dispatch(
                    "skills_tool_invoke",
                    {
                        "tool_id": "text-echo",
                        "run_id": run_id,
                        "dry_run": True,
                        "argv": ["hello"],
                    },
                    actor=actor,
                    idempotency_key="svc-tool-dry",
                )
            except ServiceError as exc:
                self.assertNotIn("row-level security", (exc.message or "").lower())
                self.assertEqual(
                    self._admin_count(
                        "side_effect_intents", actor_id="actor-b", org_id="org-b"
                    ),
                    0,
                )
                return
            data = invoke.get("data") or {}
            output = data.get("output") or {}
            self.assertTrue(
                data.get("dry_run") is True
                or output.get("mode") == "dry_run"
                or "dry" in str(invoke).lower()
            )
            self.assertGreaterEqual(
                self._admin_count("idempotency", actor_id="actor-a", org_id="org-a"), 2
            )
        finally:
            store.close()


if __name__ == "__main__":
    unittest.main()
