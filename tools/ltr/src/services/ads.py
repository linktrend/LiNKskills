from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib import error as url_error
from urllib import request as url_request
import json
import os

from google.auth.transport.requests import Request

from utils.auth import LTRAuth


class AdsService:
    """Google Ads API service wrapper for campaign/budget overview."""

    def __init__(self, config_path: str | Path, user_id: str = "me") -> None:
        self.user_id = user_id
        auth = LTRAuth(config_path=config_path)
        self.credentials = auth.get_credentials()

    def _access_token(self) -> str:
        if not self.credentials.valid and self.credentials.refresh_token:
            self.credentials.refresh(Request())
        token = self.credentials.token
        if not token:
            raise RuntimeError("Unable to obtain OAuth token for Ads API.")
        return token

    def campaign_overview(
        self,
        customer_id: str,
        limit: int = 20,
        login_customer_id: str | None = None,
    ) -> dict[str, Any]:
        developer_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "").strip()
        if not developer_token:
            return {
                "status": "error",
                "code": "GADS_MISSING_DEVELOPER_TOKEN",
                "message": "Set GOOGLE_ADS_DEVELOPER_TOKEN in environment.",
            }

        query = (
            "SELECT campaign.id, campaign.name, campaign.status, "
            "campaign_budget.amount_micros, metrics.impressions, metrics.clicks, metrics.cost_micros "
            f"FROM campaign ORDER BY metrics.impressions DESC LIMIT {limit}"
        )
        endpoint = f"https://googleads.googleapis.com/v18/customers/{customer_id}/googleAds:searchStream"
        headers = {
            "Authorization": f"Bearer {self._access_token()}",
            "developer-token": developer_token,
            "Content-Type": "application/json",
        }
        if login_customer_id:
            headers["login-customer-id"] = login_customer_id

        req = url_request.Request(
            endpoint,
            method="POST",
            data=json.dumps({"query": query}).encode("utf-8"),
            headers=headers,
        )

        try:
            with url_request.urlopen(req) as response:
                payload = json.loads(response.read().decode("utf-8"))

            rows: list[dict[str, Any]] = []
            for chunk in payload:
                for row in chunk.get("results", []):
                    campaign = row.get("campaign", {})
                    budget = row.get("campaignBudget", {})
                    metrics = row.get("metrics", {})
                    rows.append(
                        {
                            "campaign_id": campaign.get("id"),
                            "campaign_name": campaign.get("name", ""),
                            "status": campaign.get("status"),
                            "budget_micros": budget.get("amountMicros"),
                            "impressions": metrics.get("impressions"),
                            "clicks": metrics.get("clicks"),
                            "cost_micros": metrics.get("costMicros"),
                        }
                    )

            return {
                "status": "success",
                "customer_id": customer_id,
                "count": len(rows),
                "campaigns": rows,
            }
        except url_error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return {
                "status": "error",
                "code": "GADS_HTTP_ERROR",
                "message": f"{exc.code} {exc.reason}: {detail}",
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GADS_OVERVIEW_FAILED",
                "message": str(exc),
            }
