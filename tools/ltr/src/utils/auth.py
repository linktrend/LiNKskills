from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


class LTRAuth:
    """Manage OAuth credentials for the ltr CLI."""

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
    VAULT_MODULE_PATH = Path(__file__).resolve().parents[4] / "tools" / "vault" / "src" / "vault_logic.py"
    VAULT_DATA_PATH = Path(__file__).resolve().parents[4] / "tools" / "vault" / "data" / "vault.bin"
    VAULT_DEFAULT_CREDENTIALS_KEY = "ltr.credentials.json"

    def __init__(
        self,
        config_path: str | Path,
        token_path: str | Path | None = None,
        vault_credentials_key: str | None = None,
    ) -> None:
        self.config_path = Path(config_path).expanduser().resolve()
        if token_path is not None:
            self.token_path = Path(token_path).expanduser().resolve()
        else:
            self.token_path = self.LOCAL_TOKEN_PATH.resolve()
        candidate_key = (
            vault_credentials_key
            or os.getenv("LSL_VAULT_CREDENTIALS_KEY")
            or self.VAULT_DEFAULT_CREDENTIALS_KEY
        )
        self.vault_credentials_key = candidate_key.strip()

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

        oauth_config = self._load_oauth_client_config()
        flow = InstalledAppFlow.from_client_config(
            oauth_config,
            scopes=self.SCOPES,
        )
        credentials = flow.run_local_server(port=0)
        self._write_token(credentials)
        return credentials

    def _load_oauth_client_config(self) -> dict[str, Any]:
        return self._read_config_from_vault()

    def _read_config_from_file(self, path: Path) -> dict[str, Any]:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError(f"OAuth client config must be a JSON object: {path}")
        return loaded

    def _vault_set_hint(self) -> str:
        return (
            f"Missing vault secret '{self.vault_credentials_key}'. "
            f"Run: ltr vault set {self.vault_credentials_key} /path/to/credentials.json"
        )

    def _read_config_from_vault(self) -> dict[str, Any]:
        master_key = os.getenv("LSL_MASTER_KEY", "").strip()
        if not master_key:
            raise EnvironmentError("LSL_MASTER_KEY is required for vault-backed credentials")

        if not self.VAULT_MODULE_PATH.exists():
            raise FileNotFoundError(f"Vault module not found at {self.VAULT_MODULE_PATH}")

        spec = importlib.util.spec_from_file_location(
            "lsl_vault_logic",
            str(self.VAULT_MODULE_PATH),
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load vault module spec from {self.VAULT_MODULE_PATH}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        vault_store_cls = getattr(module, "VaultStore", None)
        if vault_store_cls is None:
            raise AttributeError("VaultStore class not found in vault module")

        try:
            vault_store = vault_store_cls(
                data_path=self.VAULT_DATA_PATH,
                master_key=master_key,
            )
            raw_value = vault_store.get_value(self.vault_credentials_key)
        except KeyError as exc:
            raise FileNotFoundError(self._vault_set_hint()) from exc
        except Exception:
            raise

        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Vault key '{self.vault_credentials_key}' does not contain valid JSON. "
                + self._vault_set_hint()
            ) from exc
        if not isinstance(parsed, dict):
            raise ValueError(
                f"Vault key '{self.vault_credentials_key}' must resolve to a JSON object. "
                + self._vault_set_hint()
            )
        return parsed

    def _write_token(self, credentials: Credentials) -> None:
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(credentials.to_json(), encoding="utf-8")
        self.token_path.chmod(0o600)
