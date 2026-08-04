#!/usr/bin/env python3
"""Gateway health / ready / metrics / drain surface tests (Lane 4)."""

from __future__ import annotations

import json
import os
import sys
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from typing import Any, Dict, Optional

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
from linkskills_gateway.ops import (  # noqa: E402
    DrainState,
    GatewayMetrics,
    auth_config_present,
)
from linkskills_gateway.server import create_server  # noqa: E402
from linkskills_gateway.service import SkillsGatewayService  # noqa: E402


class _BrokenStore:
    """Store that fails probe_reachable for ready tests."""

    def probe_reachable(self) -> bool:
        raise RuntimeError("store_down")

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        raise RuntimeError("store_down")


class OpsUnitTests(unittest.TestCase):
    def test_auth_config_local_test(self) -> None:
        ok, mode, detail = auth_config_present({"LINKSKILLS_AUTH_MODE": "local-test"})
        self.assertTrue(ok)
        self.assertEqual(mode, "local-test")
        self.assertEqual(detail, "local-test")

    def test_auth_config_production_requires_authenticator_env_without_import(self) -> None:
        ok, mode, detail = auth_config_present(
            {
                "LINKSKILLS_AUTH_MODE": "production",
                "LINKSKILLS_PLATFORM_AUTHENTICATOR": "",
            }
        )
        self.assertFalse(ok)
        self.assertEqual(mode, "production")
        self.assertEqual(detail, "missing_authenticator_env")

        ok2, mode2, detail2 = auth_config_present(
            {
                "LINKSKILLS_AUTH_MODE": "production",
                "LINKSKILLS_PLATFORM_AUTHENTICATOR": "some.module:Factory",
            }
        )
        self.assertTrue(ok2)
        self.assertEqual(mode2, "production")
        self.assertEqual(detail2, "authenticator_env_present")

    def test_metrics_prometheus_has_no_secret_shaped_values(self) -> None:
        metrics = GatewayMetrics()
        metrics.inc_request()
        metrics.inc_auth_fail()
        text = metrics.render_prometheus(ready_gauge=1, draining_gauge=0)
        self.assertIn("linkskills_gateway_requests_total 1", text)
        self.assertIn("linkskills_gateway_auth_fail_total 1", text)
        self.assertIn("linkskills_gateway_ready 1", text)
        self.assertNotIn("Bearer", text)
        self.assertNotIn("secret", text.lower())
        self.assertNotIn("platform.", text)


class HttpOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.metrics = GatewayMetrics()
        self.drain = DrainState()
        self.env = {
            "LINKSKILLS_AUTH_MODE": "local-test",
            "LINKSKILLS_STORE_PROBE": "0",
            "LINKSKILLS_GATEWAY_DURABLE": "0",
        }
        self.httpd = create_server(
            "127.0.0.1",
            0,
            service=SkillsGatewayService(repo_root=REPO_ROOT),
            verifier=LocalUnsignedClaimsVerifier(),
            metrics=self.metrics,
            drain=self.drain,
            environ=self.env,
        )
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.token = mint_test_bearer()

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

    def _get(self, path: str) -> tuple[int, Any, str]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", path)
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8")
        status = resp.status
        ctype = resp.getheader("Content-Type") or ""
        conn.close()
        if "json" in ctype:
            return status, json.loads(raw), raw
        return status, raw, raw

    def _post(self, path: str, body: Optional[Dict[str, Any]] = None, **headers: str) -> tuple[int, Any]:
        payload = json.dumps(body or {})
        hdrs = {
            "Content-Type": "application/json",
            "Content-Length": str(len(payload)),
        }
        hdrs.update(headers)
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("POST", path, body=payload, headers=hdrs)
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8")
        status = resp.status
        conn.close()
        return status, json.loads(raw)

    def test_health_is_liveness_only(self) -> None:
        status, payload, _ = self._get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "linkskills-gateway")
        self.assertNotIn("ready", payload)
        self.assertNotIn("auth_configured", payload)

    def test_ready_ok_when_catalog_and_local_test_auth(self) -> None:
        status, payload, _ = self._get("/ready")
        self.assertEqual(status, 200, payload)
        self.assertTrue(payload["ready"])
        self.assertTrue(payload["catalog_loaded"])
        self.assertTrue(payload["auth_configured"])
        self.assertEqual(payload["auth_mode"], "local-test")
        self.assertFalse(payload["draining"])
        self.assertEqual(payload["store_probe"], "skipped")

    def test_ready_fails_when_production_authenticator_env_missing(self) -> None:
        # Rebuild server with production env lacking authenticator ref.
        self.httpd.shutdown()
        self.httpd.server_close()
        env = {
            "LINKSKILLS_AUTH_MODE": "production",
            # Intentionally absent: LINKSKILLS_PLATFORM_AUTHENTICATOR
        }
        self.httpd = create_server(
            "127.0.0.1",
            0,
            service=SkillsGatewayService(repo_root=REPO_ROOT),
            verifier=LocalUnsignedClaimsVerifier(),
            metrics=GatewayMetrics(),
            drain=DrainState(),
            environ=env,
        )
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

        status, payload, _ = self._get("/ready")
        self.assertEqual(status, 503, payload)
        self.assertFalse(payload["ready"])
        self.assertFalse(payload["auth_configured"])
        self.assertEqual(payload["auth_mode"], "production")
        self.assertEqual(payload["auth_detail"], "missing_authenticator_env")

    def test_metrics_text_exposition(self) -> None:
        self._get("/health")
        self._get("/ready")
        status, body, raw = self._get("/metrics")
        self.assertEqual(status, 200)
        self.assertIsInstance(body, str)
        self.assertIn("linkskills_gateway_requests_total", raw)
        self.assertIn("linkskills_gateway_auth_fail_total", raw)
        self.assertIn("linkskills_gateway_ready", raw)
        self.assertNotIn(self.token, raw)

    def test_drain_rejects_new_work_health_stays_up(self) -> None:
        status, payload = self._post("/drain", {"reason": "test-cutover"})
        self.assertEqual(status, 200, payload)
        self.assertTrue(payload["draining"])

        ready_status, ready, _ = self._get("/ready")
        self.assertEqual(ready_status, 503, ready)
        self.assertTrue(ready["draining"])
        self.assertFalse(ready["ready"])

        health_status, health, _ = self._get("/health")
        self.assertEqual(health_status, 200)
        self.assertEqual(health["status"], "ok")

        op_status, op = self._post(
            "/v1/skills_list",
            {},
            Authorization=f"Bearer {self.token}",
        )
        self.assertEqual(op_status, 503, op)
        self.assertEqual(op["error"]["code"], "draining")
        self.assertTrue(op["error"]["retryable"])

        cancel_status, cancel = self._post("/drain/cancel")
        self.assertEqual(cancel_status, 200, cancel)
        self.assertFalse(cancel["draining"])

        ready2_status, ready2, _ = self._get("/ready")
        self.assertEqual(ready2_status, 200, ready2)
        self.assertTrue(ready2["ready"])

        op2_status, op2 = self._post(
            "/v1/skills_list",
            {},
            Authorization=f"Bearer {self.token}",
        )
        self.assertEqual(op2_status, 200, op2)
        self.assertIsNone(op2.get("error"))

    def test_auth_fail_increments_metrics(self) -> None:
        before = self.metrics.snapshot()["auth_fail_total"]
        status, _ = self._post("/v1/skills_list", {})
        self.assertIn(status, {401, 403})
        after = self.metrics.snapshot()["auth_fail_total"]
        self.assertEqual(after, before + 1)

    def test_store_probe_failure_marks_not_ready(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        env = {
            "LINKSKILLS_AUTH_MODE": "local-test",
            "LINKSKILLS_STORE_PROBE": "1",
        }
        service = SkillsGatewayService(repo_root=REPO_ROOT, store=_BrokenStore())  # type: ignore[arg-type]
        self.httpd = create_server(
            "127.0.0.1",
            0,
            service=service,
            verifier=LocalUnsignedClaimsVerifier(),
            metrics=GatewayMetrics(),
            drain=DrainState(),
            environ=env,
        )
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

        status, payload, _ = self._get("/ready")
        self.assertEqual(status, 503, payload)
        self.assertFalse(payload["ready"])
        self.assertEqual(payload["store_probe"], "configured")
        self.assertFalse(payload["store_reachable"])
        self.assertEqual(payload.get("store_error"), "RuntimeError")


class EnvDrainStartupTests(unittest.TestCase):
    def test_env_drain_starts_draining(self) -> None:
        env = {
            "LINKSKILLS_AUTH_MODE": "local-test",
            "LINKSKILLS_DRAIN": "1",
        }
        httpd = create_server(
            "127.0.0.1",
            0,
            service=SkillsGatewayService(repo_root=REPO_ROOT),
            verifier=LocalUnsignedClaimsVerifier(),
            environ=env,
        )
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            conn = HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("GET", "/drain")
            resp = conn.getresponse()
            payload = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(resp.status, 200)
            self.assertTrue(payload["draining"])
            self.assertIn("LINKSKILLS_DRAIN", payload["reason"])
            conn.close()
        finally:
            httpd.shutdown()
            httpd.server_close()


if __name__ == "__main__":
    unittest.main()
