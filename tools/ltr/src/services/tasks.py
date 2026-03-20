from __future__ import annotations

from pathlib import Path
from typing import Any

from googleapiclient.discovery import build

from utils.auth import LTRAuth


class TasksService:
    """Service wrapper for Google Tasks API operations."""

    def __init__(self, config_path: str | Path, user_id: str = "me") -> None:
        self.user_id = user_id
        auth = LTRAuth(config_path=config_path)
        credentials = auth.get_credentials()
        self.client = build("tasks", "v1", credentials=credentials, cache_discovery=False)

    def list_task_lists(self) -> dict[str, Any]:
        try:
            response = self.client.tasklists().list().execute()
            task_lists = response.get("items", [])
            normalized = [
                {
                    "list_id": item.get("id"),
                    "title": item.get("title", ""),
                    "updated": item.get("updated"),
                    "selfLink": item.get("selfLink"),
                }
                for item in task_lists
            ]
            return {
                "status": "success",
                "count": len(normalized),
                "task_lists": normalized,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GTASKS_LIST_LISTS_FAILED",
                "message": str(exc),
            }

    def list_tasks(self, list_id: str = "@default") -> dict[str, Any]:
        try:
            response = self.client.tasks().list(tasklist=list_id, showCompleted=True, showHidden=True).execute()
            tasks = response.get("items", [])
            normalized = [
                {
                    "task_id": item.get("id"),
                    "title": item.get("title", ""),
                    "notes": item.get("notes", ""),
                    "status": item.get("status"),
                    "due": item.get("due"),
                    "completed": item.get("completed"),
                    "updated": item.get("updated"),
                }
                for item in tasks
            ]
            return {
                "status": "success",
                "list_id": list_id,
                "count": len(normalized),
                "tasks": normalized,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GTASKS_LIST_FAILED",
                "message": str(exc),
            }

    def create_task(
        self,
        title: str,
        notes: str | None = None,
        due: str | None = None,
        list_id: str = "@default",
    ) -> dict[str, Any]:
        try:
            body: dict[str, Any] = {
                "title": title,
            }
            if notes:
                body["notes"] = notes
            if due:
                body["due"] = due

            response = self.client.tasks().insert(tasklist=list_id, body=body).execute()
            return {
                "status": "success",
                "list_id": list_id,
                "task_id": response.get("id"),
                "title": response.get("title", title),
                "due": response.get("due"),
                "updated": response.get("updated"),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GTASKS_CREATE_FAILED",
                "message": str(exc),
            }

    def delete_task(self, task_id: str, list_id: str = "@default") -> dict[str, Any]:
        try:
            self.client.tasks().delete(tasklist=list_id, task=task_id).execute()
            return {
                "status": "success",
                "list_id": list_id,
                "task_id": task_id,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GTASKS_DELETE_FAILED",
                "message": str(exc),
            }
