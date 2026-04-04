from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

from .config import Settings
from .types import DisclosureTokenClaims


class TokenError(RuntimeError):
    """Token issuance/validation error."""


class SecretResolutionError(RuntimeError):
    """Secret provider resolution error."""


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(raw: str) -> bytes:
    pad = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(raw + pad)


def _sign(message: bytes, secret: str) -> str:
    sig = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return _b64url_encode(sig)


def hash_api_key(raw_key: str) -> str:
    # Use a slow KDF for API-key fingerprinting so leaked digests are harder to brute-force.
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        raw_key.encode("utf-8"),
        b"logic-engine-api-key",
        600_000,
    )
    return digest.hex()


def hash_payload(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise SecretResolutionError(f"Secret file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SecretResolutionError(f"Failed to parse secret file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SecretResolutionError(f"Secret file root must be an object: {path}")
    return data


def _resolve_env_secret(settings: Settings) -> str:
    value = os.getenv(settings.token_secret_env_key)
    if value:
        return value
    raise SecretResolutionError(f"Missing environment secret key: {settings.token_secret_env_key}")


def _resolve_gsm_secret(settings: Settings) -> str:
    payload = _read_json(settings.gsm_secret_file)
    token = payload.get("token_secret")
    if not isinstance(token, str) or not token.strip():
        raise SecretResolutionError("GSM secret file missing token_secret")
    return token.strip()


def _resolve_gsm_named_secret(settings: Settings, secret_name: str) -> str:
    if settings.gcp_project_id:
        try:
            from google.cloud import secretmanager
        except Exception as exc:
            raise SecretResolutionError(
                "google-cloud-secret-manager is required for GSM secret resolution"
            ) from exc

        client = secretmanager.SecretManagerServiceClient()
        resource = f"projects/{settings.gcp_project_id}/secrets/{secret_name}/versions/latest"
        version = client.access_secret_version(request={"name": resource})
        payload = version.payload.data.decode("utf-8").strip() if version.payload and version.payload.data else ""
        if not payload:
            raise SecretResolutionError(f"GSM secret '{secret_name}' is empty")
        return payload

    # File-based fallback payload supports named values for local/dev replay.
    payload = _read_json(settings.gsm_secret_file)
    value = payload.get(secret_name)
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise SecretResolutionError(f"GSM secret '{secret_name}' could not be resolved")


def resolve_token_secret(settings: Settings) -> str:
    """
    Production contract: GSM is required and fail-closed.
    Non-prod: provider preference is honored, with optional fallback when enabled.
    """

    if settings.is_production:
        return _resolve_gsm_secret(settings)

    provider = settings.secret_provider
    if provider == "gsm":
        try:
            return _resolve_gsm_secret(settings)
        except SecretResolutionError:
            if not settings.allow_nonprod_secret_fallback:
                raise
            return _resolve_env_secret(settings)

    try:
        return _resolve_env_secret(settings)
    except SecretResolutionError:
        if settings.allow_nonprod_secret_fallback:
            return _resolve_gsm_secret(settings)
        raise


def resolve_named_secret(settings: Settings, secret_name: str) -> str:
    if settings.is_production:
        return _resolve_gsm_named_secret(settings, secret_name)

    provider = settings.secret_provider
    if provider == "gsm":
        try:
            return _resolve_gsm_named_secret(settings, secret_name)
        except SecretResolutionError:
            if not settings.allow_nonprod_secret_fallback:
                raise
            value = os.getenv(secret_name)
            if value:
                return value
            raise

    value = os.getenv(secret_name)
    if value:
        return value
    if settings.allow_nonprod_secret_fallback:
        return _resolve_gsm_named_secret(settings, secret_name)
    raise SecretResolutionError(f"Missing secret '{secret_name}'")


def issue_disclosure_token(
    *,
    secret: str,
    tenant_id: str,
    run_id: str,
    capability_id: str,
    version: str,
    step_scope: str,
    ttl_seconds: int,
) -> Tuple[str, DisclosureTokenClaims]:
    now = datetime.now(timezone.utc)
    exp = int((now + timedelta(seconds=ttl_seconds)).timestamp())
    claims = DisclosureTokenClaims(
        tenant_id=tenant_id,
        run_id=run_id,
        capability_id=capability_id,
        version=version,
        step_scope=step_scope,
        mode="MANAGED",
        exp=exp,
        jti=uuid.uuid4().hex,
    )

    header = {"alg": "HS256", "typ": "JWT"}
    header_part = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _b64url_encode(json.dumps(claims.model_dump(), separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_part}.{payload_part}".encode("utf-8")
    signature = _sign(signing_input, secret)
    token = f"{header_part}.{payload_part}.{signature}"
    return token, claims


def validate_disclosure_token(token: str, secret: str, now_ts: int | None = None) -> DisclosureTokenClaims:
    try:
        header_part, payload_part, signature = token.split(".")
    except ValueError as exc:
        raise TokenError("Invalid token format") from exc

    signing_input = f"{header_part}.{payload_part}".encode("utf-8")
    expected = _sign(signing_input, secret)
    if not hmac.compare_digest(expected, signature):
        raise TokenError("Invalid token signature")

    try:
        payload: Dict[str, object] = json.loads(_b64url_decode(payload_part).decode("utf-8"))
    except Exception as exc:
        raise TokenError("Invalid token payload") from exc

    claims = DisclosureTokenClaims(**payload)
    timestamp = now_ts if now_ts is not None else int(datetime.now(timezone.utc).timestamp())
    if claims.exp < timestamp:
        raise TokenError("Token expired")
    return claims
