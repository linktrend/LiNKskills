from __future__ import annotations

import argparse
import importlib.util
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import parse as url_parse
from urllib import request as url_request


class StripeService:
    """Stripe API wrapper for billing operations."""

    VAULT_MODULE_PATH = Path(__file__).resolve().parents[3] / "vault" / "src" / "vault_logic.py"
    VAULT_DATA_PATH = Path(__file__).resolve().parents[3] / "vault" / "data" / "vault.bin"

    def __init__(self) -> None:
        self.api_key = self._vault_get(os.getenv("STRIPE_API_KEY_VAULT_KEY", "STRIPE_API_KEY"))

    def list_invoices(self, limit: int = 10, status: str | None = None) -> dict[str, Any]:
        params = {"limit": max(1, min(limit, 100))}
        if status:
            params["status"] = status
        endpoint = f"https://api.stripe.com/v1/invoices?{url_parse.urlencode(params)}"
        req = url_request.Request(
            endpoint,
            method="GET",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        with url_request.urlopen(req) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rows = payload.get("data", []) if isinstance(payload, dict) else []
        invoices: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            created_ts = row.get("created")
            created_at = None
            if isinstance(created_ts, int):
                created_at = datetime.fromtimestamp(created_ts, tz=UTC).isoformat()
            invoices.append(
                {
                    "id": row.get("id"),
                    "status": row.get("status"),
                    "amount_due": row.get("amount_due"),
                    "currency": row.get("currency"),
                    "customer": row.get("customer"),
                    "created_at": created_at,
                }
            )

        return {
            "status": "success",
            "count": len(invoices),
            "invoices": invoices,
        }

    def _vault_get(self, key_name: str) -> str:
        master_key = os.getenv("LSL_MASTER_KEY", "").strip()
        if not master_key:
            raise RuntimeError("LSL_MASTER_KEY is required for stripe vault lookup.")
        if not self.VAULT_MODULE_PATH.exists():
            raise RuntimeError(f"Vault module not found: {self.VAULT_MODULE_PATH}")

        spec = importlib.util.spec_from_file_location("lsl_vault_logic", str(self.VAULT_MODULE_PATH))
        if spec is None or spec.loader is None:
            raise RuntimeError("Unable to load vault module for Stripe credentials.")

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
    parser = argparse.ArgumentParser(description="LiNKskills Stripe CLI")
    parser.add_argument("--version", action="version", version="stripe 1.0.0")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    invoice_parser = subparsers.add_parser("list-invoices", help="List Stripe invoices")
    invoice_parser.add_argument("--limit", default=10, type=int)
    invoice_parser.add_argument("--status", default=None, type=str)

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        service = StripeService()
        if args.command == "list-invoices":
            result = service.list_invoices(limit=int(args.limit), status=args.status)
        else:
            raise ValueError(f"Unsupported command: {args.command}")

        print(
            json.dumps(
                {"status": "success", "output": result, "path": "stripe"},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    except Exception as exc:
        print(
            json.dumps(
                {"status": "error", "output": str(exc), "path": "stripe"},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
