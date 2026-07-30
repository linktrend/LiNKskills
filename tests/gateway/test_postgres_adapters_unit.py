#!/usr/bin/env python3
"""Unit tests for Postgres gateway/librarian adapters + production store gate."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "gateway"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "librarian_domain"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "publisher"))

from linkskills_gateway.persistence import (  # noqa: E402
    InMemoryGatewayStore,
    open_gateway_store,
    resolve_gateway_store_mode,
)


class OpenGatewayStoreEnvTests(unittest.TestCase):
    def test_default_remains_in_memory(self) -> None:
        env = {
            k: v
            for k, v in os.environ.items()
            if k
            not in {
                "LINKSKILLS_GATEWAY_STORE",
                "LINKSKILLS_GATEWAY_DURABLE",
                "LINKSKILLS_DATABASE_URL",
                "DATABASE_URL",
                "LINKSKILLS_ENV",
                "LINKSKILLS_STORE_URL",
                "LINKSKILLS_POSTGRES_URL",
                "LINKSKILLS_EPHEMERAL_PG_URL",
            }
        }
        with mock.patch.dict(os.environ, env, clear=True):
            store = open_gateway_store(repo_root=REPO_ROOT)
            self.assertIsInstance(store, InMemoryGatewayStore)

    def test_postgres_requires_dsn(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"LINKSKILLS_GATEWAY_STORE": "postgres"},
            clear=False,
        ):
            os.environ.pop("LINKSKILLS_DATABASE_URL", None)
            os.environ.pop("DATABASE_URL", None)
            os.environ.pop("LINKSKILLS_EPHEMERAL_PG_URL", None)
            os.environ.pop("LINKSKILLS_STORE_URL", None)
            os.environ.pop("LINKSKILLS_POSTGRES_URL", None)
            with self.assertRaises(ValueError):
                open_gateway_store(repo_root=REPO_ROOT)

    def test_production_env_implies_postgres_and_rejects_memory(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"LINKSKILLS_ENV": "stage", "LINKSKILLS_GATEWAY_STORE": "memory"},
            clear=False,
        ):
            with self.assertRaises(ValueError):
                resolve_gateway_store_mode()
        with mock.patch.dict(
            os.environ,
            {"LINKSKILLS_ENV": "production"},
            clear=False,
        ):
            os.environ.pop("LINKSKILLS_GATEWAY_STORE", None)
            self.assertEqual(resolve_gateway_store_mode(), "postgres")

    def test_production_env_without_dsn_fails_closed(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"LINKSKILLS_ENV": "prod"},
            clear=False,
        ):
            for key in (
                "LINKSKILLS_GATEWAY_STORE",
                "LINKSKILLS_DATABASE_URL",
                "DATABASE_URL",
                "LINKSKILLS_STORE_URL",
                "LINKSKILLS_POSTGRES_URL",
                "LINKSKILLS_EPHEMERAL_PG_URL",
            ):
                os.environ.pop(key, None)
            with self.assertRaises(ValueError):
                open_gateway_store(repo_root=REPO_ROOT)

    def test_explicit_sqlite_allowed_only_non_production(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "LINKSKILLS_ENV": "dev",
                "LINKSKILLS_GATEWAY_STORE": "sqlite",
                "LINKSKILLS_AUTH_MODE": "local-test",
            },
            clear=False,
        ):
            self.assertEqual(resolve_gateway_store_mode(), "sqlite")

    def test_postgres_selected_when_dsn_present(self) -> None:
        fake = mock.MagicMock()
        fake.probe_reachable.return_value = True
        fake.probe_schema_ready.return_value = True
        with mock.patch.dict(
            os.environ,
            {
                "LINKSKILLS_GATEWAY_STORE": "postgres",
                "LINKSKILLS_DATABASE_URL": "postgresql://example/db",
            },
            clear=False,
        ):
            with mock.patch(
                "linkskills_gateway.postgres_store.PostgresGatewayStore",
                return_value=fake,
            ) as ctor:
                store = open_gateway_store(repo_root=REPO_ROOT)
        self.assertIs(store, fake)
        ctor.assert_called_once_with("postgresql://example/db")
        fake.probe_reachable.assert_called_once()
        fake.probe_schema_ready.assert_called_once()

    def test_postgres_probe_failure_closes_store(self) -> None:
        fake = mock.MagicMock()
        fake.probe_reachable.return_value = True
        fake.probe_schema_ready.return_value = False
        with mock.patch.dict(
            os.environ,
            {
                "LINKSKILLS_GATEWAY_STORE": "postgres",
                "LINKSKILLS_DATABASE_URL": "postgresql://example/db",
            },
            clear=False,
        ):
            with mock.patch(
                "linkskills_gateway.postgres_store.PostgresGatewayStore",
                return_value=fake,
            ):
                with self.assertRaises(RuntimeError):
                    open_gateway_store(repo_root=REPO_ROOT)
        fake.close.assert_called()


class PostgresGatewayStoreUnitTests(unittest.TestCase):
    def test_import_and_bind_identity(self) -> None:
        from linkskills_gateway.postgres_store import PostgresGatewayStore

        with mock.patch("linkskills_gateway.postgres_store.psycopg") as psycopg_mod:
            conn = mock.MagicMock()
            conn.info.transaction_status = 0
            psycopg_mod.connect.return_value = conn
            psycopg_mod.pq.TransactionStatus.IDLE = 0
            store = PostgresGatewayStore("postgresql://example/db", rls=False)
            store.bind_identity("actor-a", "org-a")
            self.assertEqual(store._current_identity(), ("actor-a", "org-a"))
            with store.identity("actor-b", "org-b"):
                self.assertEqual(store._current_identity(), ("actor-b", "org-b"))
            self.assertEqual(store._current_identity(), ("actor-a", "org-a"))
            store.close()


class LibrarianPostgresOpenTests(unittest.TestCase):
    def test_open_review_queue_postgres_env(self) -> None:
        from linkskills_librarian.store import open_review_queue_store

        fake = object()
        with mock.patch.dict(
            os.environ,
            {
                "LINKSKILLS_LIBRARIAN_STORE": "postgres",
                "LINKSKILLS_DATABASE_URL": "postgresql://example/db",
            },
            clear=False,
        ):
            with mock.patch(
                "linkskills_librarian.postgres_store.open_postgres_review_queue_store",
                return_value=fake,
            ):
                store = open_review_queue_store(repo_root=REPO_ROOT)
        self.assertIs(store, fake)

    def test_production_librarian_rejects_memory(self) -> None:
        from linkskills_librarian.store import open_review_queue_store

        with mock.patch.dict(
            os.environ,
            {
                "LINKSKILLS_ENV": "stage",
                "LINKSKILLS_LIBRARIAN_STORE": "memory",
            },
            clear=False,
        ):
            with self.assertRaises(ValueError):
                open_review_queue_store(repo_root=REPO_ROOT)

    def test_ephemeral_helper_is_not_live_ddl(self) -> None:
        helper = REPO_ROOT / "tests" / "helpers" / "ephemeral_review_queue_ddl.sql"
        self.assertTrue(helper.is_file())
        text = helper.read_text(encoding="utf-8")
        self.assertIn("NOT a live migration", text)
        self.assertIn("20260730_000008_lskills_review_queue.sql", text)
        self.assertNotIn("create table", text.lower())
        migration = (
            REPO_ROOT
            / "supabase"
            / "migrations"
            / "20260730_000008_lskills_review_queue.sql"
        )
        self.assertTrue(migration.is_file())
        mig = migration.read_text(encoding="utf-8").lower()
        self.assertIn("create table if not exists lskills.review_queue", mig)


class PublisherPostgresOpenTests(unittest.TestCase):
    def test_open_publisher_registry_postgres(self) -> None:
        from linkskills_publisher.postgres_registry import open_publisher_registry

        fake = object()
        with mock.patch.dict(
            os.environ,
            {
                "LINKSKILLS_PUBLISHER_STORE": "postgres",
                "LINKSKILLS_DATABASE_URL": "postgresql://example/db",
            },
            clear=False,
        ):
            with mock.patch(
                "linkskills_publisher.postgres_registry.PostgresPublisherRegistry.open",
                return_value=fake,
            ):
                registry = open_publisher_registry(repo_root=REPO_ROOT)
        self.assertIs(registry, fake)

    def test_sqlite_default_unchanged(self) -> None:
        from linkskills_publisher.postgres_registry import open_publisher_registry
        from linkskills_publisher.registry import PublisherRegistry

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"LINKSKILLS_PUBLISHER_STORE": ""}, clear=False):
                os.environ.pop("LINKSKILLS_PUBLISHER_STORE", None)
                registry = open_publisher_registry(state_dir=Path(tmp))
            self.assertIsInstance(registry, PublisherRegistry)
            registry.close()


class Migration000007StructuralTests(unittest.TestCase):
    def test_additive_and_platform_owned(self) -> None:
        path = (
            REPO_ROOT
            / "supabase"
            / "migrations"
            / "20260730_000007_lskills_gateway_persistence.sql"
        )
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        self.assertIn("additive only", lower)
        self.assertIn("linkplatform alone applies live", lower)
        self.assertIn("create table if not exists lskills.idempotency", lower)
        self.assertIn("create table if not exists lskills.side_effect_intents", lower)
        code_lines = []
        for line in text.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("--"):
                continue
            if "--" in line:
                line = line.split("--", 1)[0]
            code_lines.append(line)
        code = "\n".join(code_lines).lower()
        self.assertNotIn("drop schema", code)
        self.assertNotIn("truncate", code)


class Migration000008StructuralTests(unittest.TestCase):
    def test_additive_review_queue(self) -> None:
        path = (
            REPO_ROOT
            / "supabase"
            / "migrations"
            / "20260730_000008_lskills_review_queue.sql"
        )
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        self.assertIn("additive only", lower)
        self.assertIn("linkplatform alone applies live", lower)
        self.assertIn("create table if not exists lskills.review_queue", lower)
        self.assertIn("review_queue_status", lower)
        self.assertIn("dead_letter", lower)
        self.assertIn("idempotency_key", lower)
        self.assertIn("provenance", lower)
        self.assertIn("retain_until", lower)
        self.assertIn("row level security", lower)
        code_lines = []
        for line in text.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("--"):
                continue
            if "--" in line:
                line = line.split("--", 1)[0]
            code_lines.append(line)
        code = "\n".join(code_lines).lower()
        self.assertNotIn("drop schema", code)
        self.assertNotIn("truncate", code)

    def test_manifest_lists_000007_and_000008(self) -> None:
        manifest = (
            REPO_ROOT / "docs" / "migrations" / "MANIFEST-20260727-lskills-registry-v0.1.md"
        )
        text = manifest.read_text(encoding="utf-8")
        self.assertIn("20260730_000007_lskills_gateway_persistence.sql", text)
        self.assertIn("20260730_000008_lskills_review_queue.sql", text)
        self.assertNotIn("PLACEHOLDER_SHA_000008", text)


class OpsStoreProbeTests(unittest.TestCase):
    def test_production_env_enables_store_probe(self) -> None:
        from linkskills_gateway.ops import store_probe_configured

        self.assertTrue(
            store_probe_configured({"LINKSKILLS_ENV": "stage"})
        )
        self.assertTrue(
            store_probe_configured({"LINKSKILLS_GATEWAY_STORE": "postgres"})
        )


if __name__ == "__main__":
    unittest.main()
