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
from urllib.request import Request, urlopen


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


class SkillsGatewayClient:
    """Thin HTTP client for POST /v1/{operation}."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        *,
        authorization: Optional[str] = None,
        timeout_s: float = 30.0,
        event_buffer: Optional[LocalEventBuffer] = None,
    ) -> None:
        self.base_url = (base_url or os.environ.get("GATEWAY_URL") or "http://127.0.0.1:8787").rstrip(
            "/"
        )
        self.authorization = authorization
        self.timeout_s = timeout_s
        self.event_buffer = event_buffer or LocalEventBuffer()

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
        token = authorization or self.authorization
        if token:
            headers["Authorization"] = (
                token if token.lower().startswith("bearer ") else f"Bearer {token}"
            )
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

    def _request(
        self,
        method: str,
        path: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        body: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers=dict(headers or {}),
        )
        try:
            with urlopen(req, timeout=self.timeout_s) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(detail) if detail else {}
            except json.JSONDecodeError:
                parsed = {"error": {"code": "http_error", "message": detail}}
            if isinstance(parsed, dict) and parsed:
                return parsed
            raise RuntimeError(f"gateway HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"gateway unreachable: {exc}") from exc
