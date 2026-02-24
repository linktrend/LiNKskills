from __future__ import annotations

import base64
import mimetypes
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from googleapiclient.discovery import build

from utils.auth import GWAuth


class GmailService:
    """Service wrapper for Gmail API operations."""

    def __init__(self, config_path: str | Path, user_id: str = "me") -> None:
        self.user_id = user_id
        auth = GWAuth(config_path=config_path)
        credentials = auth.get_credentials()
        self.client = build("gmail", "v1", credentials=credentials, cache_discovery=False)

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str | None = None,
        bcc: str | None = None,
        attachments: list[str] | None = None,
    ) -> dict[str, Any]:
        try:
            message = EmailMessage()
            message["To"] = to
            message["Subject"] = subject
            if cc:
                message["Cc"] = cc
            if bcc:
                message["Bcc"] = bcc
            message.set_content(body)

            for attachment in attachments or []:
                path = Path(attachment).expanduser()
                payload = path.read_bytes()
                mime_type, _ = mimetypes.guess_type(path.name)
                if mime_type:
                    maintype, subtype = mime_type.split("/", maxsplit=1)
                else:
                    maintype, subtype = "application", "octet-stream"
                message.add_attachment(
                    payload,
                    maintype=maintype,
                    subtype=subtype,
                    filename=path.name,
                )

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            response = (
                self.client.users()
                .messages()
                .send(userId=self.user_id, body={"raw": encoded_message})
                .execute()
            )
            return {
                "status": "success",
                "message_id": response.get("id"),
                "thread_id": response.get("threadId"),
            }
        except FileNotFoundError as exc:
            return {
                "status": "error",
                "code": "GMAIL_ATTACHMENT_NOT_FOUND",
                "message": str(exc),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GMAIL_SEND_FAILED",
                "message": str(exc),
            }

    def list_messages(self, label: str = "INBOX", max_results: int = 10) -> dict[str, Any]:
        try:
            response = (
                self.client.users()
                .messages()
                .list(userId=self.user_id, labelIds=[label], maxResults=max_results)
                .execute()
            )
            messages = response.get("messages", [])
            summaries: list[dict[str, Any]] = []
            for message in messages:
                details = (
                    self.client.users()
                    .messages()
                    .get(
                        userId=self.user_id,
                        id=message["id"],
                        format="metadata",
                        metadataHeaders=["From", "Subject", "Date"],
                    )
                    .execute()
                )
                headers = self._headers_to_map(details.get("payload", {}).get("headers", []))
                summaries.append(
                    {
                        "message_id": details.get("id"),
                        "thread_id": details.get("threadId"),
                        "snippet": details.get("snippet", ""),
                        "from": headers.get("From", ""),
                        "subject": headers.get("Subject", ""),
                        "date": headers.get("Date", ""),
                    }
                )

            return {
                "status": "success",
                "label": label,
                "count": len(summaries),
                "messages": summaries,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GMAIL_LIST_FAILED",
                "message": str(exc),
            }

    def get_message(self, message_id: str) -> dict[str, Any]:
        try:
            response = (
                self.client.users()
                .messages()
                .get(userId=self.user_id, id=message_id, format="full")
                .execute()
            )
            payload = response.get("payload", {})
            headers = self._headers_to_map(payload.get("headers", []))
            body = self._extract_body(payload)
            return {
                "status": "success",
                "message_id": response.get("id"),
                "thread_id": response.get("threadId"),
                "snippet": response.get("snippet", ""),
                "from": headers.get("From", ""),
                "to": headers.get("To", ""),
                "subject": headers.get("Subject", ""),
                "date": headers.get("Date", ""),
                "body": body,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GMAIL_GET_FAILED",
                "message": str(exc),
            }

    def search(self, query: str) -> dict[str, Any]:
        try:
            response = (
                self.client.users()
                .threads()
                .list(userId=self.user_id, q=query)
                .execute()
            )
            threads = response.get("threads", [])
            normalized_threads = [
                {
                    "thread_id": thread.get("id"),
                    "history_id": thread.get("historyId"),
                    "snippet": thread.get("snippet", ""),
                }
                for thread in threads
            ]
            return {
                "status": "success",
                "query": query,
                "count": len(normalized_threads),
                "threads": normalized_threads,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GMAIL_SEARCH_FAILED",
                "message": str(exc),
            }

    def _extract_body(self, payload: dict[str, Any]) -> str:
        plain = self._find_part_data(payload, target_mime_type="text/plain")
        if plain:
            return plain
        html = self._find_part_data(payload, target_mime_type="text/html")
        return html

    def _find_part_data(self, part: dict[str, Any], target_mime_type: str) -> str:
        mime_type = part.get("mimeType")
        body_data = part.get("body", {}).get("data")
        if mime_type == target_mime_type and body_data:
            return self._decode_base64url(body_data)

        for child in part.get("parts", []) or []:
            nested = self._find_part_data(child, target_mime_type=target_mime_type)
            if nested:
                return nested

        if body_data and not part.get("parts"):
            return self._decode_base64url(body_data)
        return ""

    def _decode_base64url(self, raw_data: str) -> str:
        padded = raw_data + "=" * (-len(raw_data) % 4)
        return base64.urlsafe_b64decode(padded.encode("utf-8")).decode(
            "utf-8",
            errors="replace",
        )

    def _headers_to_map(self, headers: list[dict[str, str]]) -> dict[str, str]:
        mapped: dict[str, str] = {}
        for header in headers:
            name = header.get("name")
            value = header.get("value", "")
            if name:
                mapped[name] = value
        return mapped
