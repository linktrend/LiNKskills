from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
from typing import Any
from urllib import parse as url_parse
from urllib import request as url_request


class ShopifyService:
    """Shopify API wrapper for product catalog operations."""

    VAULT_MODULE_PATH = Path(__file__).resolve().parents[3] / "vault" / "src" / "vault_logic.py"
    VAULT_DATA_PATH = Path(__file__).resolve().parents[3] / "vault" / "data" / "vault.bin"

    def __init__(self) -> None:
        self.access_token = self._vault_get(
            os.getenv("SHOPIFY_ACCESS_TOKEN_VAULT_KEY", "SHOPIFY_ACCESS_TOKEN")
        )
        self.store_domain = self._vault_get(
            os.getenv("SHOPIFY_STORE_DOMAIN_VAULT_KEY", "SHOPIFY_STORE_DOMAIN")
        )
        if not self.store_domain.startswith("http://") and not self.store_domain.startswith("https://"):
            self.store_domain = f"https://{self.store_domain}"

    def list_products(self, limit: int = 20) -> dict[str, Any]:
        params = url_parse.urlencode({"limit": max(1, min(limit, 250))})
        endpoint = f"{self.store_domain.rstrip('/')}/admin/api/2024-10/products.json?{params}"
        req = url_request.Request(
            endpoint,
            method="GET",
            headers={
                "X-Shopify-Access-Token": self.access_token,
                "Content-Type": "application/json",
            },
        )
        with url_request.urlopen(req) as response:
            payload = json.loads(response.read().decode("utf-8"))

        rows = payload.get("products", []) if isinstance(payload, dict) else []
        products: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            products.append(
                {
                    "id": row.get("id"),
                    "title": row.get("title"),
                    "handle": row.get("handle"),
                    "status": row.get("status"),
                    "vendor": row.get("vendor"),
                    "created_at": row.get("created_at"),
                }
            )

        return {
            "status": "success",
            "count": len(products),
            "products": products,
        }

    def _vault_get(self, key_name: str) -> str:
        master_key = os.getenv("LSL_MASTER_KEY", "").strip()
        if not master_key:
            raise RuntimeError("LSL_MASTER_KEY is required for shopify vault lookup.")
        if not self.VAULT_MODULE_PATH.exists():
            raise RuntimeError(f"Vault module not found: {self.VAULT_MODULE_PATH}")

        spec = importlib.util.spec_from_file_location("lsl_vault_logic", str(self.VAULT_MODULE_PATH))
        if spec is None or spec.loader is None:
            raise RuntimeError("Unable to load vault module for Shopify credentials.")

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
    parser = argparse.ArgumentParser(description="LiNKskills Shopify CLI")
    parser.add_argument("--version", action="version", version="shopify 1.0.0")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    products_parser = subparsers.add_parser("list-products", help="List Shopify products")
    products_parser.add_argument("--limit", default=20, type=int)

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        service = ShopifyService()
        if args.command == "list-products":
            result = service.list_products(limit=int(args.limit))
        else:
            raise ValueError(f"Unsupported command: {args.command}")

        print(
            json.dumps(
                {"status": "success", "output": result, "path": "shopify"},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    except Exception as exc:
        print(
            json.dumps(
                {"status": "error", "output": str(exc), "path": "shopify"},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
