from __future__ import annotations

from pathlib import Path
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from utils.auth import GWAuth


class YouTubeService:
    """Service wrapper for YouTube Data API v3 operations."""

    def __init__(self, config_path: str | Path, user_id: str = "me") -> None:
        self.user_id = user_id
        auth = GWAuth(config_path=config_path)
        credentials = auth.get_credentials()
        self.client = build("youtube", "v3", credentials=credentials, cache_discovery=False)

    def get_channel_stats(self) -> dict[str, Any]:
        try:
            response = self.client.channels().list(part="snippet,statistics", mine=True).execute()
            items = response.get("items", [])
            if not items:
                return {
                    "status": "error",
                    "code": "GYOUTUBE_CHANNEL_NOT_FOUND",
                    "message": "No channel found for authenticated account.",
                }

            channel = items[0]
            snippet = channel.get("snippet", {})
            stats = channel.get("statistics", {})
            return {
                "status": "success",
                "channel_id": channel.get("id"),
                "title": snippet.get("title", ""),
                "subscriber_count": stats.get("subscriberCount"),
                "view_count": stats.get("viewCount"),
                "video_count": stats.get("videoCount"),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GYOUTUBE_STATS_FAILED",
                "message": str(exc),
            }

    def upload_video(
        self,
        file_path: str,
        title: str,
        description: str,
        category_id: str = "27",
        tags: list[str] | None = None,
        privacy: str = "private",
    ) -> dict[str, Any]:
        try:
            path = Path(file_path).expanduser().resolve()
            if not path.exists():
                return {
                    "status": "error",
                    "code": "GYOUTUBE_UPLOAD_FILE_NOT_FOUND",
                    "message": f"File not found: {path}",
                }

            body: dict[str, Any] = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "categoryId": category_id,
                },
                "status": {
                    "privacyStatus": privacy,
                },
            }
            if tags:
                body["snippet"]["tags"] = tags

            media = MediaFileUpload(str(path), resumable=True)
            request = self.client.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            )

            response: dict[str, Any] | None = None
            while response is None:
                _, response = request.next_chunk()

            if not response or "id" not in response:
                return {
                    "status": "error",
                    "code": "GYOUTUBE_UPLOAD_FAILED",
                    "message": "Upload completed without video id in response.",
                }

            return {
                "status": "success",
                "video_id": response.get("id"),
                "title": title,
                "privacy": privacy,
                "category_id": category_id,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GYOUTUBE_UPLOAD_FAILED",
                "message": str(exc),
            }

    def list_comments(self, video_id: str, max_results: int = 20) -> dict[str, Any]:
        try:
            response = (
                self.client.commentThreads()
                .list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=max_results,
                    textFormat="plainText",
                )
                .execute()
            )
            items = response.get("items", [])
            comments = []
            for item in items:
                snippet = item.get("snippet", {})
                top_comment = snippet.get("topLevelComment", {})
                top_snippet = top_comment.get("snippet", {})
                comments.append(
                    {
                        "thread_id": item.get("id"),
                        "comment_id": top_comment.get("id"),
                        "author": top_snippet.get("authorDisplayName", ""),
                        "text": top_snippet.get("textDisplay", ""),
                        "published_at": top_snippet.get("publishedAt"),
                        "like_count": top_snippet.get("likeCount", 0),
                        "total_reply_count": snippet.get("totalReplyCount", 0),
                    }
                )

            return {
                "status": "success",
                "video_id": video_id,
                "count": len(comments),
                "comments": comments,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GYOUTUBE_LIST_COMMENTS_FAILED",
                "message": str(exc),
            }

    def reply_to_comment(self, parent_id: str, text: str) -> dict[str, Any]:
        try:
            response = (
                self.client.comments()
                .insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "parentId": parent_id,
                            "textOriginal": text,
                        }
                    },
                )
                .execute()
            )
            snippet = response.get("snippet", {})
            return {
                "status": "success",
                "comment_id": response.get("id"),
                "parent_id": snippet.get("parentId", parent_id),
                "text": snippet.get("textOriginal", text),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GYOUTUBE_REPLY_FAILED",
                "message": str(exc),
            }
