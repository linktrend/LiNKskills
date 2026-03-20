from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any


class LangfuseUsageTracker:
    """Log runtime execution telemetry to Langfuse using vault-managed keys."""

    DEFAULT_PUBLIC_KEY_NAME = "LANGFUSE_PUBLIC_KEY"
    DEFAULT_SECRET_KEY_NAME = "LANGFUSE_SECRET_KEY"
    DEFAULT_HOST_KEY_NAME = "LANGFUSE_HOST"
    DISCONNECTED_MESSAGE = "[UsageTracker] Disconnected: Running in local-only mode."

    def __init__(self, repo_root: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root).expanduser().resolve() if repo_root else Path(__file__).resolve().parents[3]
        self.vault_module_path = self.repo_root / "tools" / "vault" / "src" / "vault_logic.py"
        self.vault_data_path = self.repo_root / "tools" / "vault" / "data" / "vault.bin"

        self.public_key_name = os.getenv("LANGFUSE_PUBLIC_KEY_VAULT_KEY", self.DEFAULT_PUBLIC_KEY_NAME).strip()
        self.secret_key_name = os.getenv("LANGFUSE_SECRET_KEY_VAULT_KEY", self.DEFAULT_SECRET_KEY_NAME).strip()
        self.host_key_name = os.getenv("LANGFUSE_HOST_VAULT_KEY", self.DEFAULT_HOST_KEY_NAME).strip()
        self._disconnected_notified = False

    def log_execution(
        self,
        service: str,
        action: str,
        success: bool,
        latency_ms: int,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = self._build_client()
        if client is None:
            return {
                "status": "local_only",
                "service": service,
                "action": action,
                "success": bool(success),
                "latency_ms": int(latency_ms),
            }

        payload_metadata = {
            "service": service,
            "action": action,
            "success": bool(success),
            "latency_ms": int(latency_ms),
        }
        if metadata:
            payload_metadata.update(metadata)

        try:
            trace_name = f"ltr.{service}.{action}"
            trace = client.trace(
                name=trace_name,
                input={"service": service, "action": action},
                output={"success": bool(success), "latency_ms": int(latency_ms)},
                metadata=payload_metadata,
            )

            if hasattr(trace, "generation"):
                trace.generation(
                    name="ltr.execution",
                    model="ltr-cli",
                    input={"service": service, "action": action},
                    output={"success": bool(success), "latency_ms": int(latency_ms)},
                    metadata=payload_metadata,
                )
            elif hasattr(client, "generation"):
                client.generation(
                    name="ltr.execution",
                    model="ltr-cli",
                    input={"service": service, "action": action},
                    output={"success": bool(success), "latency_ms": int(latency_ms)},
                    metadata=payload_metadata,
                )

            if hasattr(client, "flush"):
                client.flush()
        except Exception:
            self._notify_disconnected()
            return {
                "status": "local_only",
                "service": service,
                "action": action,
                "success": bool(success),
                "latency_ms": int(latency_ms),
            }

        return {
            "status": "success",
            "service": service,
            "action": action,
            "success": bool(success),
            "latency_ms": int(latency_ms),
        }

    def _build_client(self) -> Any | None:
        public_key = self._get_secret_from_vault(self.public_key_name, required=True)
        secret_key = self._get_secret_from_vault(self.secret_key_name, required=True)
        host = self._get_secret_from_vault(self.host_key_name, required=False) or os.getenv(
            "LANGFUSE_HOST",
            "https://cloud.langfuse.com",
        )
        if not public_key or not secret_key:
            self._notify_disconnected()
            return None

        try:
            from langfuse import Langfuse
        except Exception:
            self._notify_disconnected()
            return None

        try:
            return Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host,
            )
        except Exception:
            self._notify_disconnected()
            return None

    def _get_secret_from_vault(self, key_name: str, required: bool = True) -> str:
        master_key = os.getenv("LSL_MASTER_KEY", "").strip()
        if not master_key:
            if required:
                self._notify_disconnected()
            return ""
        if not self.vault_module_path.exists():
            if required:
                self._notify_disconnected()
            return ""

        spec = importlib.util.spec_from_file_location("lsl_vault_logic", str(self.vault_module_path))
        if spec is None or spec.loader is None:
            if required:
                self._notify_disconnected()
            return ""

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception:
            if required:
                self._notify_disconnected()
            return ""
        vault_store_cls = getattr(module, "VaultStore", None)
        if vault_store_cls is None:
            if required:
                self._notify_disconnected()
            return ""

        try:
            vault = vault_store_cls(data_path=self.vault_data_path, master_key=master_key)
        except Exception:
            if required:
                self._notify_disconnected()
            return ""
        try:
            value = str(vault.get_value(key_name)).strip()
        except KeyError:
            if required:
                self._notify_disconnected()
            return ""

        if required and not value:
            self._notify_disconnected()
            return ""
        return value

    def _notify_disconnected(self) -> None:
        if self._disconnected_notified:
            return
        self._disconnected_notified = True
        print(self.DISCONNECTED_MESSAGE, file=sys.stderr)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LiNKskills usage tracking CLI")
    parser.add_argument("--version", action="version", version="usage 1.1.0")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON output")

    subparsers = parser.add_subparsers(dest="command", required=True)
    log_parser = subparsers.add_parser("log", help="Log one execution event to Langfuse")
    log_parser.add_argument("--service", required=True, type=str)
    log_parser.add_argument("--action", required=True, type=str)
    log_parser.add_argument("--latency-ms", required=True, type=int)
    log_parser.add_argument("--success", required=True, choices=["true", "false"])
    log_parser.add_argument("--metadata-json", default="{}", type=str)
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        tracker = LangfuseUsageTracker()
        metadata = json.loads(args.metadata_json)
        if not isinstance(metadata, dict):
            raise ValueError("--metadata-json must decode to a JSON object")

        result = tracker.log_execution(
            service=args.service,
            action=args.action,
            success=(args.success == "true"),
            latency_ms=args.latency_ms,
            metadata=metadata,
        )
        print(json.dumps({"status": "success", "output": result, "path": "langfuse"}, sort_keys=True, separators=(",", ":")))
    except Exception as exc:
        print(
            json.dumps(
                {"status": "error", "output": str(exc), "path": "langfuse"},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
