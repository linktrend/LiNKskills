from __future__ import annotations

from pathlib import Path
from typing import Any

from googleapiclient.discovery import build

from utils.auth import GWAuth


class DocsService:
    """Service wrapper for Google Docs API operations."""

    def __init__(self, config_path: str | Path, user_id: str = "me") -> None:
        self.user_id = user_id
        auth = GWAuth(config_path=config_path)
        credentials = auth.get_credentials()
        self.client = build("docs", "v1", credentials=credentials, cache_discovery=False)

    def create(self, title: str) -> dict[str, Any]:
        try:
            response = self.client.documents().create(body={"title": title}).execute()
            return {
                "status": "success",
                "document_id": response.get("documentId"),
                "revision_id": response.get("revisionId"),
                "title": response.get("title"),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GDOCS_CREATE_FAILED",
                "message": str(exc),
            }

    def get_content(self, document_id: str) -> dict[str, Any]:
        try:
            document = self.client.documents().get(documentId=document_id).execute()
            plain_text = self._extract_plain_text(document)
            return {
                "status": "success",
                "document_id": document.get("documentId"),
                "revision_id": document.get("revisionId"),
                "content": plain_text,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GDOCS_GET_CONTENT_FAILED",
                "message": str(exc),
            }

    def append_text(self, document_id: str, text: str) -> dict[str, Any]:
        try:
            document = self.client.documents().get(documentId=document_id).execute()
            insert_index = self._end_insert_index(document)
            self.client.documents().batchUpdate(
                documentId=document_id,
                body={
                    "requests": [
                        {
                            "insertText": {
                                "location": {"index": insert_index},
                                "text": text,
                            }
                        }
                    ]
                },
            ).execute()
            revision_id = self._get_revision_id(document_id=document_id)
            return {
                "status": "success",
                "document_id": document_id,
                "revision_id": revision_id,
                "appended_chars": len(text),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GDOCS_APPEND_FAILED",
                "message": str(exc),
            }

    def replace_text(
        self,
        document_id: str,
        placeholder: str,
        replacement: str,
    ) -> dict[str, Any]:
        try:
            response = self.client.documents().batchUpdate(
                documentId=document_id,
                body={
                    "requests": [
                        {
                            "replaceAllText": {
                                "containsText": {
                                    "text": placeholder,
                                    "matchCase": True,
                                },
                                "replaceText": replacement,
                            }
                        }
                    ]
                },
            ).execute()
            replies = response.get("replies", [])
            replaced_count = 0
            if replies:
                replaced_count = int(
                    replies[0].get("replaceAllText", {}).get("occurrencesChanged", 0)
                )
            revision_id = self._get_revision_id(document_id=document_id)
            return {
                "status": "success",
                "document_id": document_id,
                "revision_id": revision_id,
                "replaced_count": replaced_count,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GDOCS_REPLACE_FAILED",
                "message": str(exc),
            }

    def append_markdown(self, document_id: str, markdown_text: str) -> dict[str, Any]:
        try:
            if not markdown_text:
                revision_id = self._get_revision_id(document_id=document_id)
                return {
                    "status": "success",
                    "document_id": document_id,
                    "revision_id": revision_id,
                    "appended_chars": 0,
                    "headings_applied": 0,
                }

            document = self.client.documents().get(documentId=document_id).execute()
            insert_index = self._end_insert_index(document)

            lines = markdown_text.splitlines()
            requests: list[dict[str, Any]] = []
            formatted_lines: list[str] = []
            heading_ranges: list[dict[str, Any]] = []

            offset = 0
            for line in lines:
                style_type = ""
                line_text = line
                if line.startswith("## "):
                    style_type = "HEADING_2"
                    line_text = line[3:]
                elif line.startswith("# "):
                    style_type = "HEADING_1"
                    line_text = line[2:]

                line_with_newline = f"{line_text}\n"
                formatted_lines.append(line_with_newline)

                if style_type:
                    start_index = insert_index + offset
                    end_index = start_index + len(line_text) + 1
                    heading_ranges.append(
                        {
                            "startIndex": start_index,
                            "endIndex": end_index,
                            "namedStyleType": style_type,
                        }
                    )

                offset += len(line_with_newline)

            full_text = "".join(formatted_lines)
            requests.append(
                {
                    "insertText": {
                        "location": {"index": insert_index},
                        "text": full_text,
                    }
                }
            )

            for heading_range in heading_ranges:
                requests.append(
                    {
                        "updateParagraphStyle": {
                            "range": {
                                "startIndex": heading_range["startIndex"],
                                "endIndex": heading_range["endIndex"],
                            },
                            "paragraphStyle": {
                                "namedStyleType": heading_range["namedStyleType"]
                            },
                            "fields": "namedStyleType",
                        }
                    }
                )

            self.client.documents().batchUpdate(
                documentId=document_id,
                body={"requests": requests},
            ).execute()
            revision_id = self._get_revision_id(document_id=document_id)
            return {
                "status": "success",
                "document_id": document_id,
                "revision_id": revision_id,
                "appended_chars": len(full_text),
                "headings_applied": len(heading_ranges),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GDOCS_APPEND_MARKDOWN_FAILED",
                "message": str(exc),
            }

    def _extract_plain_text(self, document: dict[str, Any]) -> str:
        text_parts: list[str] = []
        for element in document.get("body", {}).get("content", []):
            paragraph = element.get("paragraph")
            if not paragraph:
                continue
            for item in paragraph.get("elements", []):
                text_run = item.get("textRun")
                if text_run:
                    text_parts.append(text_run.get("content", ""))
        return "".join(text_parts).rstrip()

    def _end_insert_index(self, document: dict[str, Any]) -> int:
        content = document.get("body", {}).get("content", [])
        if not content:
            return 1
        end_index = int(content[-1].get("endIndex", 1))
        return max(1, end_index - 1)

    def _get_revision_id(self, document_id: str) -> str | None:
        document = (
            self.client.documents()
            .get(documentId=document_id, fields="documentId,revisionId")
            .execute()
        )
        revision = document.get("revisionId")
        return str(revision) if revision is not None else None
