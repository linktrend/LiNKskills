from __future__ import annotations

from pathlib import Path
from typing import Any

from googleapiclient.discovery import build

from utils.auth import LTRAuth


class SearchConsoleService:
    """Search Console API service wrapper."""

    def __init__(self, config_path: str | Path, user_id: str = "me") -> None:
        self.user_id = user_id
        auth = LTRAuth(config_path=config_path)
        credentials = auth.get_credentials()
        self.client = build("searchconsole", "v1", credentials=credentials, cache_discovery=False)

    def list_sites(self) -> dict[str, Any]:
        try:
            response = self.client.sites().list().execute()
            entries = response.get("siteEntry", [])
            sites = [
                {
                    "site_url": item.get("siteUrl"),
                    "permission_level": item.get("permissionLevel"),
                }
                for item in entries
            ]
            return {
                "status": "success",
                "count": len(sites),
                "sites": sites,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GSC_LIST_SITES_FAILED",
                "message": str(exc),
            }

    def query_performance(
        self,
        site_url: str,
        start_date: str,
        end_date: str,
        dimensions: list[str] | None = None,
        row_limit: int = 25,
        search_type: str = "web",
    ) -> dict[str, Any]:
        try:
            body: dict[str, Any] = {
                "startDate": start_date,
                "endDate": end_date,
                "dimensions": dimensions or ["query"],
                "rowLimit": row_limit,
                "type": search_type,
            }
            response = self.client.searchanalytics().query(siteUrl=site_url, body=body).execute()
            rows = response.get("rows", [])
            normalized = [
                {
                    "keys": row.get("keys", []),
                    "clicks": row.get("clicks", 0),
                    "impressions": row.get("impressions", 0),
                    "ctr": row.get("ctr", 0),
                    "position": row.get("position", 0),
                }
                for row in rows
            ]
            return {
                "status": "success",
                "site_url": site_url,
                "count": len(normalized),
                "rows": normalized,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GSC_QUERY_FAILED",
                "message": str(exc),
            }
