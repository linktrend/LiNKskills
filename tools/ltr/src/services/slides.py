from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from googleapiclient.discovery import build

from utils.auth import LTRAuth


class SlidesService:
    """Service wrapper for Google Slides API operations."""

    def __init__(self, config_path: str | Path, user_id: str = "me") -> None:
        self.user_id = user_id
        auth = LTRAuth(config_path=config_path)
        credentials = auth.get_credentials()
        self.client = build("slides", "v1", credentials=credentials, cache_discovery=False)

    def create(self, title: str) -> dict[str, Any]:
        try:
            response = self.client.presentations().create(body={"title": title}).execute()
            first_slide_object_id: str | None = None
            slides = response.get("slides", [])
            if slides:
                first_slide_object_id = slides[0].get("objectId")
            return {
                "status": "success",
                "presentation_id": response.get("presentationId"),
                "object_id": first_slide_object_id,
                "title": response.get("title", title),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GSLIDES_CREATE_FAILED",
                "message": str(exc),
            }

    def get_content(self, presentation_id: str) -> dict[str, Any]:
        try:
            presentation = (
                self.client.presentations()
                .get(presentationId=presentation_id)
                .execute()
            )
            slide_entries: list[dict[str, Any]] = []
            combined_chunks: list[str] = []

            for slide in presentation.get("slides", []):
                page_elements = slide.get("pageElements", [])
                text_chunks: list[str] = []
                for element in page_elements:
                    shape = element.get("shape")
                    if not shape:
                        continue
                    text_elements = shape.get("text", {}).get("textElements", [])
                    for text_element in text_elements:
                        run = text_element.get("textRun")
                        if not run:
                            continue
                        content = run.get("content", "")
                        if content:
                            text_chunks.append(content)

                slide_text = "".join(text_chunks).strip()
                slide_entry = {
                    "slide_id": slide.get("objectId"),
                    "text": slide_text,
                }
                slide_entries.append(slide_entry)
                if slide_text:
                    combined_chunks.append(slide_text)

            return {
                "status": "success",
                "presentation_id": presentation.get("presentationId"),
                "title": presentation.get("title", ""),
                "slides": slide_entries,
                "content": "\n\n".join(combined_chunks),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GSLIDES_GET_CONTENT_FAILED",
                "message": str(exc),
            }

    def add_slide(
        self,
        presentation_id: str,
        layout: str = "TITLE_AND_BODY",
    ) -> dict[str, Any]:
        try:
            slide_object_id = f"slide_{uuid4().hex[:12]}"
            self.client.presentations().batchUpdate(
                presentationId=presentation_id,
                body={
                    "requests": [
                        {
                            "createSlide": {
                                "objectId": slide_object_id,
                                "slideLayoutReference": {
                                    "predefinedLayout": layout,
                                },
                            }
                        }
                    ]
                },
            ).execute()
            return {
                "status": "success",
                "presentation_id": presentation_id,
                "object_id": slide_object_id,
                "layout": layout,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GSLIDES_ADD_SLIDE_FAILED",
                "message": str(exc),
            }

    def replace_text(
        self,
        presentation_id: str,
        placeholder: str,
        replacement: str,
    ) -> dict[str, Any]:
        try:
            response = self.client.presentations().batchUpdate(
                presentationId=presentation_id,
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
            occurrences_changed = 0
            if replies:
                occurrences_changed = int(
                    replies[0].get("replaceAllText", {}).get("occurrencesChanged", 0)
                )
            return {
                "status": "success",
                "presentation_id": presentation_id,
                "object_id": None,
                "occurrences_changed": occurrences_changed,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GSLIDES_REPLACE_TEXT_FAILED",
                "message": str(exc),
            }

    def insert_image(
        self,
        presentation_id: str,
        slide_id: str,
        image_url: str,
    ) -> dict[str, Any]:
        try:
            image_object_id = f"image_{uuid4().hex[:12]}"
            self.client.presentations().batchUpdate(
                presentationId=presentation_id,
                body={
                    "requests": [
                        {
                            "createImage": {
                                "objectId": image_object_id,
                                "url": image_url,
                                "elementProperties": {
                                    "pageObjectId": slide_id,
                                    "size": {
                                        "height": {"magnitude": 1800000, "unit": "EMU"},
                                        "width": {"magnitude": 3200000, "unit": "EMU"},
                                    },
                                    "transform": {
                                        "scaleX": 1,
                                        "scaleY": 1,
                                        "translateX": 800000,
                                        "translateY": 800000,
                                        "unit": "EMU",
                                    },
                                },
                            }
                        }
                    ]
                },
            ).execute()
            return {
                "status": "success",
                "presentation_id": presentation_id,
                "object_id": image_object_id,
                "slide_id": slide_id,
                "image_url": image_url,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GSLIDES_INSERT_IMAGE_FAILED",
                "message": str(exc),
            }
