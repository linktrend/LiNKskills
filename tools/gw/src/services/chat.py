from __future__ import annotations

from pathlib import Path
from typing import Any

from googleapiclient.discovery import build

from utils.auth import GWAuth


class ChatService:
    """Service wrapper for Google Chat API operations."""

    def __init__(self, config_path: str | Path, user_id: str = "me") -> None:
        self.user_id = user_id
        auth = GWAuth(config_path=config_path)
        credentials = auth.get_credentials()
        self.client = build("chat", "v1", credentials=credentials, cache_discovery=False)

    def list_spaces(self, page_size: int = 20) -> dict[str, Any]:
        try:
            normalized_page_size = max(1, min(int(page_size), 1000))
            response = self.client.spaces().list(pageSize=normalized_page_size).execute()
            spaces = response.get("spaces", [])
            normalized = [
                {
                    "name": space.get("name"),
                    "displayName": space.get("displayName", ""),
                    "spaceType": space.get("spaceType", ""),
                    "singleUserBotDm": bool(space.get("singleUserBotDm", False)),
                }
                for space in spaces
            ]
            return {
                "status": "success",
                "page_size": normalized_page_size,
                "count": len(normalized),
                "spaces": normalized,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GCHAT_LIST_SPACES_FAILED",
                "message": str(exc),
            }

    def send_message(self, space_name: str, text: str) -> dict[str, Any]:
        try:
            response = (
                self.client.spaces()
                .messages()
                .create(
                    parent=space_name,
                    body={"text": text},
                )
                .execute()
            )
            return {
                "status": "success",
                "space_name": space_name,
                "message_name": response.get("name"),
                "createTime": response.get("createTime"),
                "thread_name": response.get("thread", {}).get("name"),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GCHAT_SEND_FAILED",
                "message": str(exc),
            }

    def get_space(self, space_name: str) -> dict[str, Any]:
        try:
            response = self.client.spaces().get(name=space_name).execute()
            return {
                "status": "success",
                "space_name": response.get("name"),
                "displayName": response.get("displayName", ""),
                "spaceType": response.get("spaceType", ""),
                "spaceThreadingState": response.get("spaceThreadingState", ""),
                "spaceDetails": response.get("spaceDetails", {}),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GCHAT_GET_SPACE_FAILED",
                "message": str(exc),
            }

    def get_membership(self, space_name: str, member_name: str) -> dict[str, Any]:
        try:
            membership_name = member_name
            if not member_name.startswith("spaces/"):
                membership_name = f"{space_name}/members/{member_name}"
            response = (
                self.client.spaces()
                .members()
                .get(name=membership_name)
                .execute()
            )
            return {
                "status": "success",
                "space_name": space_name,
                "membership_name": response.get("name"),
                "role": response.get("role"),
                "state": response.get("state"),
                "member": response.get("member", {}),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GCHAT_GET_MEMBERSHIP_FAILED",
                "message": str(exc),
            }
