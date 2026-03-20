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


class ResearchRouter:
    """Multi-tier research router with cost-aware escalation."""

    VAULT_MODULE_PATH = Path(__file__).resolve().parents[3] / "vault" / "src" / "vault_logic.py"
    VAULT_DATA_PATH = Path(__file__).resolve().parents[3] / "vault" / "data" / "vault.bin"

    def __init__(self) -> None:
        self.brave_key = self._vault_get(os.getenv("BRAVE_API_KEY_VAULT_KEY", "BRAVE_API_KEY"))
        self.exa_key = self._vault_get(os.getenv("EXA_API_KEY_VAULT_KEY", "EXA_API_KEY"))
        self.perplexity_key = self._vault_get(
            os.getenv("PERPLEXITY_API_KEY_VAULT_KEY", "PERPLEXITY_API_KEY")
        )
        self.grok_key = self._vault_get(os.getenv("GROK_API_KEY_VAULT_KEY", "GROK_API_KEY"))

    def route_search(
        self,
        query: str,
        tier: str = "auto",
        limit: int = 8,
        min_confidence: float = 0.6,
    ) -> dict[str, Any]:
        tier = tier.lower().strip()
        if tier == "auto":
            web_result = self.search_web(query=query, limit=limit)
            confidence = float(web_result.get("confidence", 0.0))
            if confidence >= min_confidence:
                return {
                    "status": "success",
                    "tier_used": "web",
                    "escalated": False,
                    "confidence": confidence,
                    "result": web_result,
                }

            neural_result = self.search_neural(query=query, limit=limit)
            return {
                "status": "success",
                "tier_used": "neural",
                "escalated": True,
                "escalation_reason": (
                    f"Tier 1 confidence {confidence:.2f} below threshold {min_confidence:.2f}; "
                    "escalated to Tier 2 neural search."
                ),
                "precheck": web_result,
                "result": neural_result,
            }

        if tier == "web":
            result = self.search_web(query=query, limit=limit)
        elif tier == "neural":
            result = self.search_neural(query=query, limit=limit)
        elif tier == "brief":
            result = self.search_brief(query=query)
        elif tier == "social":
            result = self.search_social(query=query)
        else:
            raise ValueError("tier must be one of: auto, web, neural, brief, social")

        return {
            "status": "success",
            "tier_used": tier,
            "escalated": False,
            "result": result,
        }

    def search_web(self, query: str, limit: int = 8) -> dict[str, Any]:
        params = url_parse.urlencode({"q": query, "count": max(1, min(limit, 20))})
        endpoint = f"https://api.search.brave.com/res/v1/web/search?{params}"
        payload = self._request_json(
            method="GET",
            endpoint=endpoint,
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": self.brave_key,
            },
        )
        raw_results = payload.get("web", {}).get("results", []) if isinstance(payload, dict) else []
        results: list[dict[str, Any]] = []
        for row in raw_results:
            if not isinstance(row, dict):
                continue
            results.append(
                {
                    "title": row.get("title", ""),
                    "url": row.get("url", ""),
                    "snippet": row.get("description", ""),
                }
            )
        confidence = self._confidence_from_results(results)
        return {
            "tier": "web",
            "query": query,
            "count": len(results),
            "confidence": confidence,
            "results": results,
        }

    def search_neural(self, query: str, limit: int = 8) -> dict[str, Any]:
        endpoint = "https://api.exa.ai/search"
        payload = self._request_json(
            method="POST",
            endpoint=endpoint,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.exa_key,
            },
            body={
                "query": query,
                "numResults": max(1, min(limit, 20)),
                "type": "neural",
            },
        )
        raw_results = payload.get("results", []) if isinstance(payload, dict) else []
        results: list[dict[str, Any]] = []
        for row in raw_results:
            if not isinstance(row, dict):
                continue
            results.append(
                {
                    "title": row.get("title", ""),
                    "url": row.get("url", ""),
                    "snippet": row.get("text", ""),
                    "score": row.get("score"),
                }
            )
        confidence = self._confidence_from_results(results)
        return {
            "tier": "neural",
            "query": query,
            "count": len(results),
            "confidence": confidence,
            "results": results,
        }

    def search_brief(self, query: str) -> dict[str, Any]:
        endpoint = "https://api.perplexity.ai/chat/completions"
        model = os.getenv("PERPLEXITY_MODEL", "sonar")
        payload = self._request_json(
            method="POST",
            endpoint=endpoint,
            headers={
                "Authorization": f"Bearer {self.perplexity_key}",
                "Content-Type": "application/json",
            },
            body={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Produce a concise factual research brief with key points and source links.",
                    },
                    {"role": "user", "content": query},
                ],
            },
        )
        content = ""
        if isinstance(payload, dict):
            choices = payload.get("choices", [])
            if isinstance(choices, list) and choices:
                message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
                content = str(message.get("content", ""))
        confidence = 0.75 if len(content) >= 120 else 0.45
        return {
            "tier": "brief",
            "query": query,
            "model": model,
            "confidence": confidence,
            "summary": content,
        }

    def search_social(self, query: str) -> dict[str, Any]:
        endpoint = "https://api.x.ai/v1/chat/completions"
        model = os.getenv("GROK_MODEL", "grok-2-latest")
        payload = self._request_json(
            method="POST",
            endpoint=endpoint,
            headers={
                "Authorization": f"Bearer {self.grok_key}",
                "Content-Type": "application/json",
            },
            body={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Analyze social sentiment and discuss major opinions, signals, and risks.",
                    },
                    {"role": "user", "content": query},
                ],
            },
        )
        content = ""
        if isinstance(payload, dict):
            choices = payload.get("choices", [])
            if isinstance(choices, list) and choices:
                message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
                content = str(message.get("content", ""))
        confidence = 0.7 if len(content) >= 120 else 0.4
        return {
            "tier": "social",
            "query": query,
            "model": model,
            "confidence": confidence,
            "sentiment_brief": content,
        }

    def _confidence_from_results(self, results: list[dict[str, Any]]) -> float:
        if not results:
            return 0.0
        high_signal = 0
        for item in results:
            title = str(item.get("title", "")).strip()
            snippet = str(item.get("snippet", "")).strip()
            if title and snippet:
                high_signal += 1
        ratio = high_signal / max(1, len(results))
        density = min(1.0, len(results) / 8)
        return round((0.55 * ratio) + (0.45 * density), 4)

    def _request_json(
        self,
        method: str,
        endpoint: str,
        headers: dict[str, str],
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raw_body = None
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
            raise RuntimeError(f"HTTP {exc.code} {exc.reason}: {detail}") from exc

    def _vault_get(self, key_name: str) -> str:
        master_key = os.getenv("LSL_MASTER_KEY", "").strip()
        if not master_key:
            raise RuntimeError("LSL_MASTER_KEY is required for research vault lookup.")
        if not self.VAULT_MODULE_PATH.exists():
            raise RuntimeError(f"Vault module not found: {self.VAULT_MODULE_PATH}")

        spec = importlib.util.spec_from_file_location("lsl_vault_logic", str(self.VAULT_MODULE_PATH))
        if spec is None or spec.loader is None:
            raise RuntimeError("Unable to load vault module for research credentials.")

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
    parser = argparse.ArgumentParser(description="LiNKskills research router")
    parser.add_argument("--version", action="version", version="research 1.0.0")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON output")

    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Run tiered research query")
    search_parser.add_argument("--query", required=True, type=str)
    search_parser.add_argument(
        "--tier",
        default="auto",
        choices=["auto", "web", "neural", "brief", "social"],
    )
    search_parser.add_argument("--limit", default=8, type=int)
    search_parser.add_argument("--min-confidence", default=0.6, type=float)

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
        router = ResearchRouter()
        if args.command == "search":
            result = router.route_search(
                query=args.query,
                tier=args.tier,
                limit=max(1, int(args.limit)),
                min_confidence=max(0.0, min(1.0, float(args.min_confidence))),
            )
        else:
            raise ValueError(f"Unsupported command: {args.command}")

        print(
            json.dumps(
                {"status": "success", "output": result, "path": "research"},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    except Exception as exc:
        print(
            json.dumps(
                {"status": "error", "output": str(exc), "path": "research"},
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
