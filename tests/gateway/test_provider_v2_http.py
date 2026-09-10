#!/usr/bin/env python3
"""HTTP /v2 production surface, liveness, readiness against fakes, legacy 410."""

from __future__ import annotations

import json
import sys
import threading
import time
import unittest
from http.client import HTTPConnection
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for path in (
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "core",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT / "packages" / "persistence",
    REPO_ROOT / "packages" / "client",
    REPO_ROOT / "packages" / "mcp_server",
    REPO_ROOT,
):
    sys.path.insert(0, str(path))

from linkskills_client.http_v2 import HttpV2Client  # noqa: E402
from linkskills_core.provider_v2 import InMemoryProviderStore, V2Provider  # noqa: E402
from linkskills_gateway.auth import LocalUnsignedClaimsVerifier  # noqa: E402
from linkskills_gateway.auth_testing import mint_test_bearer  # noqa: E402
from linkskills_gateway.server import create_server  # noqa: E402
from linkskills_gateway.service import SkillsGatewayService  # noqa: E402
from linkskills_gateway.v2_http import (  # noqa: E402
    LEGACY_REMOVAL_GATE,
    identity_from_claims,
)


def _claims():
    return {
        "actor_id": "actor-v2",
        "actor_kind": "human",
        "org_id": "org-1",
        "scopes": ["skills:read", "skills:write"],
        "exp": int(time.time()) + 3600,
    }


class ProviderV2HttpTests(unittest.TestCase):
    def setUp(self) -> None:
        catalog = {
            "skills": [
                {
                    "skill_id": "research",
                    "version": "1.0.0",
                    "description": "fixture",
                    "format_profile": "simple",
                    "eval_suite_ref": "",
                    "certification_state": "usable",
                    "release_hash": "rel",
                    "profile_hash": "prof",
                    "compatible_runtime_profiles": ["cursor-macos"],
                }
            ]
        }
        self.service = SkillsGatewayService(repo_root=REPO_ROOT, catalog_index=catalog)
        store = InMemoryProviderStore()
        verifier = LocalUnsignedClaimsVerifier()
        provider = V2Provider(
            lambda token: identity_from_claims(
                verifier.verify(
                    token if token.lower().startswith("bearer ") else f"Bearer {token}",
                    request_payload={},
                    required_operation="skills_list",
                )
            ),
            families=[{"family_id": "research", "display_name": "Research", "description": "R"}],
            releases=[
                {
                    "skill_id": "research",
                    "version": "1.0.0",
                    "family_id": "research",
                    "resources": {"entrypoint": {"body": b"exact-http"}},
                }
            ],
            store=store,
        )
        self.httpd = create_server(
            "127.0.0.1",
            0,
            service=self.service,
            verifier=verifier,
            v2_provider=provider,
        )
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.token = mint_test_bearer(_claims())

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

    def _conn(self) -> HTTPConnection:
        return HTTPConnection("127.0.0.1", self.port, timeout=5)

    def test_health_and_ready_against_fakes(self) -> None:
        conn = self._conn()
        conn.request("GET", "/health")
        health = json.loads(conn.getresponse().read().decode())
        conn.close()
        self.assertEqual(health["status"], "ok")
        conn = self._conn()
        conn.request("GET", "/ready")
        ready_resp = conn.getresponse()
        ready = json.loads(ready_resp.read().decode())
        conn.close()
        self.assertIn(ready_resp.status, {200, 503})
        self.assertIn("ready", ready)
        self.assertEqual(ready["contract_version"], "skills.api.v0.1")
        conn = self._conn()
        conn.request("GET", "/v2/capabilities")
        caps = json.loads(conn.getresponse().read().decode())
        conn.close()
        self.assertEqual(caps["mcp_protocol"], "2026-07-28")
        self.assertFalse(caps["legacy_execution"])
        self.assertIn("retained_v0_1_image", LEGACY_REMOVAL_GATE)
        conn = self._conn()
        conn.request("GET", "/v2/openapi.json")
        spec = json.loads(conn.getresponse().read().decode())
        conn.close()
        self.assertEqual(spec["openapi"], "3.1.0")

    def test_http_conformance_and_legacy_denial(self) -> None:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        conn = self._conn()
        conn.request("POST", "/v2/skills_run_start", body=b"{}", headers=headers)
        denied = conn.getresponse()
        body = json.loads(denied.read().decode())
        conn.close()
        self.assertEqual(denied.status, 410)
        self.assertEqual(body["error"], "legacy_execution_disabled")
        conn = self._conn()
        conn.request(
            "POST",
            "/v2/skills_catalog_list",
            body=json.dumps({"limit": 10}).encode(),
            headers=headers,
        )
        listed = json.loads(conn.getresponse().read().decode())
        conn.close()
        self.assertTrue(listed["ok"])
        client = HttpV2Client(f"http://127.0.0.1:{self.port}", authorization=f"Bearer {self.token}")
        body, digest = client.read_exact(
            "skills_release_resource_get",
            {"skill_id": "research", "version": "1.0.0", "resource_id": "entrypoint"},
        )
        self.assertEqual(body, b"exact-http")
        self.assertTrue(digest.startswith("sha256:"))
        conn = self._conn()
        conn.request(
            "POST",
            "/v2/skills_catalog_list",
            body=b"{}",
            headers={"Content-Type": "application/json"},
        )
        missing = conn.getresponse()
        missing_body = json.loads(missing.read().decode())
        conn.close()
        self.assertEqual(missing.status, 401)
        self.assertEqual(missing_body["error"], "auth_required")

    def test_wrong_protocol_on_http(self) -> None:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        conn = self._conn()
        conn.request(
            "POST",
            "/v2/skills_catalog_list",
            body=json.dumps({"protocol_version": "2024-11-05"}).encode(),
            headers=headers,
        )
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode())
        conn.close()
        self.assertEqual(resp.status, 400)
        self.assertEqual(payload["error"], "contract_incompatible")


class ProductionDefaultV2HttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = SkillsGatewayService(repo_root=REPO_ROOT, catalog_index={"skills": []})
        self.verifier = LocalUnsignedClaimsVerifier()
        self.httpd = create_server(
            "127.0.0.1",
            0,
            service=self.service,
            verifier=self.verifier,
        )
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

    def test_empty_default_cannot_retrieve_exact_resources(self) -> None:
        token = mint_test_bearer(_claims())
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", "/v2/capabilities")
        caps = json.loads(conn.getresponse().read().decode())
        conn.close()
        self.assertFalse(caps["catalog_ready"])
        self.assertEqual(caps["resources"], list(caps["operations"][:13]))
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(
            "POST",
            "/v2/skills_release_resource_get",
            body=json.dumps(
                {"skill_id": "research", "version": "1.0.0", "resource_id": "entrypoint"}
            ).encode(),
            headers=headers,
        )
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode())
        conn.close()
        self.assertEqual(resp.status, 503)
        self.assertEqual(payload["error"], "catalog_unavailable")
        self.assertNotIn("content_b64", payload)
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(
            "POST",
            "/v2/skills_qualification_get",
            body=json.dumps({"skill_id": "research", "version": "1.0.0"}).encode(),
            headers=headers,
        )
        qual = json.loads(conn.getresponse().read().decode())
        conn.close()
        self.assertEqual(qual["error"], "catalog_unavailable")
        self.assertNotEqual(qual.get("qualification"), "qualified")


class TenantBoundReceiptHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        store = InMemoryProviderStore()
        verifier = LocalUnsignedClaimsVerifier()
        provider = V2Provider(
            lambda token: identity_from_claims(
                verifier.verify(
                    token if token.lower().startswith("bearer ") else f"Bearer {token}",
                    request_payload={},
                    required_operation="skills_list",
                )
            ),
            families=[{"family_id": "research", "display_name": "Research", "description": "R"}],
            releases=[
                {
                    "skill_id": "research",
                    "version": "1.0.0",
                    "family_id": "research",
                    "resources": {"entrypoint": {"body": b"exact-http"}},
                }
            ],
            store=store,
        )
        self.httpd = create_server(
            "127.0.0.1",
            0,
            service=SkillsGatewayService(repo_root=REPO_ROOT, catalog_index={"skills": []}),
            verifier=verifier,
            v2_provider=provider,
        )
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

    def _post(self, token: str, operation: str, body: dict) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(
            "POST",
            f"/v2/{operation}",
            body=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode())
        conn.close()
        return resp.status, payload

    def test_cross_org_status_is_not_found_and_read_cannot_write(self) -> None:
        org_a = mint_test_bearer(
            {
                "actor_id": "actor-a",
                "actor_kind": "human",
                "org_id": "org-a",
                "scopes": ["skills:read", "skills:write"],
                "exp": int(time.time()) + 3600,
            }
        )
        org_b = mint_test_bearer(
            {
                "actor_id": "actor-b",
                "actor_kind": "human",
                "org_id": "org-b",
                "scopes": ["skills:read", "skills:write"],
                "exp": int(time.time()) + 3600,
            }
        )
        reader = mint_test_bearer(
            {
                "actor_id": "actor-a",
                "actor_kind": "human",
                "org_id": "org-a",
                "scopes": ["skills:read"],
                "exp": int(time.time()) + 3600,
            }
        )
        report = {
            "schema_version": "0.2",
            "report_kind": "completed_use",
            "report_id": "opaque:report:http-shared",
            "occurred_at": "2026-08-13T00:00:00Z",
            "skill_id": "research",
            "skill_release_ref": "opaque:release:research:1.0.0",
            "consumer_class": "codex",
            "actor_ref": "opaque:actor:a",
            "runtime_profile_ref": "opaque:runtime:codex",
            "outcome": "use_succeeded",
            "opaque_refs": ["opaque:program:run-1"],
            "idempotency_source": "server",
            "score": 10,
        }
        status, first = self._post(
            org_a, "skills_use_report_submit", {"report": report, "client_idempotency_key": "k-a"}
        )
        self.assertEqual(status, 200)
        self.assertTrue(first["ok"])
        status, leak = self._post(
            org_b, "skills_use_report_status_get", {"report_id": "opaque:report:http-shared"}
        )
        self.assertEqual(status, 404)
        self.assertEqual(leak["error"], "not_found")
        status, other = self._post(
            org_b, "skills_use_report_submit", {"report": report, "client_idempotency_key": "k-b"}
        )
        self.assertEqual(status, 200)
        self.assertFalse(other["replay"])
        status, denied = self._post(
            reader, "skills_use_report_submit", {"report": report, "client_idempotency_key": "k-read"}
        )
        self.assertEqual(status, 403)
        self.assertEqual(denied["error"], "forbidden")
        status, own = self._post(
            reader, "skills_use_report_status_get", {"report_id": "opaque:report:http-shared"}
        )
        self.assertEqual(status, 200)
        self.assertEqual(own["status"], "accepted")


class ReadyProbeSanitisationTests(unittest.TestCase):
    def test_broken_store_does_not_leak_dsn(self) -> None:
        scheme = "postgres"
        user = "user"
        secret = "secret"
        host = "10.1.2.3"
        port = "5432"
        database = "skills"
        dsn = f"{scheme}://{user}:{secret}@{host}:{port}/{database}"

        class Boom:
            def probe_reachable(self):
                raise RuntimeError(dsn)

            def get_run(self, run_id: str):
                raise RuntimeError(dsn)

        service = SkillsGatewayService(
            repo_root=REPO_ROOT,
            catalog_index={"skills": []},
            store=Boom(),
        )
        ready = service.ready(probe_store=True, auth_configured=True)
        self.assertFalse(ready["ready"])
        blob = json.dumps(ready)
        self.assertNotIn("secret", blob)
        self.assertNotIn("postgres://", blob)
        self.assertNotIn("10.1.2.3", blob)


if __name__ == "__main__":
    unittest.main()
