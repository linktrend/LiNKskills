#!/usr/bin/env python3
"""PACI stdio MCP proxy tests — mint, renew, 401, retry, no-secret diagnostics."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import parse_qs

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

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

from linkskills_client.client import SkillsGatewayClient  # noqa: E402
from linkskills_client.paci_token_client import (  # noqa: E402
    AUTH_MODE_LOCAL_TEST,
    PaciAuthError,
    PaciClientConfig,
    PaciTokenClient,
)
from linkskills_gateway.auth import AuthError, LocalUnsignedClaimsVerifier  # noqa: E402
from linkskills_gateway.auth_testing import mint_test_bearer  # noqa: E402
from linkskills_gateway.service import SkillsGatewayService  # noqa: E402
from linkskills_mcp.paci_stdio_proxy import (  # noqa: E402
    ENV_ALLOW_INPROCESS_PRODUCTION,
    ENV_UPSTREAM,
    PaciStdioMcpProxy,
    UPSTREAM_HTTP,
    UPSTREAM_IN_PROCESS,
    _resolve_upstream,
    build_paci_client,
    require_durable_inprocess_production,
)
from linkskills_mcp.server import SkillsMcpServer  # noqa: E402


def _write_ephemeral_es256_pem(path: Path) -> None:
    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    path.write_bytes(pem)


def _claims() -> Dict[str, Any]:
    return {
        "actor_id": "actor-paci-proxy",
        "actor_kind": "service",
        "org_id": "org-1",
        "scopes": ["skills:read", "skills:write"],
        "exp": int(time.time()) + 600,
    }


class _TokenEndpointState:
    def __init__(self) -> None:
        self.requests: List[Dict[str, Any]] = []
        self.status_code = 200
        self.body: Dict[str, Any] = {
            "access_token": "placeholder",
            "token_type": "Bearer",
            "expires_in": 900,
        }
        self._failures_remaining = 0


def _make_token_server(state: _TokenEndpointState) -> Tuple[HTTPServer, str]:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length).decode("utf-8")
            form = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}
            state.requests.append({"path": self.path, "form": form})
            if state._failures_remaining > 0:
                state._failures_remaining -= 1
                payload = b'{"error":"server_error"}'
                self.send_response(503)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            payload = json.dumps(state.body).encode("utf-8")
            self.send_response(state.status_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, f"http://127.0.0.1:{port}/oauth/token"


class PaciStdioProxyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.key_path = Path(self._tmpdir.name) / "skills-paci-client.pem"
        _write_ephemeral_es256_pem(self.key_path)
        self.state = _TokenEndpointState()
        self.access_token = mint_test_bearer(_claims())
        self.state.body["access_token"] = self.access_token
        self.httpd, self.token_endpoint = _make_token_server(self.state)
        self.service = SkillsGatewayService(repo_root=REPO_ROOT)
        self.verifier = LocalUnsignedClaimsVerifier()
        self.mcp = SkillsMcpServer(service=self.service, verifier=self.verifier)
        self.paci = PaciTokenClient(
            config=PaciClientConfig(
                client_id="skills-stage-client",
                token_endpoint=self.token_endpoint,
                private_key_file=self.key_path,
                auth_mode=AUTH_MODE_LOCAL_TEST,
                backoff_base_s=0.01,
                max_retries=3,
            )
        )

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self._tmpdir.cleanup()

    def _proxy(self) -> PaciStdioMcpProxy:
        return PaciStdioMcpProxy(
            paci_client=self.paci,
            upstream="in-process",
            mcp_server=self.mcp,
            environ={
                "LINKSKILLS_CANARY": "1",
                "LINKSKILLS_AUTH_MODE": "local-test",
            },
        )

    def test_mint_and_inject_authorization_not_in_tool_args(self) -> None:
        proxy = self._proxy()
        response = proxy.handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "skills_list",
                    "arguments": {
                        "params": {},
                        "authorization": "Bearer attacker-should-be-stripped",
                    },
                },
            }
        )
        assert response is not None
        self.assertIn("result", response)
        structured = response["result"]["structuredContent"]
        self.assertGreater(structured["data"]["count"], 0)
        self.assertEqual(len(self.state.requests), 1)
        # Spoof bearer must not appear in successful path / diagnostics.
        dumped = json.dumps(response)
        self.assertNotIn("attacker-should-be-stripped", dumped)

    def test_early_renewal_before_tools_call(self) -> None:
        proxy = self._proxy()
        proxy.paci_client.get_access_token()
        assert proxy.paci_client._cached is not None
        proxy.paci_client._cached.issued_at = time.time() - 9.0
        proxy.paci_client._cached.expires_at = time.time() + 1.0
        self.state.body["expires_in"] = 10
        self.state.body["access_token"] = mint_test_bearer(_claims())
        proxy.handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "skills_list", "arguments": {"params": {}}},
            }
        )
        self.assertGreaterEqual(len(self.state.requests), 2)

    def test_expiry_renewal(self) -> None:
        proxy = self._proxy()
        proxy.paci_client.get_access_token()
        assert proxy.paci_client._cached is not None
        proxy.paci_client._cached.expires_at = time.time() - 1.0
        self.state.body["access_token"] = mint_test_bearer(_claims())
        response = proxy.handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "skills_list", "arguments": {"params": {}}},
            }
        )
        assert response is not None
        self.assertIn("result", response)
        self.assertEqual(len(self.state.requests), 2)

    def test_auth_error_fail_closed(self) -> None:
        self.state.status_code = 401
        self.state.body = {"error": "invalid_client"}
        with self.assertRaises(PaciAuthError):
            self.paci.get_access_token()
        self.assertEqual(len(self.state.requests), 1)

    def test_bounded_transient_retry(self) -> None:
        self.state._failures_remaining = 2
        token = self.paci.get_access_token()
        self.assertEqual(token, self.access_token)
        self.assertGreaterEqual(len(self.state.requests), 3)

    def test_status_omits_secrets(self) -> None:
        proxy = self._proxy()
        proxy.paci_client.get_access_token()
        status = proxy.status()
        dumped = json.dumps(status)
        self.assertNotIn(self.access_token, dumped)
        self.assertNotIn("BEGIN", dumped)
        self.assertFalse(status["live_proven"])
        response = proxy.handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 99,
                "method": "linkskills/paci_status",
                "params": {},
            }
        )
        assert response is not None
        self.assertNotIn(self.access_token, json.dumps(response))

    def test_build_paci_client_refuses_canary_static_bearer(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            build_paci_client(
                {
                    "LINKSKILLS_CANARY": "1",
                    "LINKSKILLS_AUTH_MODE": "production",
                    "LINKSKILLS_CANARY_AUTHORIZATION": "Bearer static",
                    "LINKSKILLS_PACI_CLIENT_ID": "x",
                    "LINKSKILLS_PACI_TOKEN_ENDPOINT": "https://paci.example/token",
                    "LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE": str(self.key_path),
                }
            )
        self.assertIn("static bearer", str(ctx.exception).lower())

    def test_build_paci_client_requires_paci_env(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            build_paci_client(
                {
                    "LINKSKILLS_CANARY": "1",
                    "LINKSKILLS_AUTH_MODE": "production",
                }
            )
        self.assertIn("PACI env incomplete", str(ctx.exception))

    def test_http_upstream_injects_authorization_header(self) -> None:
        recorded: List[str] = []

        class GwHandler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length") or 0)
                self.rfile.read(length)
                recorded.append(self.headers.get("Authorization") or "")
                body = json.dumps(
                    {
                        "data": {"skills": [], "count": 0},
                        "error": None,
                    }
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
                return

        gw = HTTPServer(("127.0.0.1", 0), GwHandler)
        port = gw.server_address[1]
        thread = threading.Thread(target=gw.serve_forever, daemon=True)
        thread.start()
        try:
            gateway = SkillsGatewayClient(
                base_url=f"http://127.0.0.1:{port}",
                paci_client=self.paci,
                auth_mode=AUTH_MODE_LOCAL_TEST,
            )
            proxy = PaciStdioMcpProxy(
                paci_client=self.paci,
                upstream="http",
                gateway_client=gateway,
                environ={"LINKSKILLS_AUTH_MODE": "local-test"},
            )
            response = proxy.handle_rpc(
                {
                    "jsonrpc": "2.0",
                    "id": 7,
                    "method": "tools/call",
                    "params": {
                        "name": "skills_list",
                        "arguments": {
                            "params": {},
                            "authorization": "Bearer must-not-reach-gateway",
                        },
                    },
                }
            )
            assert response is not None
            self.assertIn("result", response)
            self.assertEqual(len(recorded), 1)
            self.assertEqual(recorded[0], f"Bearer {self.access_token}")
            self.assertNotIn("must-not-reach-gateway", recorded[0])
        finally:
            gw.shutdown()
            gw.server_close()

    def test_in_process_401_style_invalidation_retries_once(self) -> None:
        """AuthError on first call → invalidate + remint once."""
        proxy = self._proxy()
        calls = {"n": 0}
        original = self.mcp.call_tool

        def flaky_call_tool(*args: Any, **kwargs: Any) -> Any:
            calls["n"] += 1
            if calls["n"] == 1:
                raise AuthError("auth_expired", "Claims expired")
            return original(*args, **kwargs)

        self.mcp.call_tool = flaky_call_tool  # type: ignore[method-assign]
        self.state.body["access_token"] = mint_test_bearer(_claims())
        response = proxy.handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {"name": "skills_list", "arguments": {"params": {}}},
            }
        )
        assert response is not None
        self.assertIn("result", response)
        self.assertEqual(calls["n"], 2)
        self.assertGreaterEqual(len(self.state.requests), 2)

    def test_production_defaults_upstream_to_http(self) -> None:
        self.assertEqual(
            _resolve_upstream({"LINKSKILLS_AUTH_MODE": "production"}),
            UPSTREAM_HTTP,
        )
        self.assertEqual(
            _resolve_upstream({"LINKSKILLS_CANARY": "1"}),
            UPSTREAM_HTTP,
        )

    def test_local_test_defaults_upstream_to_in_process(self) -> None:
        self.assertEqual(
            _resolve_upstream({"LINKSKILLS_AUTH_MODE": "local-test"}),
            UPSTREAM_IN_PROCESS,
        )

    def test_production_inprocess_without_allow_fails_closed(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            PaciStdioMcpProxy(
                paci_client=self.paci,
                upstream=UPSTREAM_IN_PROCESS,
                mcp_server=self.mcp,
                environ={
                    "LINKSKILLS_AUTH_MODE": "production",
                    "LINKSKILLS_CANARY": "1",
                },
            )
        msg = str(ctx.exception).lower()
        self.assertIn("refuses in-process", msg)
        self.assertIn("in-memory", msg)

    def test_production_inprocess_missing_env_fails_closed(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            require_durable_inprocess_production(
                {
                    ENV_ALLOW_INPROCESS_PRODUCTION: "1",
                    "LINKSKILLS_AUTH_MODE": "production",
                    "LINKSKILLS_GATEWAY_STORE": "postgres",
                    "LINKSKILLS_DATABASE_URL": "postgresql://example/db",
                }
            )
        self.assertIn("LINKSKILLS_ENV", str(ctx.exception))

    def test_production_inprocess_missing_dsn_fails_closed(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            require_durable_inprocess_production(
                {
                    ENV_ALLOW_INPROCESS_PRODUCTION: "1",
                    "LINKSKILLS_AUTH_MODE": "production",
                    "LINKSKILLS_ENV": "stage",
                    "LINKSKILLS_GATEWAY_STORE": "postgres",
                }
            )
        msg = str(ctx.exception)
        self.assertIn("DATABASE_URL", msg)
        self.assertIn("in-memory", msg.lower())

    def test_production_inprocess_allowed_with_postgres_proof(self) -> None:
        # Gate only — do not open a real postgres connection here.
        require_durable_inprocess_production(
            {
                ENV_ALLOW_INPROCESS_PRODUCTION: "1",
                "LINKSKILLS_AUTH_MODE": "production",
                "LINKSKILLS_ENV": "stage",
                "LINKSKILLS_GATEWAY_STORE": "postgres",
                "LINKSKILLS_DATABASE_URL": "postgresql://skills:skills@127.0.0.1:5432/skills",
            }
        )
        proxy = PaciStdioMcpProxy(
            paci_client=self.paci,
            upstream=UPSTREAM_IN_PROCESS,
            mcp_server=self.mcp,
            environ={
                ENV_ALLOW_INPROCESS_PRODUCTION: "1",
                "LINKSKILLS_AUTH_MODE": "production",
                "LINKSKILLS_ENV": "stage",
                "LINKSKILLS_GATEWAY_STORE": "postgres",
                "LINKSKILLS_DATABASE_URL": "postgresql://skills:skills@127.0.0.1:5432/skills",
            },
        )
        self.assertEqual(proxy.upstream, UPSTREAM_IN_PROCESS)

    def test_production_http_requires_https_gateway_url(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            PaciStdioMcpProxy(
                paci_client=self.paci,
                upstream=UPSTREAM_HTTP,
                gateway_client=SkillsGatewayClient(
                    base_url="http://127.0.0.1:9",
                    paci_client=self.paci,
                    auth_mode=AUTH_MODE_LOCAL_TEST,
                ),
                environ={
                    "LINKSKILLS_AUTH_MODE": "production",
                    "LINKSKILLS_CANARY": "1",
                },
            )
        self.assertIn("GATEWAY_URL", str(ctx.exception))

    def test_production_http_upstream_with_https_gateway(self) -> None:
        gateway = SkillsGatewayClient(
            base_url="https://skills-stage.example.invalid",
            paci_client=self.paci,
            auth_mode="production",
        )
        proxy = PaciStdioMcpProxy(
            paci_client=self.paci,
            upstream=UPSTREAM_HTTP,
            gateway_client=gateway,
            environ={
                "LINKSKILLS_AUTH_MODE": "production",
                "LINKSKILLS_CANARY": "1",
                "GATEWAY_URL": "https://skills-stage.example.invalid",
                ENV_UPSTREAM: UPSTREAM_HTTP,
            },
        )
        self.assertEqual(proxy.upstream, UPSTREAM_HTTP)
        status = proxy.status()
        self.assertEqual(status["upstream"], UPSTREAM_HTTP)
        self.assertEqual(status["auth_mode"], "production")

    def test_local_test_inprocess_still_works(self) -> None:
        proxy = self._proxy()
        self.assertEqual(proxy.upstream, UPSTREAM_IN_PROCESS)
        response = proxy.handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/list",
                "params": {},
            }
        )
        assert response is not None
        self.assertIn("result", response)
        self.assertGreater(len(response["result"]["tools"]), 0)


if __name__ == "__main__":
    unittest.main()
