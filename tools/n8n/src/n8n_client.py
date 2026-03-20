from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
from typing import Any
from urllib import error as url_error
from urllib import parse as url_parse
from urllib import request as url_request


class N8NService:
    """n8n API wrapper for workflow read/trigger/create/activate operations."""

    VAULT_MODULE_PATH = Path(__file__).resolve().parents[3] / "vault" / "src" / "vault_logic.py"
    VAULT_DATA_PATH = Path(__file__).resolve().parents[3] / "vault" / "data" / "vault.bin"

    def __init__(self) -> None:
        self.base_url = self._vault_get(os.getenv("N8N_URL_VAULT_KEY", "N8N_BASE_URL")).rstrip("/")
        self.api_key = self._vault_get(os.getenv("N8N_API_KEY_VAULT_KEY", "N8N_API_KEY"))

    def read_workflow(self, workflow_id: str) -> dict[str, Any]:
        payload = self._request("GET", f"/api/v1/workflows/{url_parse.quote(workflow_id, safe='')}")
        return {
            "status": "success",
            "workflow": payload,
        }

    def list_workflows(self, limit: int = 100) -> dict[str, Any]:
        payload = self._request("GET", f"/api/v1/workflows?limit={max(1, min(limit, 250))}")
        workflows = payload.get("data") if isinstance(payload, dict) else payload
        if not isinstance(workflows, list):
            workflows = []
        return {
            "status": "success",
            "count": len(workflows),
            "workflows": workflows,
        }

    def trigger_workflow(self, workflow_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._request(
            "POST",
            f"/api/v1/workflows/{url_parse.quote(workflow_id, safe='')}/run",
            body=payload,
        )
        return {
            "status": "success",
            "workflow_id": workflow_id,
            "execution": response,
        }

    def create_workflow(self, workflow_json: dict[str, Any]) -> dict[str, Any]:
        response = self._request("POST", "/api/v1/workflows", body=workflow_json)
        workflow_id = response.get("id") if isinstance(response, dict) else None
        return {
            "status": "success",
            "workflow_id": workflow_id,
            "workflow": response,
        }

    def activate_workflow(self, workflow_id: str, active: bool = True) -> dict[str, Any]:
        endpoint = f"/api/v1/workflows/{url_parse.quote(workflow_id, safe='')}/{'activate' if active else 'deactivate'}"
        response = self._request("POST", endpoint, body={})
        return {
            "status": "success",
            "workflow_id": workflow_id,
            "active": active,
            "response": response,
        }

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        endpoint = f"{self.base_url}{path}"
        raw_body = None
        headers = {
            "Content-Type": "application/json",
            "X-N8N-API-KEY": self.api_key,
        }
        if body is not None:
            raw_body = json.dumps(body).encode("utf-8")

        req = url_request.Request(
            endpoint,
            method=method,
            data=raw_body,
            headers=headers,
        )
        try:
            with url_request.urlopen(req) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except url_error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"n8n HTTP {exc.code} {exc.reason}: {detail}") from exc

    def _vault_get(self, key_name: str) -> str:
        master_key = os.getenv("LSL_MASTER_KEY", "").strip()
        if not master_key:
            raise RuntimeError("LSL_MASTER_KEY is required for n8n vault lookup.")
        if not self.VAULT_MODULE_PATH.exists():
            raise RuntimeError(f"Vault module not found: {self.VAULT_MODULE_PATH}")

        spec = importlib.util.spec_from_file_location("lsl_vault_logic", str(self.VAULT_MODULE_PATH))
        if spec is None or spec.loader is None:
            raise RuntimeError("Unable to load vault module for n8n credentials.")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        vault_store_cls = getattr(module, "VaultStore", None)
        if vault_store_cls is None:
            raise RuntimeError("VaultStore class not found in vault module.")

        vault = vault_store_cls(data_path=self.VAULT_DATA_PATH, master_key=master_key)
        try:
            value = str(vault.get_value(key_name)).strip()
        except KeyError as exc:
            raise RuntimeError(
                f"Missing vault secret '{key_name}'. Run: ltr vault set {key_name} <value>"
            ) from exc
        if not value:
            raise RuntimeError(
                f"Vault secret '{key_name}' is empty. Run: ltr vault set {key_name} <value>"
            )
        return value


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LiNKskills n8n CLI")
    parser.add_argument("--version", action="version", version="n8n 1.0.0")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    read_parser = subparsers.add_parser("read", help="Read one workflow by id")
    read_parser.add_argument("--workflow-id", required=True, type=str)

    list_parser = subparsers.add_parser("list", help="List workflows")
    list_parser.add_argument("--limit", default=100, type=int)

    trigger_parser = subparsers.add_parser("trigger", help="Trigger one workflow")
    trigger_parser.add_argument("--workflow-id", required=True, type=str)
    trigger_parser.add_argument("--payload-json", default="{}", type=str)

    create_parser = subparsers.add_parser("create", help="Create workflow from JSON")
    create_parser.add_argument("--workflow-json", required=True, type=str)

    activate_parser = subparsers.add_parser("activate", help="Activate workflow")
    activate_parser.add_argument("--workflow-id", required=True, type=str)

    deactivate_parser = subparsers.add_parser("deactivate", help="Deactivate workflow")
    deactivate_parser.add_argument("--workflow-id", required=True, type=str)

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        service = N8NService()

        if args.command == "read":
            result = service.read_workflow(workflow_id=args.workflow_id)
        elif args.command == "list":
            result = service.list_workflows(limit=max(1, int(args.limit)))
        elif args.command == "trigger":
            payload = json.loads(args.payload_json)
            if not isinstance(payload, dict):
                raise ValueError("--payload-json must decode to a JSON object")
            result = service.trigger_workflow(workflow_id=args.workflow_id, payload=payload)
        elif args.command == "create":
            workflow_json = json.loads(args.workflow_json)
            if not isinstance(workflow_json, dict):
                raise ValueError("--workflow-json must decode to a JSON object")
            result = service.create_workflow(workflow_json=workflow_json)
        elif args.command == "activate":
            result = service.activate_workflow(workflow_id=args.workflow_id, active=True)
        else:
            result = service.activate_workflow(workflow_id=args.workflow_id, active=False)

        print(
            json.dumps(
                {"status": "success", "output": result, "path": service.base_url},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    except Exception as exc:
        print(
            json.dumps(
                {"status": "error", "output": str(exc), "path": "n8n"},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
