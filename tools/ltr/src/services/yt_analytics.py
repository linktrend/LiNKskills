from __future__ import annotations

from pathlib import Path
from typing import Any

from googleapiclient.discovery import build

from utils.auth import LTRAuth


class YTAnalyticsService:
    """YouTube Analytics + Reporting service wrapper."""

    def __init__(self, config_path: str | Path, user_id: str = "me") -> None:
        self.user_id = user_id
        auth = LTRAuth(config_path=config_path)
        credentials = auth.get_credentials()
        self.analytics_client = build("youtubeAnalytics", "v2", credentials=credentials, cache_discovery=False)
        self.reporting_client = build("youtubereporting", "v1", credentials=credentials, cache_discovery=False)

    def query_private_metrics(
        self,
        start_date: str,
        end_date: str,
        metrics: str = "views,estimatedMinutesWatched,subscribersGained",
        dimensions: str = "day",
        ids: str = "channel==MINE",
        max_results: int = 30,
    ) -> dict[str, Any]:
        try:
            response = (
                self.analytics_client.reports()
                .query(
                    ids=ids,
                    startDate=start_date,
                    endDate=end_date,
                    metrics=metrics,
                    dimensions=dimensions,
                    maxResults=max_results,
                )
                .execute()
            )
            return {
                "status": "success",
                "column_headers": response.get("columnHeaders", []),
                "rows": response.get("rows", []),
                "kind": response.get("kind"),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GYT_ANALYTICS_QUERY_FAILED",
                "message": str(exc),
            }

    def list_reporting_jobs(self) -> dict[str, Any]:
        try:
            response = self.reporting_client.jobs().list().execute()
            jobs = response.get("jobs", [])
            normalized = [
                {
                    "job_id": job.get("id"),
                    "name": job.get("name", ""),
                    "report_type_id": job.get("reportTypeId", ""),
                    "create_time": job.get("createTime"),
                    "expire_time": job.get("expireTime"),
                }
                for job in jobs
            ]
            return {
                "status": "success",
                "count": len(normalized),
                "jobs": normalized,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GYT_REPORTING_LIST_JOBS_FAILED",
                "message": str(exc),
            }
