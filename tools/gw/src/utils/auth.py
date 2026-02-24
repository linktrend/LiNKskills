from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


class GWAuth:
    """Manage OAuth credentials for the gw CLI."""

    SCOPES: list[str] = [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/tasks",
        "https://www.googleapis.com/auth/chat.spaces.readonly",
        "https://www.googleapis.com/auth/chat.messages.create",
        "https://www.googleapis.com/auth/youtube.force-ssl",
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/analytics.readonly",
        "https://www.googleapis.com/auth/yt-analytics.readonly",
        "https://www.googleapis.com/auth/webmasters.readonly",
        "https://www.googleapis.com/auth/forms.body",
        "https://www.googleapis.com/auth/forms.responses.readonly",
        "https://www.googleapis.com/auth/adwords",
    ]

    # Local identity isolation: token storage is pinned to the gateway source
    # directory (same directory as cli.py) to avoid cross-project token reuse.
    LOCAL_TOKEN_PATH = Path(__file__).resolve().parent.parent / "token.json"

    def __init__(self, config_path: str | Path, token_path: str | Path | None = None) -> None:
        self.config_path = Path(config_path).expanduser().resolve()
        if token_path is not None:
            self.token_path = Path(token_path).expanduser().resolve()
        else:
            self.token_path = self.LOCAL_TOKEN_PATH.resolve()

    def get_credentials(self) -> Credentials:
        """Load credentials from disk, refresh if expired, or start OAuth flow."""
        credentials: Credentials | None = None

        if self.token_path.exists():
            try:
                credentials = Credentials.from_authorized_user_file(
                    str(self.token_path),
                    scopes=self.SCOPES,
                )
            except Exception:
                credentials = None

        if credentials and credentials.valid:
            return credentials

        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
                self._write_token(credentials)
                return credentials
            except Exception:
                credentials = None

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"OAuth client config not found at: {self.config_path}"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.config_path),
            scopes=self.SCOPES,
        )
        credentials = flow.run_local_server(port=0)
        self._write_token(credentials)
        return credentials

    def _write_token(self, credentials: Credentials) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(credentials.to_json(), encoding="utf-8")
        self.token_path.chmod(0o600)
