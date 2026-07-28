#!/usr/bin/env python3
"""Client package tests — LocalEventBuffer + compat gateway/fallback + flush fail-closed."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for path in (
    REPO_ROOT / "packages" / "gateway",
    REPO_ROOT / "packages" / "mcp_server",
    REPO_ROOT / "packages" / "client",
    REPO_ROOT / "packages" / "librarian_domain",
    REPO_ROOT / "packages" / "eval_runner",
    REPO_ROOT / "packages" / "contracts",
    REPO_ROOT,
):
    sys.path.insert(0, str(path))

from linkskills_client.client import LocalEventBuffer, SkillsGatewayClient  # noqa: E402
from linkskills_client.compat import load_skill, record_invocation  # noqa: E402
from linkskills_gateway.auth import LocalUnsignedClaimsVerifier  # noqa: E402
from linkskills_gateway.auth_testing import mint_test_bearer  # noqa: E402
from linkskills_gateway.server import create_server  # noqa: E402
from linkskills_gateway.service import SkillsGatewayService  # noqa: E402
from lib.skill_runtime.loader import SkillBundle  # noqa: E402


def _claims():
    return {
        "actor_id": "actor-client",
        "actor_kind": "human",
        "org_id": "org-1",
        "scopes": ["skills:read", "skills:write"],
        "exp": int(time.time()) + 3600,
    }


class LocalEventBufferTests(unittest.TestCase):
    def test_append_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            buf = LocalEventBuffer(Path(tmp) / "events.jsonl")
            event = buf.append("skills_feedback_submit", {"skill_id": "x"})
            loaded = buf.load()
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].event_id, event.event_id)


class CompatTests(unittest.TestCase):
    def test_load_skill_falls_back_without_gateway_url(self) -> None:
        os.environ.pop("GATEWAY_URL", None)
        bundle = load_skill("git-safeguard", repo_root=REPO_ROOT, require_usable=False)
        self.assertIsInstance(bundle, SkillBundle)
        self.assertEqual(bundle.skill_id, "git-safeguard")

    def test_load_skill_via_gateway_when_configured(self) -> None:
        service = SkillsGatewayService(repo_root=REPO_ROOT)
        httpd = create_server(
            "127.0.0.1",
            0,
            service=service,
            verifier=LocalUnsignedClaimsVerifier(),
        )
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        token = mint_test_bearer(_claims())
        os.environ["GATEWAY_URL"] = f"http://127.0.0.1:{port}"
        try:
            client = SkillsGatewayClient(
                base_url=os.environ["GATEWAY_URL"],
                authorization=f"Bearer {token}",
            )
            result = load_skill(
                "git-safeguard",
                require_usable=False,
                client=client,
            )
            self.assertEqual(result["source"], "gateway")
            self.assertEqual(result["skill_id"], "git-safeguard")
        finally:
            os.environ.pop("GATEWAY_URL", None)
            httpd.shutdown()
            httpd.server_close()

    def test_record_invocation_buffers_mapped_feedback_shape(self) -> None:
        os.environ["GATEWAY_URL"] = "http://127.0.0.1:1"
        with tempfile.TemporaryDirectory() as tmp:
            client = SkillsGatewayClient(
                base_url=os.environ["GATEWAY_URL"],
                authorization=f"Bearer {mint_test_bearer(_claims())}",
                event_buffer=LocalEventBuffer(Path(tmp) / "buf.jsonl"),
                timeout_s=0.2,
            )
            result = record_invocation(
                {"skill": "git-safeguard", "status": "failed", "summary": "offline"},
                client=client,
            )
            self.assertEqual(result["source"], "gateway_buffered")
            pending = client.event_buffer.load()
            self.assertEqual(len(pending), 1)
            payload = pending[0].payload
            self.assertEqual(payload["skill_id"], "git-safeguard")
            self.assertEqual(payload["kind"], "invocation")
            self.assertEqual(payload["outcome"], "failed")
            self.assertEqual(payload["notes"], "offline")
            self.assertNotIn("skill", payload)
            self.assertNotIn("status", payload)
            self.assertNotIn("summary", payload)
        os.environ.pop("GATEWAY_URL", None)


class FlushFailClosedTests(unittest.TestCase):
    def test_http_4xx_does_not_remove_or_count_written(self) -> None:
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length") or 0)
                self.rfile.read(length)
                body = json.dumps({"error": {"code": "auth_forbidden", "message": "no"}}).encode(
                    "utf-8"
                )
                self.send_response(403)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):  # noqa: A003
                return

        httpd = HTTPServer(("127.0.0.1", 0), Handler)
        port = httpd.server_address[1]
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                buf_path = Path(tmp) / "buf.jsonl"
                client = SkillsGatewayClient(
                    base_url=f"http://127.0.0.1:{port}",
                    authorization="Bearer unused",
                    event_buffer=LocalEventBuffer(buf_path),
                    timeout_s=2.0,
                )
                client.buffer_event(
                    "skills_feedback_submit",
                    {
                        "skill_id": "git-safeguard",
                        "kind": "invocation",
                        "outcome": "failed",
                    },
                )
                result = client.flush_buffered_events()
                self.assertEqual(result["written"], 0)
                self.assertEqual(result["failed"], 1)
                self.assertEqual(result["remaining"], 1)
                remaining = client.event_buffer.load()
                self.assertEqual(len(remaining), 1)
                self.assertEqual(remaining[0].payload["skill_id"], "git-safeguard")
                self.assertGreaterEqual(remaining[0].attempts, 1)
        finally:
            httpd.shutdown()
            httpd.server_close()


if __name__ == "__main__":
    unittest.main()
