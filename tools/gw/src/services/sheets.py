from __future__ import annotations

from pathlib import Path
from typing import Any

from googleapiclient.discovery import build

from utils.auth import GWAuth


class SheetsService:
    """Service wrapper for Google Sheets API operations."""

    def __init__(self, config_path: str | Path, user_id: str = "me") -> None:
        self.user_id = user_id
        auth = GWAuth(config_path=config_path)
        credentials = auth.get_credentials()
        try:
            self.client = build(
                "sheets",
                "v1",
                credentials=credentials,
                cache_discovery=False,
            )
        except Exception:
            self.client = build(
                "sheets",
                "v4",
                credentials=credentials,
                cache_discovery=False,
            )

    def create(self, title: str) -> dict[str, Any]:
        try:
            response = (
                self.client.spreadsheets()
                .create(
                    body={"properties": {"title": title}},
                    fields="spreadsheetId,properties.title",
                )
                .execute()
            )
            return {
                "status": "success",
                "spreadsheet_id": response.get("spreadsheetId"),
                "title": response.get("properties", {}).get("title"),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GSHEETS_CREATE_FAILED",
                "message": str(exc),
            }

    def append_row(
        self,
        spreadsheet_id: str,
        values: list[Any] | list[list[Any]],
        range_name: str = "Sheet1!A1",
    ) -> dict[str, Any]:
        try:
            rows = self._normalize_rows(values)
            response = (
                self.client.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body={"values": rows},
                )
                .execute()
            )
            updates = response.get("updates", {})
            return {
                "status": "success",
                "spreadsheet_id": spreadsheet_id,
                "updated_range": updates.get("updatedRange"),
                "updated_rows": updates.get("updatedRows", 0),
                "updated_cells": updates.get("updatedCells", 0),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GSHEETS_APPEND_FAILED",
                "message": str(exc),
            }

    def update_range(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: list[Any] | list[list[Any]],
    ) -> dict[str, Any]:
        try:
            rows = self._normalize_rows(values)
            response = (
                self.client.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="USER_ENTERED",
                    body={"values": rows},
                )
                .execute()
            )
            return {
                "status": "success",
                "spreadsheet_id": spreadsheet_id,
                "updated_range": response.get("updatedRange"),
                "updated_rows": response.get("updatedRows", 0),
                "updated_cells": response.get("updatedCells", 0),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GSHEETS_UPDATE_FAILED",
                "message": str(exc),
            }

    def read_range(self, spreadsheet_id: str, range_name: str) -> dict[str, Any]:
        try:
            response = (
                self.client.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_name)
                .execute()
            )
            raw_values = response.get("values", [])
            values: list[list[Any]] = []
            for row in raw_values:
                if isinstance(row, list):
                    values.append(row)
                else:
                    values.append([row])
            return {
                "status": "success",
                "spreadsheet_id": spreadsheet_id,
                "range": response.get("range", range_name),
                "values": values,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GSHEETS_READ_FAILED",
                "message": str(exc),
            }

    def add_sheet(self, spreadsheet_id: str, title: str) -> dict[str, Any]:
        try:
            response = (
                self.client.spreadsheets()
                .batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={
                        "requests": [
                            {
                                "addSheet": {
                                    "properties": {"title": title},
                                }
                            }
                        ]
                    },
                )
                .execute()
            )
            replies = response.get("replies", [])
            sheet_props: dict[str, Any] = {}
            if replies:
                sheet_props = replies[0].get("addSheet", {}).get("properties", {})
            return {
                "status": "success",
                "spreadsheet_id": spreadsheet_id,
                "sheet_id": sheet_props.get("sheetId"),
                "title": sheet_props.get("title", title),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GSHEETS_ADD_SHEET_FAILED",
                "message": str(exc),
            }

    def _normalize_rows(self, values: list[Any] | list[list[Any]]) -> list[list[Any]]:
        if not values:
            return []
        if all(isinstance(item, list) for item in values):
            normalized: list[list[Any]] = []
            for item in values:
                if isinstance(item, list):
                    normalized.append(list(item))
            return normalized
        return [list(values)]
