#!/usr/bin/env python3
"""PACI token client tests — fake token endpoint + ephemeral ES256 key."""

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
sys.path.insert(0, str(REPO_ROOT / "packages" / "client"))

from linkskills_client.client import SkillsGatewayClient  # noqa: E402
from linkskills_client.paci_token_client import (  # noqa: E402
    ASSERTION_LIFETIME_MAX_S,
    CLIENT_ASSERTION_TYPE,
    PaciAuthError,
    PaciClientConfig,
    PaciConfigError,
    PaciTokenClient,
    PaciTransientError,
    refuse_brain_openclaw_reuse,
)


def _write_ephemeral_es256_pem(path: Path) -> None:
    key = ec.generate_private_key(ec.SECP256R1())
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    path.write_bytes(pem)


class _TokenEndpointState:
    def __init__(self) -> None:
        self.requests: List[Dict[str, Any]] = []
        self.status_code = 200
        self.body: Dict[str, Any] = {
            "access_token": "skills-access-token-1",
            "token_type": "Bearer",
            "expires_in": 900,
        }
        self.fail_times = 0
        self._failures_remaining = 0
        self.seen_assertion_jtis: List[str] = []


def _make_token_server(state: _TokenEndpointState) -> Tuple[HTTPServer, str]:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length).decode("utf-8")
            form = {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}
            state.requests.append({"path": self.path, "form": form})

            assertion = form.get("client_assertion") or ""
            parts = assertion.split(".")
            if len(parts) == 3:
                import base64

                pad = "=" * (-len(parts[1]) % 4)
                claims = json.loads(base64.urlsafe_b64decode(parts[1] + pad))
                jti = str(claims.get("jti") or "")
                if jti:
                    if jti in state.seen_assertion_jtis:
                        payload = json.dumps({"error": "invalid_client", "error_description": "jti replay"}).encode(
                            "utf-8"
                        )
                        self.send_response(401)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(payload)))
                        self.end_headers()
                        self.wfile.write(payload)
                        return
                    state.seen_assertion_jtis.append(jti)

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


class PaciTokenClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.key_path = Path(self._tmpdir.name) / "skills-paci-client.pem"
        _write_ephemeral_es256_pem(self.key_path)
        self.state = _TokenEndpointState()
        self.httpd, self.token_endpoint = _make_token_server(self.state)

    def tearDown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self._tmpdir.cleanup()

    def _client(self, **kwargs: Any) -> PaciTokenClient:
        cfg = PaciClientConfig(
            client_id=kwargs.pop("client_id", "skills-stage-client"),
            token_endpoint=kwargs.pop("token_endpoint", self.token_endpoint),
            private_key_file=kwargs.pop("private_key_file", self.key_path),
            kid=kwargs.pop("kid", "00000000-0000-4000-8000-000000000001"),
            scope=kwargs.pop("scope", "skills:read"),
            resource_audience=kwargs.pop("resource_audience", "lskills-api"),
            assertion_lifetime_s=kwargs.pop("assertion_lifetime_s", ASSERTION_LIFETIME_MAX_S),
            early_renewal_fraction=kwargs.pop("early_renewal_fraction", 0.20),
            max_retries=kwargs.pop("max_retries", 3),
            backoff_base_s=kwargs.pop("backoff_base_s", 0.01),
            timeout_s=kwargs.pop("timeout_s", 5.0),
        )
        return PaciTokenClient(config=cfg)

    def test_mint_client_credentials_private_key_jwt(self) -> None:
        client = self._client()
        token = client.get_access_token()
        self.assertEqual(token, "skills-access-token-1")
        self.assertEqual(len(self.state.requests), 1)
        form = self.state.requests[0]["form"]
        self.assertEqual(form["grant_type"], "client_credentials")
        self.assertEqual(form["client_assertion_type"], CLIENT_ASSERTION_TYPE)
        self.assertEqual(form["client_id"], "skills-stage-client")
        self.assertEqual(form["scope"], "skills:read")
        self.assertTrue(form["client_assertion"])

        # Assertion claims: iss=sub=client_id, aud=token_endpoint, iat/exp/jti
        import base64

        parts = form["client_assertion"].split(".")
        self.assertEqual(len(parts), 3)
        pad = "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(parts[1] + pad))
        self.assertEqual(claims["iss"], "skills-stage-client")
        self.assertEqual(claims["sub"], "skills-stage-client")
        self.assertEqual(claims["aud"], self.token_endpoint)
        self.assertLessEqual(claims["exp"] - claims["iat"], ASSERTION_LIFETIME_MAX_S)
        self.assertTrue(claims["jti"])

        header_pad = "=" * (-len(parts[0]) % 4)
        header = json.loads(base64.urlsafe_b64decode(parts[0] + header_pad))
        self.assertEqual(header["alg"], "ES256")
        self.assertEqual(header["kid"], "00000000-0000-4000-8000-000000000001")

    def test_caches_token_and_ignores_refresh_token(self) -> None:
        self.state.body["refresh_token"] = "must-not-be-used"
        client = self._client()
        t1 = client.get_access_token()
        t2 = client.get_access_token()
        self.assertEqual(t1, t2)
        self.assertEqual(len(self.state.requests), 1)
        self.assertNotIn("refresh_token", client.status())

    def test_early_renewal_when_ttl_below_20_percent(self) -> None:
        self.state.body["expires_in"] = 10
        client = self._client(early_renewal_fraction=0.20)
        client.get_access_token()
        self.assertEqual(len(self.state.requests), 1)
        # Simulate clock near end of lifetime (<20% remaining ⇒ renew).
        assert client._cached is not None
        client._cached.issued_at = time.time() - 9.0
        client._cached.expires_at = time.time() + 1.0
        self.state.body["access_token"] = "skills-access-token-2"
        renewed = client.get_access_token()
        self.assertEqual(renewed, "skills-access-token-2")
        self.assertEqual(len(self.state.requests), 2)
        # Distinct assertion jtis across mints (local replay-safe).
        jtis = self.state.seen_assertion_jtis
        self.assertEqual(len(jtis), 2)
        self.assertNotEqual(jtis[0], jtis[1])

    def test_auth_error_fail_closed_no_retry(self) -> None:
        self.state.status_code = 401
        self.state.body = {"error": "invalid_client"}
        client = self._client(max_retries=3, backoff_base_s=0.01)
        with self.assertRaises(PaciAuthError):
            client.get_access_token()
        self.assertEqual(len(self.state.requests), 1)

    def test_transient_retry_then_success(self) -> None:
        self.state._failures_remaining = 2
        client = self._client(max_retries=3, backoff_base_s=0.01)
        token = client.get_access_token()
        self.assertEqual(token, "skills-access-token-1")
        self.assertGreaterEqual(len(self.state.requests), 3)

    def test_transient_exhausted_raises(self) -> None:
        self.state._failures_remaining = 10
        client = self._client(max_retries=1, backoff_base_s=0.01)
        with self.assertRaises(PaciTransientError):
            client.get_access_token()

    def test_refuse_brain_openclaw_endpoint(self) -> None:
        with self.assertRaises(PaciConfigError):
            PaciClientConfig(
                client_id="skills-stage-client",
                token_endpoint="https://paci.example/openclaw/oauth/token",
                private_key_file=self.key_path,
            )
        with self.assertRaises(PaciConfigError):
            PaciClientConfig(
                client_id="skills-stage-client",
                token_endpoint=self.token_endpoint,
                private_key_file=self.key_path,
                resource_audience="linkbrain-api",
            )
        with self.assertRaises(PaciConfigError):
            refuse_brain_openclaw_reuse()

    def test_private_key_only_via_file_secretref(self) -> None:
        missing = Path(self._tmpdir.name) / "missing.pem"
        with self.assertRaises(PaciConfigError):
            PaciClientConfig(
                client_id="skills-stage-client",
                token_endpoint=self.token_endpoint,
                private_key_file=missing,
            )

    def test_from_env_and_gateway_client_paci_bearer(self) -> None:
        env = {
            "LINKSKILLS_PACI_CLIENT_ID": "skills-stage-client",
            "LINKSKILLS_PACI_TOKEN_ENDPOINT": self.token_endpoint,
            "LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE": str(self.key_path),
            "LINKSKILLS_PACI_SCOPE": "skills:read",
            "LINKSKILLS_AUTH_MODE": "production",
            "GATEWAY_URL": "http://127.0.0.1:9",
        }
        paci = PaciTokenClient.from_env(env)
        self.assertEqual(paci.get_access_token(), "skills-access-token-1")

        # Fake gateway that records Authorization.
        recorded: Dict[str, str] = {}

        class GwHandler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length") or 0)
                self.rfile.read(length)
                recorded["authorization"] = self.headers.get("Authorization") or ""
                body = b'{"ok":true}'
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
            client = SkillsGatewayClient.from_env(
                {**env, "GATEWAY_URL": f"http://127.0.0.1:{port}"},
                paci_client=paci,
            )
            client.call("skills_list", {})
            self.assertEqual(recorded["authorization"], "Bearer skills-access-token-1")
        finally:
            gw.shutdown()
            gw.server_close()

    def test_from_env_rejects_static_bearer_outside_local_test(self) -> None:
        env = {
            "LINKSKILLS_AUTH_MODE": "production",
            "GATEWAY_TOKEN": "static-should-fail",
            "GATEWAY_URL": "http://127.0.0.1:9",
        }
        with self.assertRaises(PaciConfigError):
            SkillsGatewayClient.from_env(env)

    def test_from_env_allows_static_bearer_local_test_only(self) -> None:
        env = {
            "LINKSKILLS_AUTH_MODE": "local-test",
            "LINKSKILLS_LOCAL_TEST_STATIC_BEARER": "local-static",
            "GATEWAY_URL": "http://127.0.0.1:9",
        }
        client = SkillsGatewayClient.from_env(env)
        self.assertIsNone(client.paci_client)
        self.assertEqual(client.authorization, "local-static")

    def test_status_omits_secrets(self) -> None:
        client = self._client()
        client.get_access_token()
        status = client.status()
        dumped = json.dumps(status)
        self.assertNotIn("skills-access-token-1", dumped)
        self.assertNotIn("BEGIN", dumped)
        self.assertFalse(status["live_proven"])
        self.assertEqual(status["domain"], "skills")


if __name__ == "__main__":
    unittest.main()
