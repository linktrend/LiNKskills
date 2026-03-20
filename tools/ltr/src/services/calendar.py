from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from googleapiclient.discovery import build

from utils.auth import LTRAuth


class CalendarService:
    """Service wrapper for Google Calendar API operations."""

    def __init__(self, config_path: str | Path, user_id: str = "me") -> None:
        self.user_id = user_id
        auth = LTRAuth(config_path=config_path)
        credentials = auth.get_credentials()
        self.client = build("calendar", "v3", credentials=credentials, cache_discovery=False)

    def list_events(
        self,
        calendar_id: str = "primary",
        time_min: str | None = None,
        max_results: int = 10,
    ) -> dict[str, Any]:
        try:
            normalized_time_min = self._normalize_iso8601(time_min) if time_min else self._utc_now_iso8601()
            response = (
                self.client.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=normalized_time_min,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            items = response.get("items", [])
            events = [
                {
                    "event_id": item.get("id"),
                    "summary": item.get("summary", ""),
                    "start": (item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")),
                    "end": (item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")),
                    "htmlLink": item.get("htmlLink"),
                    "hangoutLink": item.get("hangoutLink"),
                    "status": item.get("status"),
                }
                for item in items
            ]
            return {
                "status": "success",
                "calendar_id": calendar_id,
                "count": len(events),
                "events": events,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GCALENDAR_LIST_FAILED",
                "message": str(exc),
            }

    def create_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        description: str | None = None,
        attendees: list[str] | None = None,
        add_meet: bool = False,
    ) -> dict[str, Any]:
        try:
            start = self._normalize_iso8601(start_time)
            end = self._normalize_iso8601(end_time)
            body: dict[str, Any] = {
                "summary": title,
                "start": {"dateTime": start},
                "end": {"dateTime": end},
            }
            if description:
                body["description"] = description
            if attendees:
                body["attendees"] = [{"email": email} for email in attendees]
            if add_meet:
                body["conferenceData"] = {
                    "createRequest": {
                        "requestId": uuid4().hex,
                        "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    }
                }

            request = self.client.events().insert(calendarId="primary", body=body)
            if add_meet:
                response = request.execute(conferenceDataVersion=1)
            else:
                response = request.execute()

            return {
                "status": "success",
                "calendar_id": "primary",
                "event_id": response.get("id"),
                "summary": response.get("summary", title),
                "start": response.get("start", {}).get("dateTime"),
                "end": response.get("end", {}).get("dateTime"),
                "htmlLink": response.get("htmlLink"),
                "hangoutLink": response.get("hangoutLink"),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GCALENDAR_CREATE_FAILED",
                "message": str(exc),
            }

    def update_event(
        self,
        event_id: str,
        title: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> dict[str, Any]:
        try:
            updates: dict[str, Any] = {}
            if title is not None:
                updates["summary"] = title
            if start_time is not None:
                updates["start"] = {"dateTime": self._normalize_iso8601(start_time)}
            if end_time is not None:
                updates["end"] = {"dateTime": self._normalize_iso8601(end_time)}
            if not updates:
                return {
                    "status": "error",
                    "code": "GCALENDAR_UPDATE_NO_FIELDS",
                    "message": "No fields were provided for update.",
                }

            response = (
                self.client.events()
                .patch(calendarId="primary", eventId=event_id, body=updates)
                .execute()
            )
            return {
                "status": "success",
                "calendar_id": "primary",
                "event_id": response.get("id"),
                "summary": response.get("summary"),
                "start": response.get("start", {}).get("dateTime"),
                "end": response.get("end", {}).get("dateTime"),
                "htmlLink": response.get("htmlLink"),
                "hangoutLink": response.get("hangoutLink"),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GCALENDAR_UPDATE_FAILED",
                "message": str(exc),
            }

    def delete_event(self, event_id: str) -> dict[str, Any]:
        try:
            self.client.events().delete(calendarId="primary", eventId=event_id).execute()
            return {
                "status": "success",
                "calendar_id": "primary",
                "event_id": event_id,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GCALENDAR_DELETE_FAILED",
                "message": str(exc),
            }

    def get_free_busy(
        self,
        time_min: str,
        time_max: str,
        calendar_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        try:
            normalized_min = self._normalize_iso8601(time_min)
            normalized_max = self._normalize_iso8601(time_max)
            target_calendars = calendar_ids or ["primary"]
            response = (
                self.client.freebusy()
                .query(
                    body={
                        "timeMin": normalized_min,
                        "timeMax": normalized_max,
                        "items": [{"id": calendar_id} for calendar_id in target_calendars],
                    }
                )
                .execute()
            )
            calendars = response.get("calendars", {})
            busy_by_calendar: dict[str, list[dict[str, Any]]] = {}
            for calendar_id, data in calendars.items():
                blocks = data.get("busy", [])
                busy_by_calendar[calendar_id] = [
                    {
                        "start": block.get("start"),
                        "end": block.get("end"),
                    }
                    for block in blocks
                ]
            return {
                "status": "success",
                "time_min": normalized_min,
                "time_max": normalized_max,
                "busy": busy_by_calendar,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GCALENDAR_FREEBUSY_FAILED",
                "message": str(exc),
            }

    def _normalize_iso8601(self, value: str) -> str:
        candidate = value.strip()
        if candidate.endswith("Z"):
            candidate = f"{candidate[:-1]}+00:00"
        parsed = datetime.fromisoformat(candidate)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.isoformat()

    def _utc_now_iso8601(self) -> str:
        return datetime.now(timezone.utc).isoformat()
