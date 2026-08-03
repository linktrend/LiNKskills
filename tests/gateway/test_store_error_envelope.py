#!/usr/bin/env python3
"""Gateway HTTP boundary: sanitized envelope on unexpected store failures."""

from __future__ import annotations

import json
import sys
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from typing import Any
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
for path in (
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "core",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
):
    sys.path.insert(0, str(path))

from linkskills_gateway.auth import LocalUnsignedClaimsVerifier  # noqa: E402
from linkskills_gateway.auth_testing import mint_test_bearer  # noqa: E402
from linkskills_gateway.persistence import InMemoryGatewayStore  # noqa: E402
from linkskills_gateway.server import create_server  # noqa: E402
from linkskills_gateway.service import SkillsGatewayService  # noqa: E402


class _RlsBoomStore(InMemoryGatewayStore):
    """Store that raises a Postgres-shaped RLS error on atomic writes."""

    def identity(self, actor_id: str, org_id: str):  # type: ignore[override]
        from contextlib import contextmanager

        @contextmanager
        def _ctx():
            yield self

        return _ctx()

    def run_atomic_idempotent(  # type: ignore[override]
        self,
        actor_id: str,
        operation: str,
        key: str,
        request_hash: str,
        mutator: Any,
    ) -> Any:
        raise RuntimeError(
            "new row violates row-level security policy for table idempotency"
        )


class StoreErrorEnvelopeHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        catalog = {
            "skills": [
                {
                    "skill_id": "canary-echo",
                    "version": "0.2.0",
                    "description": "canary",
                    "format_profile": "simple",
                    "eval_suite_ref": "",
                    "certification_state": "usable",
                    "release_hash": "rel-canary",
                    "profile_hash": "prof-canary",
                    "compatible_runtime_profiles": ["cursor-macos"],
                }
            ]
        }
        self.service = SkillsGatewayService(
            repo_root=REPO_ROOT,
            catalog_index=catalog,
            store=_RlsBoomStore(),
        )
        self.httpd = create_server(
            "127.0.0.1",
            0,
            service=self.service,
            verifier=LocalUnsignedClaimsVerifier(),
        )
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.token = mint_test_bearer(
            {
                "actor_id": "openclaw-skills-stage",
                "org_id": "org-stage",
                "actor_kind": "service",
            }
        )

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

    def test_store_rls_failure_returns_structured_500_not_disconnect(self) -> None:
        body = json.dumps(
            {
                "skill_id": "canary-echo",
                "idempotency_key": "stage-rls-boom-1",
            }
        )
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(
            "POST",
            "/v1/skills_run_start",
            body=body,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
                "Idempotency-Key": "stage-rls-boom-1",
            },
        )
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8")
        payload = json.loads(raw)
        self.assertEqual(resp.status, 500, payload)
        self.assertEqual(payload["error"]["code"], "store_error")
        self.assertFalse(payload["error"]["retryable"])
        self.assertNotIn("violates row-level security", raw)
        self.assertNotIn("Traceback", raw)
        self.assertNotIn("password", raw.lower())
        conn.close()

    def test_missing_org_fail_closed_403(self) -> None:
        # In-memory store has no identity(); use a store that advertises identity.
        class _IdentityStore(InMemoryGatewayStore):
            def identity(self, actor_id: str, org_id: str):
                from contextlib import contextmanager

                @contextmanager
                def _ctx():
                    yield self

                return _ctx()

        self.httpd.shutdown()
        self.httpd.server_close()
        service = SkillsGatewayService(
            repo_root=REPO_ROOT,
            catalog_index={
                "skills": [
                    {
                        "skill_id": "canary-echo",
                        "version": "0.2.0",
                        "description": "canary",
                        "format_profile": "simple",
                        "eval_suite_ref": "",
                        "certification_state": "usable",
                        "release_hash": "rel",
                        "profile_hash": "prof",
                        "compatible_runtime_profiles": ["cursor-macos"],
                    }
                ]
            },
            store=_IdentityStore(),
        )
        self.httpd = create_server(
            "127.0.0.1",
            0,
            service=service,
            verifier=LocalUnsignedClaimsVerifier(),
        )
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

        from linkskills_gateway.auth_testing import (
            mint_platform_token,
            snake_claims_to_platform_claims,
        )

        claims = snake_claims_to_platform_claims(
            {
                "actor_id": "svc-no-org",
                "actor_kind": "service",
                "scopes": ["skills:read", "skills:write"],
            }
        )
        claims["orgId"] = None
        token = mint_platform_token(claims)

        body = json.dumps({"skill_id": "canary-echo"})
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(
            "POST",
            "/v1/skills_run_start",
            body=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
                "Idempotency-Key": "no-org-1",
            },
        )
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(resp.status, 403, payload)
        self.assertEqual(payload["error"]["code"], "rls_org_required")
        conn.close()


class PostgresStoreIdentityUnitTests(unittest.TestCase):
    def test_require_rls_identity_rejects_empty_org(self) -> None:
        from linkskills_gateway.postgres_store import PostgresGatewayStore

        with self.assertRaises(ValueError) as ctx:
            PostgresGatewayStore._require_rls_identity("actor-a", "")
        self.assertIn("org_id", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
