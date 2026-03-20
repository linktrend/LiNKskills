from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any
from urllib import parse as url_parse
from urllib import request as url_request


class NewsService:
    """Apify-backed news retrieval service."""

    VAULT_MODULE_PATH = Path(__file__).resolve().parents[4] / "tools" / "vault" / "src" / "vault_logic.py"
    VAULT_DATA_PATH = Path(__file__).resolve().parents[4] / "tools" / "vault" / "data" / "vault.bin"
    APIFY_DEFAULT_TOKEN_KEY = "APIFY_API_TOKEN"

    def __init__(self) -> None:
        self.actor_id = os.getenv("APIFY_NEWS_ACTOR_ID", "apify/google-search-scraper").strip()
        if not self.actor_id:
            self.actor_id = "apify/google-search-scraper"
        self.token_key = os.getenv("APIFY_VAULT_TOKEN_KEY", self.APIFY_DEFAULT_TOKEN_KEY).strip()
        self.apify_token = self._get_token_from_vault()

    def search(self, query: str, limit: int = 10) -> dict[str, Any]:
        try:
            items = self._run_actor(
                {
                    "queries": query,
                    "maxPagesPerQuery": 1,
                    "resultsPerPage": max(1, min(limit, 50)),
                }
            )
            normalized = self._normalize_items(items)[:limit]
            return {
                "status": "success",
                "query": query,
                "count": len(normalized),
                "articles": normalized,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "NEWS_SEARCH_FAILED",
                "message": str(exc),
            }

    def trending(self, limit: int = 10) -> dict[str, Any]:
        trending_query = os.getenv("APIFY_TRENDING_QUERY", "latest world news").strip()
        try:
            items = self._run_actor(
                {
                    "queries": trending_query,
                    "maxPagesPerQuery": 1,
                    "resultsPerPage": max(1, min(limit, 50)),
                }
            )
            normalized = self._normalize_items(items)[:limit]
            return {
                "status": "success",
                "query": trending_query,
                "count": len(normalized),
                "articles": normalized,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "NEWS_TRENDING_FAILED",
                "message": str(exc),
            }

    def _run_actor(self, actor_input: dict[str, Any]) -> list[dict[str, Any]]:
        actor_path = url_parse.quote(self.actor_id, safe="/")
        endpoint = (
            f"https://api.apify.com/v2/acts/{actor_path}/run-sync-get-dataset-items"
            f"?token={url_parse.quote(self.apify_token, safe='')}&format=json&clean=true"
        )
        request_payload = json.dumps(actor_input).encode("utf-8")
        req = url_request.Request(
            endpoint,
            method="POST",
            data=request_payload,
            headers={"Content-Type": "application/json"},
        )
        with url_request.urlopen(req) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            items = payload.get("items", [])
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
        return []

    def _normalize_items(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for item in items:
            title = (
                item.get("title")
                or item.get("headline")
                or item.get("name")
                or ""
            )
            url = item.get("url") or item.get("link") or item.get("articleUrl") or ""
            source = item.get("source") or item.get("publisher") or item.get("siteName") or ""
            published_at = (
                item.get("publishedAt")
                or item.get("published")
                or item.get("timestamp")
                or item.get("date")
            )
            summary = (
                item.get("description")
                or item.get("snippet")
                or item.get("summary")
                or ""
            )
            normalized.append(
                {
                    "title": str(title),
                    "url": str(url),
                    "source": str(source),
                    "published_at": published_at,
                    "summary": str(summary),
                }
            )
        return normalized

    def _get_token_from_vault(self) -> str:
        master_key = os.getenv("LSL_MASTER_KEY", "").strip()
        if not master_key:
            raise RuntimeError("LSL_MASTER_KEY is required to load APIFY_API_TOKEN from vault.")
        if not self.VAULT_MODULE_PATH.exists():
            raise RuntimeError(f"Vault module not found: {self.VAULT_MODULE_PATH}")

        spec = importlib.util.spec_from_file_location(
            "lsl_vault_logic",
            str(self.VAULT_MODULE_PATH),
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("Unable to load vault module for APIFY token retrieval.")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        vault_store_cls = getattr(module, "VaultStore", None)
        if vault_store_cls is None:
            raise RuntimeError("VaultStore class not found in vault module.")

        vault = vault_store_cls(
            data_path=self.VAULT_DATA_PATH,
            master_key=master_key,
        )
        try:
            token = str(vault.get_value(self.token_key)).strip()
        except KeyError as exc:
            raise RuntimeError(
                f"Missing vault secret '{self.token_key}'. "
                f"Run: ltr vault set {self.token_key} <token>"
            ) from exc
        if not token:
            raise RuntimeError(
                f"Vault secret '{self.token_key}' is empty. "
                f"Run: ltr vault set {self.token_key} <token>"
            )
        return token
