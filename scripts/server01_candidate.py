#!/usr/bin/env python3
"""Validate the Skills-owned Server 01 v2 deployment candidate pack.

The pack lives under ``docs/integrations/server01/``. It never mutates live
compose, never deploys, and never treats an unbuilt image placeholder as a
hosted digest. Hosted ``linux/amd64`` publication remains HOLD until an
independent build records a digest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

PACK_REL = Path("docs/integrations/server01")
CANDIDATE_REL = PACK_REL / "CANDIDATE.json"
OVERLAY_REL = PACK_REL / "compose.overlay.yml"
DOCKERFILE_REL = PACK_REL / "Dockerfile.candidate"
HANDOFF_REL = PACK_REL / "HANDOFF.md"
ROLLBACK_REL = PACK_REL / "ROLLBACK.md"
LIVE_COMPOSE = "/srv/linktrend/deploy/compose/core-services.compose.yml"
PREVIOUS_IMAGE = (
    "sha256:7cf2780a82c2c37c113b2d55b787a4e72a7098063cf434ea0654826c3719257f"
)
PREVIOUS_COMMIT = "7067716fef5189a1427a7cf9b0847cec898e19de"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
SECRETISH_RE = re.compile(
    r"(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|postgres(ql)?://\S+:\S+@|ghp_[A-Za-z0-9]{20,})",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(r"^REPLACE_WITH_[A-Z0-9_]+$")
MUTATING_ACTIONS = frozenset(
    {"deploy", "apply", "push-image", "compose-up", "ssh-host", "mutate-live"}
)


class Server01CandidateError(ValueError):
    """A deterministic Server 01 candidate validation failure."""


def repo_root() -> Path:
    """Return the repository root that contains this script."""
    return Path(__file__).resolve().parents[1]


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def read_source_identity(root: Path) -> dict[str, str]:
    """Bind the candidate to the exact checked-out commit and tree."""
    commit = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    branch = _git(root, "branch", "--show-current")
    origin = _git(root, "remote", "get-url", "origin")
    origin = re.sub(r"https://[^@]+@", "https://", origin)
    if not SHA40_RE.fullmatch(commit) or not SHA40_RE.fullmatch(tree):
        raise Server01CandidateError("source_identity_unbound")
    return {
        "repository": "linktrend/LiNKskills",
        "origin": origin,
        "branch": branch,
        "commit": commit,
        "tree": tree,
    }


def load_candidate(root: Path) -> dict[str, Any]:
    """Load and type-check the canonical candidate JSON."""
    path = root / CANDIDATE_REL
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Server01CandidateError(f"candidate_json_invalid:{exc}") from exc
    if not isinstance(data, dict):
        raise Server01CandidateError("candidate_json_not_object")
    return data


def _require_text(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise Server01CandidateError(f"missing_text:{key}")
    return value


def _scan_secrets(text: str, label: str) -> None:
    if SECRETISH_RE.search(text):
        raise Server01CandidateError(f"secret_material_forbidden:{label}")


def _overlay_text(root: Path) -> str:
    return (root / OVERLAY_REL).read_text(encoding="utf-8")


def validate_candidate_document(data: Mapping[str, Any]) -> None:
    """Fail closed when the canonical JSON is not a non-live v2 candidate."""
    if data.get("kind") != "linkskills-server01-candidate":
        raise Server01CandidateError("kind_mismatch")
    if data.get("packet") != "ED-06":
        raise Server01CandidateError("packet_mismatch")
    if data.get("issue") != 328:
        raise Server01CandidateError("issue_mismatch")
    if data.get("status") != "CANDIDATE_NOT_DEPLOYED":
        raise Server01CandidateError("status_must_remain_not_deployed")
    if data.get("liveMutation") is not False:
        raise Server01CandidateError("live_mutation_must_be_false")
    hosted = data.get("hostedImageBuild")
    if not isinstance(hosted, dict) or hosted.get("status") != "HOLD":
        raise Server01CandidateError("hosted_image_must_remain_hold_until_digest")
    if hosted.get("architecture") != "linux/amd64":
        raise Server01CandidateError("architecture_must_be_linux_amd64")
    if hosted.get("runtimeUser") != "10002:10002":
        raise Server01CandidateError("runtime_user_must_be_10002")
    if hosted.get("candidateImage") != "HOLD_REPLACE_WITH_HOSTED_LINUX_AMD64_DIGEST":
        raise Server01CandidateError("candidate_image_placeholder_required")
    previous = data.get("previousState")
    if not isinstance(previous, dict):
        raise Server01CandidateError("previous_state_missing")
    if previous.get("imageDigest") != PREVIOUS_IMAGE:
        raise Server01CandidateError("previous_image_must_be_retained")
    if previous.get("releaseCommit") != PREVIOUS_COMMIT:
        raise Server01CandidateError("previous_release_must_be_retained")
    if previous.get("composePath") != LIVE_COMPOSE:
        raise Server01CandidateError("live_compose_path_must_be_named_not_edited")
    if previous.get("contract") != "skills.api.v0.1":
        raise Server01CandidateError("previous_contract_must_remain_v0_1")
    candidate = data.get("candidate")
    if not isinstance(candidate, dict):
        raise Server01CandidateError("candidate_block_missing")
    if candidate.get("contract") != "skills.api.v0.2":
        raise Server01CandidateError("candidate_contract_must_be_v0_2")
    if candidate.get("httpEntrypoint") != "linkskills-gateway":
        raise Server01CandidateError("http_entrypoint_mismatch")
    if candidate.get("mcpEntrypoint") != "linkskills-mcp-v2":
        raise Server01CandidateError("mcp_entrypoint_mismatch")
    if candidate.get("bind") != "127.0.0.1:18798":
        raise Server01CandidateError("bind_must_remain_loopback")
    if candidate.get("store") != "postgres" or candidate.get("storeProbe") is not True:
        raise Server01CandidateError("production_store_probe_required")
    health = candidate.get("healthPaths")
    if not isinstance(health, list) or not {"/health", "/ready", "/metrics", "/drain"}.issubset(health):
        raise Server01CandidateError("health_ready_metrics_drain_required")
    hardening = data.get("hardening")
    if not isinstance(hardening, dict):
        raise Server01CandidateError("hardening_missing")
    if hardening.get("user") != "10002:10002":
        raise Server01CandidateError("non_root_user_required")
    if hardening.get("readOnlyRoot") is not True:
        raise Server01CandidateError("read_only_root_required")
    if hardening.get("capDrop") != ["ALL"]:
        raise Server01CandidateError("cap_drop_all_required")
    if hardening.get("noNewPrivileges") is not True:
        raise Server01CandidateError("no_new_privileges_required")
    if hardening.get("pidsLimit") != 256:
        raise Server01CandidateError("pids_limit_required")


def validate_overlay(text: str, data: Mapping[str, Any]) -> None:
    """Require the compose overlay to stay a sanitized, non-live proposal."""
    _scan_secrets(text, "compose.overlay.yml")
    if LIVE_COMPOSE in text:
        raise Server01CandidateError("overlay_must_not_embed_live_compose_path")
    required = (
        'user: "10002:10002"',
        "read_only: true",
        "no-new-privileges:true",
        "cap_drop:",
        "- ALL",
        "platform: linux/amd64",
        "127.0.0.1:18798:8787",
        "linkskills-gateway",
        "LINKSKILLS_GATEWAY_STORE: postgres",
        "LINKSKILLS_STORE_PROBE: \"1\"",
        "org.linktrend.contract: skills.api.v0.2",
        "image: REPLACE_WITH_HOSTED_LINUX_AMD64_DIGEST",
        "name: REPLACE_WITH_PLATFORM_READBACK_NETWORK",
        "external: true",
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise Server01CandidateError(f"overlay_missing:{missing[0]}")
    if "0.0.0.0:" in text.split("ports:", 1)[-1].split("tmpfs:", 1)[0]:
        raise Server01CandidateError("public_publish_forbidden")
    if PREVIOUS_IMAGE in text:
        raise Server01CandidateError("candidate_overlay_must_not_reuse_previous_digest")
    if "user: \"0:" in text or "user: \"root\"" in text:
        raise Server01CandidateError("root_user_forbidden")
    image_line = next(
        (line.strip() for line in text.splitlines() if line.strip().startswith("image:")),
        "",
    )
    image_value = image_line.split(":", 1)[1].strip()
    if DIGEST_RE.fullmatch(image_value) or image_value.endswith(PREVIOUS_IMAGE):
        raise Server01CandidateError("overlay_digest_must_wait_for_hosted_build")
    if not PLACEHOLDER_RE.fullmatch(image_value):
        raise Server01CandidateError("overlay_image_must_be_placeholder")
    previous = data["previousState"]
    if previous["imageDigest"] == image_value:
        raise Server01CandidateError("cannot_cutover_to_previous_digest")


def validate_dockerfile(text: str) -> None:
    """Require a non-root linux Python image definition without secrets."""
    _scan_secrets(text, "Dockerfile.candidate")
    required = (
        "FROM python:3.11-slim-bookworm",
        "useradd --uid 10002",
        "USER 10002:10002",
        "--require-hashes -r requirements-dev.lock",
        'ENTRYPOINT ["linkskills-gateway"]',
        "org.linktrend.contract=\"skills.api.v0.2\"",
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise Server01CandidateError(f"dockerfile_missing:{missing[0]}")
    if re.search(r"^USER\s+0\b", text, re.MULTILINE):
        raise Server01CandidateError("dockerfile_root_user_forbidden")


def validate_docs(root: Path) -> None:
    """Require handoff and rollback to name HOLDs and the retained image."""
    handoff = (root / HANDOFF_REL).read_text(encoding="utf-8")
    rollback = (root / ROLLBACK_REL).read_text(encoding="utf-8")
    for label, text in (("HANDOFF.md", handoff), ("ROLLBACK.md", rollback)):
        _scan_secrets(text, label)
        if PREVIOUS_IMAGE not in text:
            raise Server01CandidateError(f"docs_must_retain_previous_image:{label}")
        if LIVE_COMPOSE not in text and label == "HANDOFF.md":
            raise Server01CandidateError("handoff_must_name_live_compose_as_untouched")
    if "CANDIDATE_NOT_DEPLOYED" not in handoff:
        raise Server01CandidateError("handoff_must_keep_not_deployed_status")
    if "HOLD" not in handoff:
        raise Server01CandidateError("handoff_must_record_hosted_digest_hold")
    if "drain" not in rollback.lower():
        raise Server01CandidateError("rollback_must_drain")


def validate_pack(root: Path | None = None) -> dict[str, Any]:
    """Validate the Server 01 candidate pack against the checked-out identity.

    Returns:
        A JSON-serialisable receipt. ``status`` is ``PASS`` only when the pack
        is a non-live, non-secret v2 candidate that retains the previous image.

    Raises:
        Server01CandidateError: when the pack is incomplete or would imply
            live mutation, a public listener, secrets, or a fake image digest.
    """
    base = repo_root() if root is None else Path(root)
    for rel in (CANDIDATE_REL, OVERLAY_REL, DOCKERFILE_REL, HANDOFF_REL, ROLLBACK_REL):
        if not (base / rel).is_file():
            raise Server01CandidateError(f"missing_pack_file:{rel.as_posix()}")
    data = load_candidate(base)
    blob = json.dumps(data, sort_keys=True, separators=(",", ":"))
    _scan_secrets(blob, "CANDIDATE.json")
    validate_candidate_document(data)
    overlay = _overlay_text(base)
    validate_overlay(overlay, data)
    validate_dockerfile((base / DOCKERFILE_REL).read_text(encoding="utf-8"))
    validate_docs(base)
    identity = read_source_identity(base)
    overlay_digest = "sha256:" + hashlib.sha256(overlay.encode("utf-8")).hexdigest()
    return {
        "status": "PASS",
        "packet": "ED-06",
        "issue": 328,
        "liveMutation": False,
        "hostedImageBuild": "HOLD",
        "sourceIdentity": identity,
        "previousImage": PREVIOUS_IMAGE,
        "overlayDigest": overlay_digest,
        "contract": "skills.api.v0.2",
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint. Only ``validate`` is permitted."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        nargs="?",
        default="validate",
        help="Only 'validate' is accepted. Deploy/apply actions fail closed.",
    )
    parser.add_argument(
        "--root",
        default=str(repo_root()),
        help="Repository root (defaults to the checkout that contains this script).",
    )
    args = parser.parse_args(argv)
    if args.action in MUTATING_ACTIONS:
        print(
            json.dumps(
                {
                    "status": "HOLD",
                    "error": f"live_action_forbidden:{args.action}",
                },
                sort_keys=True,
            )
        )
        return 2
    if args.action != "validate":
        print(json.dumps({"status": "HOLD", "error": f"unknown_action:{args.action}"}))
        return 2
    try:
        receipt = validate_pack(Path(args.root))
    except Server01CandidateError as exc:
        print(json.dumps({"status": "HOLD", "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(receipt, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
