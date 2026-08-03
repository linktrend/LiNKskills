"""Sealed Linux certification modes: release/promoting vs local non-promoting.

Release mode (default for certification artifacts) must never fall back to the
repository-visible local HMAC key or a floating image tag. A public dev key can
forge receipts, so it must never produce a promoting ``usable`` result.

Local non-promoting mode may use the documented dev key and a floating tag for
pipeline smoke tests, but must force draft/eval_pending and must not write
sealed release evidence under ``evidence/phase10/sealed/``.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

# Documented local-only issuer material. Safe for unit tests and explicit
# non-promoting canaries. Never sufficient for catalog ``usable`` promotion.
LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY = (
    "linkskills-local-eval-runner-issuer-key-not-for-production"
)

MODE_RELEASE = "release"
MODE_LOCAL_NON_PROMOTING = "local-non-promoting"
VALID_MODES = frozenset({MODE_RELEASE, MODE_LOCAL_NON_PROMOTING})

_DIGEST_PIN_RE = re.compile(r".+@sha256:[0-9a-f]{64}$", re.IGNORECASE)
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)

SEALED_RELEASE_EVIDENCE_DIR = "evidence/phase10/sealed"
ENV_MODE = "LINKSKILLS_SEALED_CERT_MODE"
ENV_NON_PROMOTING = "LINKSKILLS_CERT_NON_PROMOTING"
ENV_IMAGE = "LINKSKILLS_SEALED_CERT_IMAGE"
ENV_IMAGE_DIGEST = "LINKSKILLS_SEALED_CERT_IMAGE_DIGEST"
ENV_ISSUER_KEY = "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"
ENV_ISSUER_ID = "LINKSKILLS_EVAL_RUNNER_ISSUER_ID"


@dataclass(frozen=True)
class SealedCertPreflight:
    """Result of fail-closed sealed-cert mode validation."""

    ok: bool
    mode: str
    errors: tuple[str, ...]
    image: str = ""
    image_digest: str = ""
    issuer_id: str = ""
    non_promoting: bool = False

    @property
    def promoting(self) -> bool:
        return self.ok and not self.non_promoting


def is_local_dev_issuer_key(key: Optional[str]) -> bool:
    """True when ``key`` is the repository-visible non-promoting HMAC material."""
    return str(key or "").strip() == LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY


def is_digest_pinned_image(image: Optional[str]) -> bool:
    """True when image reference includes an immutable ``@sha256:<64 hex>`` digest."""
    text = str(image or "").strip()
    return bool(text and _DIGEST_PIN_RE.match(text))


def extract_image_digest(image: Optional[str]) -> str:
    """Return the sha256 hex digest from a digest-pinned image reference."""
    text = str(image or "").strip()
    if not is_digest_pinned_image(text):
        return ""
    return text.rsplit("@sha256:", 1)[-1].lower()


def normalize_mode(
    raw_mode: Optional[str] = None,
    *,
    non_promoting_flag: bool = False,
    argv: Optional[Sequence[str]] = None,
) -> str:
    """Resolve sealed cert mode from env / CLI markers."""
    args = list(argv or [])
    if non_promoting_flag or "--local-non-promoting" in args:
        return MODE_LOCAL_NON_PROMOTING
    text = str(raw_mode or "").strip().lower().replace("_", "-")
    if not text:
        flag = os.environ.get(ENV_NON_PROMOTING, "").strip().lower()
        if flag in {"1", "true", "yes", "on"}:
            return MODE_LOCAL_NON_PROMOTING
        text = os.environ.get(ENV_MODE, "").strip().lower().replace("_", "-")
    if not text:
        return MODE_RELEASE
    if text in {"local", "local-non-promoting", "non-promoting", "test", "dev"}:
        return MODE_LOCAL_NON_PROMOTING
    if text in {"release", "promoting", "prod", "production"}:
        return MODE_RELEASE
    return text


def promoting_issuer_keys(
    env: Optional[Mapping[str, str]] = None,
) -> list[bytes]:
    """Trusted issuer keys that may authorize ``usable`` promotion.

    Excludes the repository-visible local dev key even when present in env.
    """
    source = env if env is not None else os.environ
    keys: list[bytes] = []
    primary = str(source.get(ENV_ISSUER_KEY, "") or "").strip()
    if primary and not is_local_dev_issuer_key(primary):
        keys.append(primary.encode("utf-8"))
    extra = str(source.get("LINKSKILLS_EVAL_RUNNER_TRUSTED_KEYS", "") or "").strip()
    if extra:
        for part in extra.split(","):
            part = part.strip()
            if part and not is_local_dev_issuer_key(part):
                keys.append(part.encode("utf-8"))
    return keys


def validate_sealed_cert_preflight(
    *,
    mode: Optional[str] = None,
    issuer_key: Optional[str] = None,
    image: Optional[str] = None,
    issuer_id: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> SealedCertPreflight:
    """Fail-closed validation before any sealed-cert mutation.

    Release mode requires an externally supplied non-dev issuer key and a
    digest-pinned image. Local non-promoting mode allows documented defaults
    but never authorizes promotion.
    """
    source = env if env is not None else os.environ
    resolved_mode = normalize_mode(mode if mode is not None else source.get(ENV_MODE))
    key = (
        issuer_key
        if issuer_key is not None
        else str(source.get(ENV_ISSUER_KEY, "") or "")
    ).strip()
    img = (
        image if image is not None else str(source.get(ENV_IMAGE, "") or "")
    ).strip()
    iid = (
        issuer_id
        if issuer_id is not None
        else str(source.get(ENV_ISSUER_ID, "") or "")
    ).strip()

    errors: list[str] = []
    if resolved_mode not in VALID_MODES:
        errors.append(
            f"unknown sealed cert mode {resolved_mode!r}; "
            f"expected one of {sorted(VALID_MODES)}"
        )
        return SealedCertPreflight(
            ok=False,
            mode=resolved_mode,
            errors=tuple(errors),
            image=img,
            issuer_id=iid,
            non_promoting=True,
        )

    if resolved_mode == MODE_LOCAL_NON_PROMOTING:
        # Documented defaults allowed; never promoting.
        if not img:
            img = "python:3.12-slim"
        if not key:
            key = LOCAL_DEV_EVAL_RUNNER_ISSUER_KEY
        if not iid:
            iid = "linkskills-eval-runner-local-non-promoting"
        digest = extract_image_digest(img)
        return SealedCertPreflight(
            ok=True,
            mode=resolved_mode,
            errors=(),
            image=img,
            image_digest=digest,
            issuer_id=iid,
            non_promoting=True,
        )

    # Release / promoting mode — fail closed before mutation.
    if not key:
        errors.append(
            f"{ENV_ISSUER_KEY} is required in release/promoting mode "
            "(no fallback; supply process-only from GSM in production)"
        )
    elif is_local_dev_issuer_key(key):
        errors.append(
            f"{ENV_ISSUER_KEY} must not be the repository-visible local dev key "
            f"in release/promoting mode"
        )
    if not img:
        errors.append(
            f"{ENV_IMAGE} is required in release/promoting mode "
            "and must be digest-pinned (name@sha256:<64 hex>)"
        )
    elif not is_digest_pinned_image(img):
        errors.append(
            f"{ENV_IMAGE} must be digest-pinned with @sha256:<64 hex>; "
            f"floating tags are forbidden in release/promoting mode (got {img!r})"
        )
    if not iid:
        iid = "linkskills-eval-runner-sealed-linux"

    digest = extract_image_digest(img)
    explicit_digest = str(source.get(ENV_IMAGE_DIGEST, "") or "").strip().lower()
    if explicit_digest:
        if not _SHA256_HEX_RE.match(explicit_digest):
            errors.append(
                f"{ENV_IMAGE_DIGEST} must be 64 lowercase/hex sha256 chars when set"
            )
        elif digest and explicit_digest != digest:
            errors.append(
                f"{ENV_IMAGE_DIGEST} does not match digest in {ENV_IMAGE}"
            )
        else:
            digest = explicit_digest

    return SealedCertPreflight(
        ok=not errors,
        mode=resolved_mode,
        errors=tuple(errors),
        image=img,
        image_digest=digest,
        issuer_id=iid,
        non_promoting=False,
    )


def non_promoting_classification(would_certify: bool) -> str:
    """Map a would-be certify outcome to a non-promoting catalog state."""
    return "eval_pending" if would_certify else "draft"
