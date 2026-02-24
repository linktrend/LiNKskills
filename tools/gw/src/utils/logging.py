from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


class GWAuditLogger:
    """Append-only JSONL audit logger."""

    def __init__(self, log_path: str | Path | None = None) -> None:
        default_path = Path("~/.gw/logs/audit.jsonl").expanduser()
        self.log_path = Path(log_path).expanduser() if log_path else default_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        service: str,
        action: str,
        status: str,
        resource_id: str,
    ) -> None:
        entry: dict[str, str] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "service": service,
            "action": action,
            "status": status,
            "resource_id": resource_id,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
