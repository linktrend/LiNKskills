from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from utils.auth import GWAuth


class DriveService:
    """Service wrapper for Google Drive API operations."""

    ALLOWED_SHARE_RECIPIENT: str = "calusa@linktrend.media"
    EXPORT_MIME_TYPES: dict[str, str] = {
        "application/vnd.google-apps.document": "application/pdf",
        "application/vnd.google-apps.spreadsheet": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.google-apps.presentation": "application/pdf",
        "application/vnd.google-apps.drawing": "application/pdf",
    }
    CONVERSION_MIME_TYPES: dict[str, str] = {
        "text/plain": "application/vnd.google-apps.document",
        "text/markdown": "application/vnd.google-apps.document",
        "text/csv": "application/vnd.google-apps.spreadsheet",
        "application/vnd.ms-excel": "application/vnd.google-apps.spreadsheet",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "application/vnd.google-apps.spreadsheet",
    }

    def __init__(self, config_path: str | Path, user_id: str = "me") -> None:
        self.user_id = user_id
        auth = GWAuth(config_path=config_path)
        credentials = auth.get_credentials()
        self.client = build("drive", "v3", credentials=credentials, cache_discovery=False)

    def list_files(self, query: str | None = None, page_size: int = 10) -> dict[str, Any]:
        try:
            response = (
                self.client.files()
                .list(
                    q=query,
                    pageSize=page_size,
                    fields="files(id,name,mimeType,parents)",
                )
                .execute()
            )
            files = response.get("files", [])
            normalized = [
                {
                    "file_id": file_data.get("id"),
                    "name": file_data.get("name"),
                    "mimeType": file_data.get("mimeType"),
                    "parents": file_data.get("parents", []),
                }
                for file_data in files
            ]
            return {
                "status": "success",
                "count": len(normalized),
                "files": normalized,
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GDRIVE_LIST_FAILED",
                "message": str(exc),
            }

    def upload(
        self,
        file_path: str,
        folder_id: str | None = None,
        convert: bool = False,
    ) -> dict[str, Any]:
        try:
            path = Path(file_path).expanduser().resolve()
            if not path.exists():
                return {
                    "status": "error",
                    "code": "GDRIVE_UPLOAD_FILE_NOT_FOUND",
                    "message": f"File not found: {path}",
                }

            source_mime_type, _ = mimetypes.guess_type(path.name)
            metadata: dict[str, Any] = {"name": path.name}
            if folder_id:
                metadata["parents"] = [folder_id]

            if convert and source_mime_type:
                target_mime = self.CONVERSION_MIME_TYPES.get(source_mime_type)
                if target_mime:
                    metadata["mimeType"] = target_mime

            media = MediaFileUpload(
                str(path),
                mimetype=source_mime_type or "application/octet-stream",
                resumable=False,
            )
            created = (
                self.client.files()
                .create(body=metadata, media_body=media, fields="id,name,mimeType")
                .execute()
            )
            return {
                "status": "success",
                "file_id": created.get("id"),
                "name": created.get("name"),
                "mimeType": created.get("mimeType"),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GDRIVE_UPLOAD_FAILED",
                "message": str(exc),
            }

    def download(self, file_id: str, local_path: str) -> dict[str, Any]:
        try:
            metadata = (
                self.client.files()
                .get(fileId=file_id, fields="id,name,mimeType")
                .execute()
            )
            file_name = str(metadata.get("name", "downloaded_file"))
            source_mime_type = str(metadata.get("mimeType", "application/octet-stream"))
            destination = Path(local_path).expanduser()
            destination.parent.mkdir(parents=True, exist_ok=True)

            if source_mime_type.startswith("application/vnd.google-apps"):
                export_mime_type = self.EXPORT_MIME_TYPES.get(source_mime_type)
                if not export_mime_type:
                    return {
                        "status": "error",
                        "code": "GDRIVE_UNSUPPORTED_EXPORT",
                        "message": f"Unsupported Google file export for mimeType: {source_mime_type}",
                    }
                request = self.client.files().export_media(
                    fileId=file_id,
                    mimeType=export_mime_type,
                )
            else:
                request = self.client.files().get_media(fileId=file_id)

            with destination.open("wb") as handle:
                downloader = MediaIoBaseDownload(handle, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()

            return {
                "status": "success",
                "file_id": metadata.get("id"),
                "name": file_name,
                "mimeType": source_mime_type,
                "local_path": str(destination),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GDRIVE_DOWNLOAD_FAILED",
                "message": str(exc),
            }

    def create_folder(self, name: str, parent_id: str | None = None) -> dict[str, Any]:
        try:
            metadata: dict[str, Any] = {
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if parent_id:
                metadata["parents"] = [parent_id]
            created = (
                self.client.files()
                .create(body=metadata, fields="id,name,mimeType")
                .execute()
            )
            return {
                "status": "success",
                "file_id": created.get("id"),
                "name": created.get("name"),
                "mimeType": created.get("mimeType"),
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GDRIVE_CREATE_FOLDER_FAILED",
                "message": str(exc),
            }

    def share(
        self,
        file_id: str,
        role: str = "reader",
        notify: bool = True,
        recipient: str = ALLOWED_SHARE_RECIPIENT,
    ) -> dict[str, Any]:
        if recipient != self.ALLOWED_SHARE_RECIPIENT:
            return {
                "status": "error",
                "code": "GDRIVE_FORBIDDEN_RECIPIENT",
                "message": (
                    "Sharing is restricted. Allowed recipient: "
                    f"{self.ALLOWED_SHARE_RECIPIENT}"
                ),
                "resource_id": f"{file_id}:{recipient}",
            }

        try:
            permission_body = {
                "type": "user",
                "role": role,
                "emailAddress": self.ALLOWED_SHARE_RECIPIENT,
            }
            permission = (
                self.client.permissions()
                .create(
                    fileId=file_id,
                    body=permission_body,
                    sendNotificationEmail=notify,
                    fields="id,emailAddress,role",
                )
                .execute()
            )
            file_data = (
                self.client.files()
                .get(fileId=file_id, fields="id,name,mimeType")
                .execute()
            )
            return {
                "status": "success",
                "file_id": file_data.get("id"),
                "name": file_data.get("name"),
                "mimeType": file_data.get("mimeType"),
                "permission_id": permission.get("id"),
                "recipient": permission.get("emailAddress", self.ALLOWED_SHARE_RECIPIENT),
                "role": permission.get("role", role),
                "resource_id": f"{file_data.get('id')}:{self.ALLOWED_SHARE_RECIPIENT}",
            }
        except Exception as exc:
            return {
                "status": "error",
                "code": "GDRIVE_SHARE_FAILED",
                "message": str(exc),
            }
