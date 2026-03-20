from __future__ import annotations

from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from urllib import error as url_error
from urllib import request as url_request
import json

from utils.auth import LTRAuth


class AnalyticsService:
    """GA4 Data API (runReport) service wrapper."""

    def __init__(self, config_path: str | Path, user_id: str = "me") -> None:
        self.user_id = user_id
        auth = LTRAuth(config_path=config_path)
        self.credentials = auth.get_credentials()

    def _access_token(self) -> str:
        if not self.credentials.valid and self.credentials.refresh_token:
            self.credentials.refresh(Request())
        token = self.credentials.token
        if not token:
            raise RuntimeError("Unable to obtain OAuth token for Analytics API.")
        return token

    def run_report(
        self,
        property_id: str,
        start_date: str,
        end_date: str,
        metrics: list[str],
        dimensions: list[str] | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        try:
            body: dict[str, Any] = {
                "dateRanges": [{"startDate": start_date, "endDate": end_date}],
                "metrics": [{"name": metric} for metric in metrics],
                "limit": str(limit),
            }
            if dimensions:
                body["dimensions"] = [{"name": dimension} for dimension in dimensions]

            endpoint = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
            req = url_request.Request(
                endpoint,
                method="POST",
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self._access_token()}",
                    "Content-Type": "application/json",
                },
            )
            with url_request.urlopen(req) as response:
                payload = json.loads(response.read().decode("utf-8"))

            rows = payload.get("rows", [])
            normalized_rows = []
            for row in rows:
                dimensions_values = [item.get("value") for item in row.get("dimensionValues", [])]
                metric_values = [item.get("value") for item in row.get("metricValues", [])]
                normalized_rows.append(
                    {
                        "dimensions": dimensions_values,
                        "metrics": metric_values,
                    }
                )

            return {
                "status": "success",
                "property_id": property_id,
                "row_count": payload.get("rowCount", len(normalized_rows)),
                "rows": normalized_rows,
                "dimension_headers": [item.get("name") for item in payload.get("dimensionHeaders", [])],
                "metric_headers": [item.get("name") for item in payload.get("metricHeaders", [])],
            }
        except url_error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return {
                "status": "error",
                "code": "GANALYTICS_HTTP_ERROR",
                "message": f"{exc.code} {exc.reason}: {detail}",
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GANALYTICS_REPORT_FAILED",
                "message": str(exc),
            }
