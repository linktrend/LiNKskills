from __future__ import annotations

from pathlib import Path
from typing import Any

from googleapiclient.discovery import build

from utils.auth import GWAuth


class FormsService:
    """Google Forms API service wrapper."""

    def __init__(self, config_path: str | Path, user_id: str = "me") -> None:
        self.user_id = user_id
        auth = GWAuth(config_path=config_path)
        credentials = auth.get_credentials()
        self.client = build("forms", "v1", credentials=credentials, cache_discovery=False)

    def create_form(self, title: str, document_title: str | None = None) -> dict[str, Any]:
        try:
            info: dict[str, Any] = {"title": title}
            if document_title:
                info["documentTitle"] = document_title
            response = self.client.forms().create(body={"info": info}).execute()
            return {
                "status": "success",
                "form_id": response.get("formId"),
                "responder_uri": response.get("responderUri"),
                "title": response.get("info", {}).get("title", title),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GFORMS_CREATE_FAILED",
                "message": str(exc),
            }

    def list_responses(self, form_id: str, page_size: int = 50) -> dict[str, Any]:
        try:
            response = self.client.forms().responses().list(formId=form_id, pageSize=page_size).execute()
            responses = response.get("responses", [])
            normalized = [
                {
                    "response_id": item.get("responseId"),
                    "create_time": item.get("createTime"),
                    "last_submitted_time": item.get("lastSubmittedTime"),
                }
                for item in responses
            ]
            return {
                "status": "success",
                "form_id": form_id,
                "count": len(normalized),
                "responses": normalized,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GFORMS_LIST_RESPONSES_FAILED",
                "message": str(exc),
            }
