"""Sealed Linux certification modes and hosted evaluator admission contract.

Release mode (default for certification artifacts) must never fall back to the
repository-visible local HMAC key or a floating image tag. A public dev key can
forge receipts, so it must never produce a promoting ``usable`` result.

Local non-promoting mode may use the documented dev key and a floating tag for
pipeline smoke tests, but must force draft/eval_pending and must not write
sealed release evidence under ``evidence/phase10/sealed/``.

The privileged local-Docker script is **local-workstation only**. It must never
be transferred to Server01/VPS or used with production issuer keys. A future
hosted executor is admitted only through
``validate_hosted_sealed_evaluator_contract`` (digest-pinned image, process
injected issuer material, strong isolation proof, exact source/tree identity,
bounded artifact retention, fail-closed). Passing that contract is **not** a
usable/live certification.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

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
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

SEALED_RELEASE_EVIDENCE_DIR = "evidence/phase10/sealed"
LOCAL_PRIVILEGED_SCRIPT_REL = "scripts/run-sealed-linux-certify.sh"
ENV_MODE = "LINKSKILLS_SEALED_CERT_MODE"
ENV_NON_PROMOTING = "LINKSKILLS_CERT_NON_PROMOTING"
ENV_IMAGE = "LINKSKILLS_SEALED_CERT_IMAGE"
ENV_IMAGE_DIGEST = "LINKSKILLS_SEALED_CERT_IMAGE_DIGEST"
ENV_ISSUER_KEY = "LINKSKILLS_EVAL_RUNNER_ISSUER_KEY"
ENV_ISSUER_ID = "LINKSKILLS_EVAL_RUNNER_ISSUER_ID"
ENV_EXECUTOR_KIND = "LINKSKILLS_SEALED_EXECUTOR_KIND"
ENV_SEALED_TARGET = "LINKSKILLS_SEALED_TARGET"
ENV_HOSTED_EVALUATOR = "LINKSKILLS_HOSTED_SEALED_EVALUATOR"
ENV_USE_PRODUCTION_ISSUER = "LINKSKILLS_USE_PRODUCTION_ISSUER"

EXECUTOR_KIND_LOCAL_PRIVILEGED_DOCKER = "local-privileged-docker"
EXECUTOR_KIND_HOSTED = "hosted"
VALID_EXECUTOR_KINDS = frozenset(
    {EXECUTOR_KIND_LOCAL_PRIVILEGED_DOCKER, EXECUTOR_KIND_HOSTED}
)

HOSTED_CONTRACT_SCHEMA_ID = "linkskills.hosted-sealed-evaluator/0.1.0"
ISSUER_INJECTION_PROCESS_ENV_NAME_ONLY = "process-env-name-only"
HOSTED_ISOLATION_PROOFS = frozenset(
    {"bwrap-unshare-net", "linux-network-namespace-denied"}
)
FORBIDDEN_LOCAL_SCRIPT_TARGETS = frozenset(
    {
        "server01",
        "vps",
        "production",
        "prod",
        "stage-vps",
        "shared-runtime",
    }
)
FORBIDDEN_QUALIFICATION_CLAIMS = frozenset(
    {"usable", "certified", "live", "live-usable", "production"}
)
MAX_HOSTED_ARTIFACT_BYTES = 32 * 1024 * 1024
MAX_HOSTED_ARTIFACT_AGE_HOURS = 48
HOSTED_ALLOWED_ARTIFACT_PREFIXES = (
    "evidence/end-to-end-delivery/ed-03/",
    "evidence/tmp/hosted-sealed/",
    "/tmp/linkskills-hosted-sealed/",
)


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


@dataclass(frozen=True)
class HostedSealedEvaluatorContract:
    """Fail-closed admission result for a future hosted sealed executor.

    ``ok`` means the *contract* is well-formed. It never authorizes catalog
    ``usable`` promotion, live provider/consumer claims, or Server01 Docker
    privilege.
    """

    ok: bool
    errors: tuple[str, ...]
    schema_id: str = HOSTED_CONTRACT_SCHEMA_ID
    executor_kind: str = EXECUTOR_KIND_HOSTED
    image: str = ""
    image_digest: str = ""
    source_commit: str = ""
    source_tree: str = ""
    source_tree_sha256: str = ""
    network_isolation: str = ""
    network_isolation_proof: str = ""
    issuer_injection: str = ""
    artifact_max_bytes: int = 0
    artifact_max_age_hours: int = 0
    authorizes_usable: bool = False


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


def _truthy_env(value: Optional[str]) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _normalize_target(raw: Optional[str]) -> str:
    return str(raw or "").strip().lower().replace("_", "-").replace(" ", "")


def refuse_local_privileged_docker_script(
    env: Optional[Mapping[str, str]] = None,
) -> tuple[bool, tuple[str, ...]]:
    """Return whether the local privileged Docker script may run.

    Fail closed when the caller asks for the hosted executor, Server01/VPS/
    production targets, or production issuer material. The script stays
    workstation-local.
    """
    source = env if env is not None else os.environ
    errors: list[str] = []
    kind = str(source.get(ENV_EXECUTOR_KIND, "") or "").strip().lower()
    if kind == EXECUTOR_KIND_HOSTED:
        errors.append(
            f"{ENV_EXECUTOR_KIND}=hosted is not the local privileged Docker "
            f"script ({LOCAL_PRIVILEGED_SCRIPT_REL}); hosted admission uses "
            "validate_hosted_sealed_evaluator_contract only"
        )
    if _truthy_env(source.get(ENV_HOSTED_EVALUATOR)):
        errors.append(
            f"{ENV_HOSTED_EVALUATOR} forbids {LOCAL_PRIVILEGED_SCRIPT_REL}; "
            "do not transfer this script to a hosted executor"
        )
    target = _normalize_target(source.get(ENV_SEALED_TARGET))
    if target in FORBIDDEN_LOCAL_SCRIPT_TARGETS:
        errors.append(
            f"{ENV_SEALED_TARGET}={target!r} forbids local privileged Docker; "
            "never run this script on Server01/VPS/production"
        )
    if _truthy_env(source.get(ENV_USE_PRODUCTION_ISSUER)):
        errors.append(
            f"{ENV_USE_PRODUCTION_ISSUER} forbids {LOCAL_PRIVILEGED_SCRIPT_REL}; "
            "production issuer keys must not be used with local privileged Docker"
        )
    return (not errors, tuple(errors))


def payload_is_hosted_contract_document(payload: Mapping[str, Any]) -> bool:
    """True when ``payload`` is a hosted evaluator *contract*, not receipts."""
    schema = str(payload.get("schema_id") or payload.get("schema") or "").strip()
    return schema == HOSTED_CONTRACT_SCHEMA_ID


def hosted_contract_authorizes_usable(payload: Mapping[str, Any]) -> bool:
    """Hosted contracts never authorize catalog ``usable`` (always False)."""
    del payload
    return False


def _retention_int(raw: Any, *, field: str, errors: list[str]) -> int:
    if raw is None or raw == "":
        errors.append(f"hosted contract {field} is required")
        return 0
    try:
        value = int(raw)
    except (TypeError, ValueError):
        errors.append(f"hosted contract {field} must be an integer")
        return 0
    return value


def validate_hosted_sealed_evaluator_contract(
    payload: Optional[Mapping[str, Any]] = None,
    *,
    issuer_key: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
) -> HostedSealedEvaluatorContract:
    """Admit a future hosted sealed executor only when the contract is complete.

    Fail closed. Never treats contract admission as ``usable`` certification.
    Never accepts privileged Docker, local-script transfer, floating images,
    unproven isolation, missing source/tree pins, or unbounded artifacts.
    """
    source = env if env is not None else os.environ
    data: Mapping[str, Any] = payload if payload is not None else {}
    errors: list[str] = []

    schema = str(data.get("schema_id") or data.get("schema") or "").strip()
    if schema != HOSTED_CONTRACT_SCHEMA_ID:
        errors.append(
            f"hosted contract schema_id must be {HOSTED_CONTRACT_SCHEMA_ID!r} "
            f"(got {schema!r})"
        )

    kind = str(data.get("executor_kind") or "").strip().lower()
    if kind != EXECUTOR_KIND_HOSTED:
        errors.append(
            f"hosted contract executor_kind must be {EXECUTOR_KIND_HOSTED!r} "
            f"(got {kind!r})"
        )

    if data.get("privileged_docker") is True or data.get("docker_privileged") is True:
        errors.append(
            "hosted executor must not use privileged Docker "
            "(local privileged Docker stays on the workstation script only)"
        )
    if data.get("local_script_transferred") is True:
        errors.append(
            f"{LOCAL_PRIVILEGED_SCRIPT_REL} must never be transferred to "
            "Server01/VPS or a hosted executor"
        )
    local_script = str(data.get("local_script") or "").strip()
    if local_script == LOCAL_PRIVILEGED_SCRIPT_REL:
        errors.append(
            "hosted contract must not name the local privileged Docker script "
            "as the executor"
        )

    target = _normalize_target(
        str(data.get("target") or data.get("deploy_target") or "")
    )
    if target in FORBIDDEN_LOCAL_SCRIPT_TARGETS:
        errors.append(
            f"hosted contract target {target!r} is not an admitted hosted "
            "executor identity in this issue (no Server01/VPS/production Docker)"
        )

    image = str(data.get("image") or data.get(ENV_IMAGE) or "").strip()
    if not image:
        errors.append(
            "hosted contract image is required and must be digest-pinned "
            "(name@sha256:<64 hex>)"
        )
    elif not is_digest_pinned_image(image):
        errors.append(
            "hosted contract image must be digest-pinned with @sha256:<64 hex>; "
            f"floating tags are forbidden (got {image!r})"
        )
    digest = extract_image_digest(image)
    explicit_digest = str(data.get("image_digest") or "").strip().lower()
    if explicit_digest:
        if not _SHA256_HEX_RE.match(explicit_digest):
            errors.append("hosted contract image_digest must be 64 hex chars")
        elif digest and explicit_digest != digest:
            errors.append("hosted contract image_digest does not match image pin")
        else:
            digest = explicit_digest
    if image and is_digest_pinned_image(image) and not digest:
        errors.append("hosted contract could not extract image digest")

    injection = str(data.get("issuer_injection") or "").strip()
    if injection != ISSUER_INJECTION_PROCESS_ENV_NAME_ONLY:
        errors.append(
            "hosted contract issuer_injection must be "
            f"{ISSUER_INJECTION_PROCESS_ENV_NAME_ONLY!r} "
            "(process-injected name-only env; never argv KEY=value or disk files)"
        )
    if data.get("issuer_key") or data.get("secret") or data.get("credential"):
        errors.append(
            "hosted contract must not embed issuer key, secret, or credential values"
        )
    key = (
        issuer_key
        if issuer_key is not None
        else str(source.get(ENV_ISSUER_KEY, "") or "")
    ).strip()
    if key and is_local_dev_issuer_key(key):
        errors.append(
            "hosted executor must not use the repository-visible local dev issuer key"
        )
    if _truthy_env(str(data.get("use_production_issuer") or "")) or _truthy_env(
        source.get(ENV_USE_PRODUCTION_ISSUER)
    ):
        errors.append(
            "hosted contract must not request production issuer keys in this issue"
        )

    isolation = str(data.get("network_isolation") or "").strip().lower()
    if isolation != "denied":
        errors.append(
            "hosted contract network_isolation must be 'denied' "
            f"(got {isolation!r}); unproven/allow_unproven is not admitted"
        )
    proof = str(data.get("network_isolation_proof") or "").strip().lower()
    if proof not in HOSTED_ISOLATION_PROOFS:
        errors.append(
            "hosted contract network_isolation_proof must be one of "
            f"{sorted(HOSTED_ISOLATION_PROOFS)} (got {proof!r})"
        )
    if proof in {"allow_unproven", "unproven", "macos-path-allowlist", "sandbox-exec"}:
        errors.append("hosted contract isolation proof is not a strong Linux denial")

    commit = str(data.get("source_commit") or data.get("git_sha") or "").strip().lower()
    tree = str(data.get("source_tree") or data.get("git_tree") or "").strip().lower()
    tree_sha = str(data.get("source_tree_sha256") or "").strip().lower()
    if not _GIT_SHA_RE.match(commit):
        errors.append("hosted contract source_commit must be a 40-hex git commit")
    if not _GIT_SHA_RE.match(tree):
        errors.append("hosted contract source_tree must be a 40-hex git tree")
    if not _SHA256_HEX_RE.match(tree_sha):
        errors.append("hosted contract source_tree_sha256 must be a 64-hex digest")

    retention_raw = data.get("artifact_retention")
    retention: Mapping[str, Any]
    if isinstance(retention_raw, Mapping):
        retention = retention_raw
    elif retention_raw is None:
        retention = {}
        errors.append("hosted contract artifact_retention is required")
    else:
        retention = {}
        errors.append("hosted contract artifact_retention must be an object")

    max_bytes = _retention_int(
        retention.get("max_bytes") if isinstance(retention, Mapping) else None,
        field="artifact_retention.max_bytes",
        errors=errors,
    )
    max_age = _retention_int(
        retention.get("max_age_hours") if isinstance(retention, Mapping) else None,
        field="artifact_retention.max_age_hours",
        errors=errors,
    )
    if max_bytes <= 0:
        errors.append("hosted contract artifact_retention.max_bytes must be > 0")
    elif max_bytes > MAX_HOSTED_ARTIFACT_BYTES:
        errors.append(
            "hosted contract artifact_retention.max_bytes exceeds bound "
            f"{MAX_HOSTED_ARTIFACT_BYTES}"
        )
    if max_age <= 0:
        errors.append("hosted contract artifact_retention.max_age_hours must be > 0")
    elif max_age > MAX_HOSTED_ARTIFACT_AGE_HOURS:
        errors.append(
            "hosted contract artifact_retention.max_age_hours exceeds bound "
            f"{MAX_HOSTED_ARTIFACT_AGE_HOURS}"
        )

    prefixes_raw = (
        retention.get("allowed_path_prefixes") if isinstance(retention, Mapping) else None
    )
    if not isinstance(prefixes_raw, Sequence) or isinstance(
        prefixes_raw, (str, bytes, bytearray)
    ):
        errors.append(
            "hosted contract artifact_retention.allowed_path_prefixes is required"
        )
        prefixes: tuple[str, ...] = ()
    else:
        prefixes = tuple(str(p).strip() for p in prefixes_raw if str(p).strip())
        if not prefixes:
            errors.append(
                "hosted contract artifact_retention.allowed_path_prefixes must be non-empty"
            )
        for prefix in prefixes:
            norm = prefix.replace("\\", "/")
            if ".." in norm.split("/"):
                errors.append(
                    f"hosted artifact path prefix {prefix!r} must not contain '..'"
                )
                continue
            allowed_ok = any(
                norm == allowed
                or norm.rstrip("/") == allowed.rstrip("/")
                or norm.startswith(allowed)
                or (norm + "/").startswith(allowed)
                for allowed in HOSTED_ALLOWED_ARTIFACT_PREFIXES
            )
            if not allowed_ok:
                errors.append(
                    f"hosted artifact path prefix {prefix!r} is outside the "
                    "bounded ED-03/tmp retention set"
                )
            if norm.startswith(SEALED_RELEASE_EVIDENCE_DIR) or norm.rstrip(
                "/"
            ) == SEALED_RELEASE_EVIDENCE_DIR:
                errors.append(
                    "hosted executor must not write local sealed release evidence "
                    f"under {SEALED_RELEASE_EVIDENCE_DIR}"
                )

    claim = str(
        data.get("qualification_claim") or data.get("certification_claim") or ""
    ).strip().lower()
    if claim in FORBIDDEN_QUALIFICATION_CLAIMS:
        errors.append(
            "hosted contract must not claim usable/live/certified qualification "
            f"(got {claim!r}); contract admission is not certification"
        )
    if data.get("authorizes_usable") is True or data.get("usable") is True:
        errors.append(
            "hosted contract authorizes_usable must remain false; "
            "do not fabricate usable certification"
        )

    return HostedSealedEvaluatorContract(
        ok=not errors,
        errors=tuple(errors),
        schema_id=schema or HOSTED_CONTRACT_SCHEMA_ID,
        executor_kind=kind or EXECUTOR_KIND_HOSTED,
        image=image,
        image_digest=digest,
        source_commit=commit,
        source_tree=tree,
        source_tree_sha256=tree_sha,
        network_isolation=isolation,
        network_isolation_proof=proof,
        issuer_injection=injection,
        artifact_max_bytes=max_bytes,
        artifact_max_age_hours=max_age,
        authorizes_usable=False,
    )
