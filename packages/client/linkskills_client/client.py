"""HTTP client + offline LocalEventBuffer for LiNKskills Gateway."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .paci_token_client import (
    AUTH_MODE_LOCAL_TEST,
    GATEWAY_401_RETRY_MAX,
    PaciConfigError,
    PaciTokenClient,
    is_loopback_host,
    paci_env_configured,
    require_https_outside_local_test,
    resolve_auth_mode,
)


@dataclass
class BufferedEvent:
    """One offline telemetry / run event awaiting flush."""

    event_type: str
    payload: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    attempts: int = 0


class LocalEventBuffer:
    """Append-only local buffer for offline Gateway telemetry events."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path or Path.cwd() / ".linkskills_event_buffer.jsonl")

    def append(self, event_type: str, payload: Mapping[str, Any]) -> BufferedEvent:
        event = BufferedEvent(event_type=event_type, payload=dict(payload))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "payload": event.payload,
                        "created_at": event.created_at,
                        "attempts": event.attempts,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
        return event

    def load(self) -> List[BufferedEvent]:
        if not self.path.is_file():
            return []
        events: List[BufferedEvent] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            events.append(
                BufferedEvent(
                    event_id=str(raw.get("event_id") or uuid.uuid4()),
                    event_type=str(raw.get("event_type") or "unknown"),
                    payload=dict(raw.get("payload") or {}),
                    created_at=float(raw.get("created_at") or time.time()),
                    attempts=int(raw.get("attempts") or 0),
                )
            )
        return events

    def rewrite(self, events: Sequence[BufferedEvent]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            for event in events:
                handle.write(
                    json.dumps(
                        {
                            "event_id": event.event_id,
                            "event_type": event.event_type,
                            "payload": event.payload,
                            "created_at": event.created_at,
                            "attempts": event.attempts,
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )


def _format_authorization(token: str) -> str:
    value = token.strip()
    if value.lower().startswith("bearer "):
        return value
    return f"Bearer {value}"


class SkillsGatewayClient:
    """Thin HTTP client for POST /v1/{operation}.

    Authorization resolution order per request:

    1. Explicit ``authorization=`` override on the call.
    2. Injected ``paci_client`` (PACI ``client_credentials`` + ``private_key_jwt``).
    3. Static ``authorization`` constructor arg (tests / local-test explicit mode).

    Prefer :meth:`from_env` for Cursor/canary: PACI SecretRef env is primary;
    static ``GATEWAY_TOKEN`` / ``LINKSKILLS_CANARY_AUTHORIZATION`` is allowed
    only when ``LINKSKILLS_AUTH_MODE=local-test``.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        *,
        authorization: Optional[str] = None,
        paci_client: Optional[PaciTokenClient] = None,
        timeout_s: float = 30.0,
        event_buffer: Optional[LocalEventBuffer] = None,
        auth_mode: Optional[str] = None,
    ) -> None:
        raw_base = (base_url or os.environ.get("GATEWAY_URL") or "http://127.0.0.1:8787").rstrip(
            "/"
        )
        if auth_mode is not None:
            mode = str(auth_mode).strip().lower()
        else:
            env_mode = str(os.environ.get("LINKSKILLS_AUTH_MODE") or "").strip().lower()
            if env_mode:
                mode = env_mode
            else:
                # Direct construction (tests/compat): loopback http uses local-test gate.
                # from_env always passes auth_mode explicitly.
                parsed = urlparse(raw_base)
                if parsed.scheme == "http" and is_loopback_host(parsed.hostname):
                    mode = AUTH_MODE_LOCAL_TEST
                else:
                    mode = "production"
        self.base_url = require_https_outside_local_test(
            raw_base,
            auth_mode=mode,
            label="GATEWAY_URL",
        ).rstrip("/")
        self.authorization = authorization
        self.paci_client = paci_client
        self.timeout_s = timeout_s
        self.event_buffer = event_buffer or LocalEventBuffer()
        self.auth_mode = mode

    @classmethod
    def from_env(
        cls,
        environ: Optional[Mapping[str, str]] = None,
        *,
        timeout_s: float = 30.0,
        event_buffer: Optional[LocalEventBuffer] = None,
        paci_client: Optional[PaciTokenClient] = None,
    ) -> "SkillsGatewayClient":
        """Build a client from Skills PACI env (preferred) or local-test static bearer."""
        env = environ if environ is not None else os.environ
        base_url = (env.get("GATEWAY_URL") or "http://127.0.0.1:8787").rstrip("/")
        mode = resolve_auth_mode(env)

        resolved_paci = paci_client
        static: Optional[str] = None

        if resolved_paci is None and paci_env_configured(env):
            resolved_paci = PaciTokenClient.from_env(env)

        if resolved_paci is None:
            static_token = (
                str(env.get("LINKSKILLS_CANARY_AUTHORIZATION") or "").strip()
                or str(env.get("GATEWAY_TOKEN") or "").strip()
                or str(env.get("LINKSKILLS_LOCAL_TEST_STATIC_BEARER") or "").strip()
            )
            if static_token:
                if mode != AUTH_MODE_LOCAL_TEST:
                    raise PaciConfigError(
                        "Static bearer env "
                        "(LINKSKILLS_CANARY_AUTHORIZATION / GATEWAY_TOKEN / "
                        "LINKSKILLS_LOCAL_TEST_STATIC_BEARER) is local-test only; "
                        "set LINKSKILLS_AUTH_MODE=local-test or configure PACI "
                        f"({ENV_HINT})"
                    )
                static = static_token

        if resolved_paci is None and not static:
            raise PaciConfigError(
                "No Skills authorization configured: set PACI env "
                f"({ENV_HINT}) or local-test static bearer"
            )

        return cls(
            base_url=base_url,
            authorization=static,
            paci_client=resolved_paci,
            timeout_s=timeout_s,
            event_buffer=event_buffer,
            auth_mode=mode,
        )

    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/health")

    def ready(self) -> Dict[str, Any]:
        return self._request("GET", "/ready")

    def call(
        self,
        operation: str,
        params: Optional[Mapping[str, Any]] = None,
        *,
        request_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        authorization: Optional[str] = None,
    ) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "X-Request-Id": request_id or str(uuid.uuid4()),
        }
        token = self._resolve_authorization(authorization)
        if token:
            headers["Authorization"] = token
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        body = {"params": dict(params or {}), "request_id": headers["X-Request-Id"]}
        return self._request("POST", f"/v1/{operation}", headers=headers, body=body)

    def buffer_event(self, event_type: str, payload: Mapping[str, Any]) -> BufferedEvent:
        return self.event_buffer.append(event_type, payload)

    def flush_buffered_events(
        self,
        *,
        operation: str = "skills_feedback_submit",
        limit: int = 100,
    ) -> Dict[str, Any]:
        pending = self.event_buffer.load()
        written = 0
        failed = 0
        remaining: List[BufferedEvent] = []
        for event in pending:
            if written + failed >= limit:
                remaining.append(event)
                continue
            try:
                self.call(operation, event.payload)
                written += 1
            except Exception:  # noqa: BLE001 — offline retry path
                event.attempts += 1
                failed += 1
                remaining.append(event)
        self.event_buffer.rewrite(remaining)
        return {
            "attempted": written + failed,
            "written": written,
            "failed": failed,
            "remaining": len(remaining),
        }

    def status(self) -> Dict[str, Any]:
        """Safe diagnostics — never includes bearer tokens or key material."""
        paci_status = self.paci_client.status() if self.paci_client is not None else None
        return {
            "base_url": self.base_url,
            "auth_mode": self.auth_mode,
            "paci_configured": self.paci_client is not None,
            "static_authorization_configured": bool(self.authorization),
            "paci": paci_status,
            "live_proven": False,
        }

    def _resolve_authorization(self, override: Optional[str] = None) -> Optional[str]:
        if override:
            return _format_authorization(override)
        if self.paci_client is not None:
            return self.paci_client.authorization_header()
        if self.authorization:
            return _format_authorization(self.authorization)
        return None

    def _request(
        self,
        method: str,
        path: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        body: Optional[Mapping[str, Any]] = None,
        _auth_retries: int = 0,
    ) -> Dict[str, Any]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        req_headers = dict(headers or {})
        req = Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers=req_headers,
        )
        try:
            with urlopen(req, timeout=self.timeout_s) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            # HTTP 4xx/5xx must fail flush/call paths — never treat error bodies
            # as successful responses (would drop buffered events as "written").
            detail = exc.read().decode("utf-8", errors="replace")
            if (
                exc.code == 401
                and self.paci_client is not None
                and _auth_retries < GATEWAY_401_RETRY_MAX
                and "Authorization" in req_headers
            ):
                # Invalidate cached PACI access token and remint once (bounded).
                self.paci_client.invalidate()
                refreshed = self.paci_client.authorization_header(force_refresh=True)
                retry_headers = dict(req_headers)
                retry_headers["Authorization"] = refreshed
                return self._request(
                    method,
                    path,
                    headers=retry_headers,
                    body=body,
                    _auth_retries=_auth_retries + 1,
                )
            raise RuntimeError(f"gateway HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"gateway unreachable: {exc}") from exc


# Kept short for error messages (no secrets).
ENV_HINT = (
    "LINKSKILLS_PACI_CLIENT_ID, LINKSKILLS_PACI_TOKEN_ENDPOINT, "
    "LINKSKILLS_PACI_CLIENT_PRIVATE_KEY_FILE"
)
