"""Stdlib HTTP JSON API for LiNKskills Gateway.

Routes:
  GET  /health
  GET  /ready
  POST /v1/{operation}

Compatibility note: ``packages/client/linkskills_client/compat.py`` wraps
``lib.skill_runtime`` so existing Python consumers can migrate toward this
gateway without an immediate cutover.
"""

from __future__ import annotations

import json
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple, Type
from urllib.parse import urlparse

from .auth import AuthError, FakePlatformClaimsVerifier
from .service import OPERATIONS, ServiceError, SkillsGatewayService


def _json_bytes(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def make_handler(
    service: SkillsGatewayService,
    verifier: Optional[FakePlatformClaimsVerifier] = None,
) -> Type[BaseHTTPRequestHandler]:
    auth = verifier or FakePlatformClaimsVerifier()

    class LiNKskillsGateway(BaseHTTPRequestHandler):
        server_version = "LiNKskillsGateway/0.1"

        def log_message(self, fmt: str, *args: Any) -> None:
            # Quiet by default; tests and operators can wrap if needed.
            return

        def _send(self, status: int, payload: Dict[str, Any]) -> None:
            body = _json_bytes(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
            length = int(self.headers.get("Content-Length") or "0")
            if length <= 0:
                return {}, None
            if length > 1_000_000:
                return None, "payload_too_large"
            raw = self.rfile.read(length)
            try:
                data = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return None, "invalid_json"
            if data is None:
                return {}, None
            if not isinstance(data, dict):
                return None, "json_object_required"
            return data, None

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path.rstrip("/") or "/"
            if path == "/health":
                self._send(200, service.health())
                return
            if path == "/ready":
                ready = service.ready()
                self._send(200 if ready.get("ready") else 503, ready)
                return
            self._send(
                404,
                {
                    "error": {
                        "code": "not_found",
                        "message": f"Unknown path: {path}",
                        "retryable": False,
                    }
                },
            )

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path.rstrip("/") or "/"
            prefix = "/v1/"
            if not path.startswith(prefix):
                self._send(
                    404,
                    {
                        "error": {
                            "code": "not_found",
                            "message": f"Unknown path: {path}",
                            "retryable": False,
                        }
                    },
                )
                return

            operation = path[len(prefix) :]
            if operation not in OPERATIONS:
                self._send(
                    404,
                    {
                        "error": {
                            "code": "unknown_operation",
                            "message": f"Unknown operation: {operation}",
                            "retryable": False,
                        }
                    },
                )
                return

            body, err = self._read_json()
            if err:
                self._send(
                    400,
                    {
                        "error": {
                            "code": err,
                            "message": err.replace("_", " "),
                            "retryable": False,
                        }
                    },
                )
                return

            assert body is not None
            request_id = str(
                self.headers.get("X-Request-Id")
                or body.get("request_id")
                or uuid.uuid4()
            )
            # Idempotency-Key header is authoritative for run_start retries.
            idempotency_key = self.headers.get("Idempotency-Key") or body.get(
                "idempotency_key"
            )
            params = body.get("params") if isinstance(body.get("params"), dict) else body

            # Strip envelope-only keys when body is used as params.
            if "params" not in body:
                params = {
                    k: v
                    for k, v in params.items()
                    if k
                    not in {
                        "request_id",
                        "idempotency_key",
                        "actor_id",
                        "actor_kind",
                        "org_id",
                        "scopes",
                        "exp",
                        "credential_id",
                        "platform_actor_id",
                        "actor",
                        "identity",
                        "claims",
                        "platform_claims",
                    }
                }

            authorization = self.headers.get("Authorization")
            try:
                # Pass original body + headers so spoofed identity is visible.
                # Never accept X-Actor-* override headers as authority.
                actor = auth.verify(
                    authorization,
                    request_payload=body,
                    request_headers=dict(self.headers.items()),
                )
                envelope = service.dispatch(
                    operation,
                    params,
                    actor=actor,
                    request_id=request_id,
                    idempotency_key=str(idempotency_key) if idempotency_key else None,
                )
                self._send(200, envelope)
            except AuthError as exc:
                status = 401
                if exc.code in {"auth_forbidden", "auth_spoof_rejected"}:
                    status = 403
                self._send(
                    status,
                    service.envelope(
                        actor=None,
                        operation=operation,
                        request_id=request_id,
                        idempotency_id=str(idempotency_key) if idempotency_key else None,
                        error={
                            "code": exc.code,
                            "message": exc.message,
                            "retryable": False,
                        },
                    ),
                )
            except ServiceError as exc:
                self._send(
                    exc.http_status,
                    service.envelope(
                        actor=None,
                        operation=operation,
                        request_id=request_id,
                        idempotency_id=str(idempotency_key) if idempotency_key else None,
                        error={
                            "code": exc.code,
                            "message": exc.message,
                            "retryable": exc.retryable,
                        },
                    ),
                )

    return LiNKskillsGateway


def create_server(
    host: str = "127.0.0.1",
    port: int = 8787,
    *,
    service: Optional[SkillsGatewayService] = None,
    verifier: Optional[FakePlatformClaimsVerifier] = None,
) -> ThreadingHTTPServer:
    svc = service or SkillsGatewayService()
    handler = make_handler(svc, verifier=verifier)
    return ThreadingHTTPServer((host, port), handler)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="LiNKskills Gateway HTTP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    httpd = create_server(args.host, args.port)
    print(f"linkskills-gateway listening on http://{args.host}:{args.port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
