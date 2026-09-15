"""Production binding regressions, with real Postgres checks on hosted CI."""

import base64
import copy
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from linkskills_core.provider_v2 import InMemoryProviderStore, PROTOCOL_VERSION
from linkskills_gateway.production_v2 import (
    PostgresProviderStore, ProductionV2Provider, decode_release, manifest_digest,
)


def publication():
    body = b"Follow the verified procedure."
    manifest = {
        "skill_id": "git-safeguard", "version": "1.1.0", "qualification": "qualified",
        "family_id": "development", "runtime_profiles": ["cursor-macos"],
        "provenance": {"source_commit": "a" * 40},
        "resources": {"SKILL.md": {
            "content_b64": base64.b64encode(body).decode(),
            "content_digest": "sha256:" + hashlib.sha256(body).hexdigest(),
            "provenance": {"source_commit": "a" * 40},
            "licence": {"spdx": "LicenseRef-Proprietary"},
        }},
    }
    return {"release_id": "git-safeguard@1.1.0", "manifest": manifest,
            "manifest_sha256": manifest_digest(manifest), "lifecycle": "qualified"}


def request(operation, **params):
    return {"operation": operation, "protocol_version": PROTOCOL_VERSION,
            "authorization": "test-bearer", **params}


class Store(InMemoryProviderStore):
    def __init__(self):
        super().__init__()
        self.row = publication()
        self.enabled = True

    def snapshot(self, claims):
        if not self.enabled:
            raise ValueError("forbidden")
        return [decode_release(self.row)], {"runtime_profile": "cursor-macos",
                                             "release_ids": [self.row["release_id"]]}


def runtime():
    auth = Mock()
    auth.verify.return_value = SimpleNamespace(
        org_id="org-a", actor_id="actor-a", runtime_binding_id="binding-a",
        scopes={"skills:read", "skills:write"}, permitted_operations={"read", "execute"},
    )
    store = Store()
    return ProductionV2Provider(auth, store), auth, store


def test_exact_content_and_immediate_revocation():
    provider, _, store = runtime()
    req = request("skills_release_content_get", skill_id="git-safeguard", version="1.1.0", resource_id="SKILL.md")
    assert provider.handle(req)["ok"]
    store.row["lifecycle"] = "revoked"
    assert provider.handle(req)["error"] == "revoked_release"


def test_disabled_binding_and_claim_spoofing_fail_closed():
    provider, _, store = runtime()
    store.enabled = False
    result = provider.handle(request("skills_release_content_get", skill_id="git-safeguard",
                                     version="1.1.0", activated_release_ids=["*"], actor_id="other"))
    assert result == {"ok": False, "error": "forbidden"}


def test_mutating_operation_requires_write_verification():
    provider, auth, _ = runtime()
    auth.verify.side_effect = ValueError("read-only actor")
    assert provider.handle(request("skills_use_report_submit"))["error"] == "auth_invalid"
    assert auth.verify.call_args.kwargs["required_operation"] == "skills_feedback_submit"


def test_tampered_manifest_or_bytes_rejected():
    row = publication()
    corrupted = copy.deepcopy(row)
    corrupted["manifest"]["version"] = "2.0.0"
    with pytest.raises(ValueError, match="integrity_mismatch"):
        decode_release(corrupted)
    corrupted = copy.deepcopy(row)
    corrupted["manifest"]["resources"]["SKILL.md"]["content_b64"] = "YmFk"
    corrupted["manifest_sha256"] = manifest_digest(corrupted["manifest"])
    with pytest.raises(ValueError, match="integrity_mismatch"):
        decode_release(corrupted)


def test_database_errors_do_not_leak():
    provider, _, store = runtime()
    store.snapshot = Mock(side_effect=RuntimeError("private connection detail"))
    assert provider.handle(request("skills_catalog_list")) == {"ok": False, "error": "store_unavailable"}


def test_legacy_and_bad_protocol_do_not_touch_database():
    provider, _, store = runtime()
    store.snapshot = Mock(side_effect=AssertionError("must not connect"))
    assert provider.handle(request("skills_run_start"))["error"] == "legacy_execution_disabled"
    assert provider.handle({**request("skills_catalog_list"), "protocol_version": "old"})["error"] == "contract_incompatible"
    store.snapshot.assert_not_called()


@pytest.mark.skipif(not os.environ.get("LINKSKILLS_V2_TEST_DATABASE_URL"), reason="hosted Postgres only")
def test_postgres_receipt_restart_isolation_and_immutable_publication():
    """Use a dedicated disposable CI database; never start Docker locally."""
    import psycopg
    from psycopg.types.json import Jsonb

    dsn = os.environ["LINKSKILLS_V2_TEST_DATABASE_URL"]
    root = Path(__file__).resolve().parents[2]
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("create schema lskills")
        conn.execute("create role svc_lskills_runtime nologin nobypassrls")
        conn.execute("create role svc_lskills_librarian nologin nobypassrls")
        conn.execute("grant usage on schema lskills to svc_lskills_runtime, svc_lskills_librarian")
        conn.execute((root / "supabase/migrations/20260915031801_lskills_provider_v2_runtime.sql").read_text())
        row = publication()
        conn.execute(
            "insert into lskills.provider_releases (release_id,manifest,manifest_sha256,qualification_sha256) values (%s,%s,%s,%s)",
            (row["release_id"], Jsonb(row["manifest"]), row["manifest_sha256"], "sha256:" + "a" * 64),
        )
    store = PostgresProviderStore(dsn)
    assert store.probe()["ready"]
    record = {"org_id": "org-a", "actor_id": "actor-a", "request_hash": "hash-a", "payload": {}}
    store.put("use", "receipt-a", record, org_id="org-a", actor_id="actor-a")
    restarted = PostgresProviderStore(dsn)
    assert restarted.get("use", "receipt-a", org_id="org-a", actor_id="actor-a") == record
    assert restarted.get("use", "receipt-a", org_id="org-b", actor_id="actor-a") is None
    assert restarted.get("use", "receipt-a", org_id="org-a", actor_id="actor-b") is None
    assert restarted.put("use", "receipt-a", record, org_id="org-a", actor_id="actor-a") == record
    with pytest.raises(ValueError, match="idempotency_conflict"):
        restarted.put("use", "receipt-a", {**record, "request_hash": "different"}, org_id="org-a", actor_id="actor-a")
    with psycopg.connect(dsn) as conn:
        conn.execute("set local role svc_lskills_librarian")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute("update lskills.provider_releases set manifest='{}'")
