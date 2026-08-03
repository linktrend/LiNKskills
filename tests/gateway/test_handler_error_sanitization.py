#!/usr/bin/env python3
"""HTTP handler must return sanitized envelopes on unexpected store faults."""

from __future__ import annotations

import json
import sys
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATHS = [
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "core",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
]
for path in PACKAGE_PATHS:
    sys.path.insert(0, str(path))

from linkskills_gateway.auth import LocalUnsignedClaimsVerifier  # noqa: E402
from linkskills_gateway.auth_testing import mint_test_bearer  # noqa: E402
from linkskills_gateway.ops import DrainState, GatewayMetrics  # noqa: E402
from linkskills_gateway.persistence import IdempotencyReserveResult  # noqa: E402
from linkskills_gateway.server import create_server  # noqa: E402
from linkskills_gateway.service import SkillsGatewayService  # noqa: E402


class _RlsBoomStore:
    """Store that raises a psycopg-shaped RLS privilege error on atomic write."""

    def identity(self, actor_id: str, org_id: str):
        from contextlib import contextmanager

        @contextmanager
        def _ctx():
            yield self

        return _ctx()

    def run_atomic_idempotent(
        self,
        actor_id: str,
        operation: str,
        key: str,
        request_hash: str,
        mutator: Any,
    ) -> IdempotencyReserveResult:
        del actor_id, operation, key, request_hash, mutator
        err = type("InsufficientPrivilege", (Exception,), {})(
            "new row violates row-level security policy for table idempotency"
        )
        raise err

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        del run_id
        return None


class HandlerErrorSanitizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.token = mint_test_bearer(
            {
                "actor_id": "actor-a",
                "org_id": "org-a",
                "scopes": ["lskills", "skills:write", "skills:run"],
            }
        )
        service = SkillsGatewayService(
            repo_root=REPO_ROOT,
            store=_RlsBoomStore(),  # type: ignore[arg-type]
        )
        self.httpd = create_server(
            "127.0.0.1",
            0,
            service=service,
            verifier=LocalUnsignedClaimsVerifier(),
            metrics=GatewayMetrics(),
            drain=DrainState(),
            environ={"LINKSKILLS_AUTH_MODE": "local-test"},
        )
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

    def _post(self, path: str, body: Mapping[str, Any]) -> tuple[int, Dict[str, Any]]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            payload = json.dumps(body).encode("utf-8")
            conn.request(
                "POST",
                path,
                body=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.token}",
                    "Idempotency-Key": "sanitize-key-1",
                },
            )
            resp = conn.getresponse()
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw)
        finally:
            conn.close()

    def test_rls_privilege_error_returns_sanitized_store_error(self) -> None:
        status, payload = self._post(
            "/v1/skills_run_start",
            {"params": {"skill_id": "canary-echo", "version": "1.0.0"}},
        )
        self.assertEqual(status, 500, payload)
        err = payload.get("error") or {}
        self.assertEqual(err.get("code"), "store_error")
        self.assertEqual(err.get("message"), "Persistence rejected the write (sanitized)")
        self.assertFalse(err.get("retryable"))
        blob = json.dumps(payload)
        self.assertNotIn("row-level security", blob.lower())
        self.assertNotIn("InsufficientPrivilege", blob)
        self.assertNotIn("violates", blob.lower())


if __name__ == "__main__":
    unittest.main()
