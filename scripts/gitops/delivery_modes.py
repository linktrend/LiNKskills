#!/usr/bin/env python3
"""Configurable delivery modes: issue-pr compatibility and Phase integration.

Pure helpers for Packager discover and Phase fixtures. Checkpoint pushes never
open PRs. Risk-class Issue PR exceptions are explicit under phase-integration.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

MODE_ISSUE_PR = "issue-pr"
MODE_PHASE_INTEGRATION = "phase-integration"
DEFAULT_DELIVERY_MODE = MODE_ISSUE_PR
RECOMMENDED_V2_DELIVERY_MODE = MODE_PHASE_INTEGRATION
DEFAULT_PHASE_PREFIX = "phase/"

CONFIG_REL = Path(".github/linktrend-delivery-mode.json")
EXCEPTION_REL = Path(".linktrend/issue-pr-exception.json")
PHASE_DELIVERY_REL = Path(".linktrend/phase-delivery-record.json")

ISSUE_PR_RISK_CLASSES = frozenset(
    {
        "security",
        "authentication",
        "database_migration",
        "infrastructure",
        "major_shared_api",
        "unusually_large_scope",
        "cross_phase_impact",
    }
)

NAMED_GATES = frozenset({"fast-gate", "staging-gate", "release-gate"})
PHASE_IDENTITY_PATHS = frozenset({PHASE_DELIVERY_REL.as_posix()})
REUSED_PHASE_IDENTITY_KEYS = (
    "headSha",
    "gitTree",
    "baseSha",
    "immutableBaseSha",
    "acceptedIssues",
    "acceptedCommits",
    "dependencyOrder",
    "candidateRevision",
    "sealed",
    "mergeSha",
    "sealRevision",
    "sealedSha",
    "candidateIdentity",
    "candidateId",
    "namedGateEvidence",
    "fast",
    "full",
)

_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
_ZERO_SHA_RE = re.compile(r"^0{40}$")

# Test hook: (repo_root, branch, sha) -> exception dict | None
_EXCEPTION_HOOK: Callable[[Path | None, str, str], dict[str, Any] | None] | None = None


@dataclass(frozen=True)
class DeliveryConfig:
    delivery_mode: str = DEFAULT_DELIVERY_MODE
    phase_branch_prefix: str = DEFAULT_PHASE_PREFIX

    @property
    def is_phase_integration(self) -> bool:
        return self.delivery_mode == MODE_PHASE_INTEGRATION


@dataclass(frozen=True)
class PrOpenDecision:
    open_pr: bool
    reason: str
    risk_class: str | None = None


def recommended_v2_delivery_config() -> DeliveryConfig:
    """Return the recommended new-install profile without changing v1 behavior.

    Version-1/no-config consumers remain ``issue-pr``.  Installers creating a
    complete v2 policy should use this profile unless the consumer explicitly
    selects ``issue-pr``.
    """

    return DeliveryConfig(delivery_mode=RECOMMENDED_V2_DELIVERY_MODE)


def effective_delivery_mode(config: DeliveryConfig, *, explicit_mode: str | None = None) -> str:
    """Resolve a new-install recommendation while preserving explicit choice."""

    selected = (explicit_mode or config.delivery_mode or "").strip()
    if selected == MODE_ISSUE_PR:
        return MODE_ISSUE_PR
    if selected == MODE_PHASE_INTEGRATION:
        return MODE_PHASE_INTEGRATION
    return RECOMMENDED_V2_DELIVERY_MODE


def normalize_sha(value: str | None) -> str:
    return (value or "").strip().lower()


def is_valid_sha(value: str | None) -> bool:
    sha = normalize_sha(value)
    return bool(_SHA40_RE.fullmatch(sha)) and not bool(_ZERO_SHA_RE.fullmatch(sha))


def checkpoint_opens_pr() -> bool:
    """Checkpoints never create PRs (either delivery mode)."""
    return False


def is_phase_branch(name: str, prefix: str = DEFAULT_PHASE_PREFIX) -> bool:
    p = prefix if prefix.endswith("/") else f"{prefix}/"
    return bool(name) and name.startswith(p)


def is_issue_branch(name: str) -> bool:
    return bool(name) and name.startswith("issue/")


def git_first_parent_sha(repo: str | Path, sha: str) -> str:
    """Return the only parent of a commit, or empty when the object is not a single-parent tip."""

    subject = normalize_sha(sha)
    if not is_valid_sha(subject):
        return ""
    result = subprocess.run(
        ["git", "rev-list", "--parents", "-n", "1", subject],
        cwd=Path(repo),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        return ""
    parts = (result.stdout or "").strip().split()
    if len(parts) != 2:
        return ""
    parent = normalize_sha(parts[1])
    return parent if is_valid_sha(parent) else ""


def git_commit_paths(repo: str | Path, sha: str) -> set[str]:
    """Return the path set changed by one commit."""

    subject = normalize_sha(sha)
    if not is_valid_sha(subject):
        return set()
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "-r", "--name-only", subject],
        cwd=Path(repo),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        return set()
    return {line.strip() for line in (result.stdout or "").splitlines() if line.strip()}


def is_phase_identity_commit(repo: str | Path, sha: str) -> bool:
    """True when ``sha`` is a single-parent commit that only binds the Phase record path."""

    if not git_first_parent_sha(repo, sha):
        return False
    paths = git_commit_paths(repo, sha)
    return bool(paths) and paths <= PHASE_IDENTITY_PATHS


def git_is_ancestor(repo: str | Path, ancestor_sha: str, descendant_sha: str) -> bool:
    """Prove exact Git ancestry without relying on branch names or PR metadata."""

    if not is_valid_sha(ancestor_sha) or not is_valid_sha(descendant_sha):
        return False
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", normalize_sha(ancestor_sha), normalize_sha(descendant_sha)],
        cwd=Path(repo),
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def bind_phase_identity_fields(
    record: Mapping[str, Any],
    *,
    assembled_sha: str,
    tip_sha: str,
) -> tuple[bool, str]:
    """Bind sealed/merge/gate fields to the assembled package vs identity-binding tip."""

    recorded = normalize_sha(str(record.get("headSha") or ""))
    assembled = normalize_sha(assembled_sha)
    tip = normalize_sha(tip_sha)
    if not is_valid_sha(recorded) or not is_valid_sha(assembled) or not is_valid_sha(tip):
        return False, "phase_delivery_head_sha_invalid"
    if recorded != assembled:
        return False, "phase_delivery_head_sha_mismatch"
    if recorded == tip:
        return False, "phase_delivery_self_referential_head"
    tree = normalize_sha(str(record.get("gitTree") or ""))
    if tree and tree == tip:
        return False, "phase_delivery_self_referential_tree"
    gate = record.get("namedGateEvidence") if isinstance(record.get("namedGateEvidence"), Mapping) else None
    if gate is not None:
        gate_sha = normalize_sha(str(gate.get("sha") or ""))
        if is_valid_sha(gate_sha) and gate_sha != assembled:
            return False, "phase_delivery_gate_sha_not_assembled"
        if gate_sha == tip:
            return False, "phase_delivery_gate_sha_self_referential"
    merge = record.get("mergeSha")
    if merge not in (None, "", False):
        merged = normalize_sha(str(merge))
        if not is_valid_sha(merged):
            return False, "phase_delivery_merge_sha_invalid"
        if merged in {assembled, tip}:
            return False, "phase_delivery_merge_sha_identity_collision"
    if bool(record.get("sealed")):
        sealed_sha = normalize_sha(str(record.get("sealedSha") or ""))
        if sealed_sha != tip:
            return False, "phase_delivery_sealed_sha_not_tip"
        identity = record.get("candidateIdentity") if isinstance(record.get("candidateIdentity"), Mapping) else None
        if identity is not None:
            source = normalize_sha(str(identity.get("sourceSha") or ""))
            if source != tip:
                return False, "phase_delivery_candidate_source_not_tip"
    else:
        sealed_sha = record.get("sealedSha")
        if sealed_sha not in (None, "", False) and is_valid_sha(str(sealed_sha)):
            return False, "phase_delivery_unsealed_sealed_sha"
        identity = record.get("candidateIdentity")
        if identity not in (None, "", False, {}):
            return False, "phase_delivery_unsealed_candidate_identity"
    return True, "identity_bound"


def committed_record_matches_expected(committed: Mapping[str, Any], expected: Mapping[str, Any]) -> tuple[bool, str]:
    """Reject forged extra-field overlays that would reuse sealed/merge/gate identity."""

    for key in REUSED_PHASE_IDENTITY_KEYS:
        if expected.get(key) != committed.get(key):
            return False, f"phase_record_identity_mismatch:{key}"
    return True, "ok"


def validate_risk_class(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = str(value).strip()
    if cleaned in ISSUE_PR_RISK_CLASSES:
        return cleaned
    return None


def parse_issue_pr_exception(payload: dict[str, Any] | None) -> tuple[str | None, str]:
    """Return (risk_class, detail). Invalid payloads fail closed (no exception)."""
    if not isinstance(payload, dict):
        return None, "exception_missing"
    if payload.get("schemaVersion") != 1:
        return None, "exception_schema_invalid"
    risk = validate_risk_class(payload.get("riskClass"))
    if not risk:
        return None, "exception_risk_class_invalid"
    return risk, "ok"


def load_delivery_config(
    repo_root: Path | None = None,
    *,
    env: dict[str, str] | None = None,
) -> DeliveryConfig:
    """Resolve and strictly validate v1/v2 delivery configuration."""
    from coordinator.config import load_delivery_config as load_runtime_config

    return load_runtime_config(repo_root, env=env)  # type: ignore[return-value]


def should_open_pr_for_branch(
    branch: str,
    config: DeliveryConfig,
    *,
    risk_class: str | None = None,
    review_ready: bool = True,
) -> PrOpenDecision:
    """Decide whether Packager discover may open/ensure a development draft PR.

    Checkpoints (review_ready=False) never open PRs.
    """
    if not review_ready:
        return PrOpenDecision(False, "skipped_not_ready")
    if checkpoint_opens_pr():
        return PrOpenDecision(False, "checkpoint_never_opens_pr")

    if not config.is_phase_integration:
        return PrOpenDecision(True, "issue_pr_mode")

    if is_phase_branch(branch, config.phase_branch_prefix):
        return PrOpenDecision(True, "phase_branch_pr")

    if is_issue_branch(branch):
        risk = validate_risk_class(risk_class)
        if risk:
            return PrOpenDecision(True, "issue_pr_risk_exception", risk_class=risk)
        return PrOpenDecision(False, "skipped_phase_mode_issue_without_exception")

    # Legacy allowlisted work branches under phase mode: treat like Issue (no PR)
    # unless they are the Phase branch (already handled).
    return PrOpenDecision(False, "skipped_phase_mode_non_phase_branch")


def load_exception_for_tip(
    *,
    repo_root: Path | None,
    branch: str,
    sha: str,
    payload: dict[str, Any] | None = None,
) -> tuple[str | None, str]:
    """Resolve Issue PR risk exception for a tip SHA."""
    if _EXCEPTION_HOOK is not None:
        hooked = _EXCEPTION_HOOK(repo_root, branch, sha)
        return parse_issue_pr_exception(hooked)
    if payload is not None:
        return parse_issue_pr_exception(payload)
    if repo_root is None:
        return None, "exception_unavailable"
    path = Path(repo_root) / EXCEPTION_REL
    if not path.is_file():
        return None, "exception_missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "exception_unreadable"
    return parse_issue_pr_exception(data)


def named_gate_evidence(
    *,
    gate: str,
    sha: str | None,
    checks: list[dict[str, Any]],
    required: list[str],
    expected_sha: str | None = None,
    stale_event: bool = False,
    allow_neutral: bool = False,
) -> dict[str, Any]:
    """Build fail-closed named-gate evidence for an exact SHA.

    Import of packager_logic.fast_gate_status is local to avoid cycles at import.
    """
    from packager_logic import fast_gate_status, latest_checks_by_name

    gate_id = (gate or "").strip()
    if gate_id not in NAMED_GATES:
        return {
            "gate": gate_id or "unknown",
            "sha": normalize_sha(sha),
            "status": "failed",
            "detail": "unknown_gate_id",
            "checks": [],
        }

    subject = normalize_sha(sha)
    if not subject or _ZERO_SHA_RE.fullmatch(subject) or not is_valid_sha(subject):
        return {
            "gate": gate_id,
            "sha": subject,
            "status": "failed",
            "detail": "invalid_or_zero_sha",
            "checks": [],
        }

    if expected_sha is not None:
        exp = normalize_sha(expected_sha)
        if not is_valid_sha(exp):
            return {
                "gate": gate_id,
                "sha": subject,
                "status": "failed",
                "detail": "expected_sha_invalid",
                "checks": [],
            }
        if exp != subject:
            return {
                "gate": gate_id,
                "sha": subject,
                "status": "failed",
                "detail": f"wrong_sha:expected={exp}",
                "checks": [],
            }

    if stale_event:
        return {
            "gate": gate_id,
            "sha": subject,
            "status": "failed",
            "detail": "stale_event_head",
            "checks": [],
        }

    # Neutral/skipped conclusions are non-success unless allow_neutral is set.
    # When allow_neutral is True, NEUTRAL/SKIPPED/SKIP count as success; all other
    # non-success conclusions (FAILURE, CANCELLED, …) remain fail-closed.
    # Do not delegate to fast_gate_status when allow_neutral is set — that helper
    # treats any non-SUCCESS conclusion as failed.
    latest = latest_checks_by_name(checks)
    req = [r.strip() for r in required if r.strip()]
    check_rows = [{"name": n, "state": latest.get(n, "MISSING")} for n in req]
    if not req:
        return {
            "gate": gate_id,
            "sha": subject,
            "status": "failed",
            "detail": "REQUIRED_CHECKS empty",
            "checks": check_rows,
        }

    neutral_ok = frozenset({"NEUTRAL", "SKIPPED", "SKIP"}) if allow_neutral else frozenset()
    if not allow_neutral:
        for name in req:
            state = latest.get(name, "MISSING")
            if state in {"NEUTRAL", "SKIPPED", "SKIP", "CANCELLED", "ACTION_REQUIRED"}:
                return {
                    "gate": gate_id,
                    "sha": subject,
                    "status": "failed",
                    "detail": f"{name}={state}",
                    "checks": check_rows,
                }
        status, detail = fast_gate_status(checks, required)
        return {
            "gate": gate_id,
            "sha": subject,
            "status": status,
            "detail": detail,
            "checks": check_rows,
        }

    for name in req:
        state = latest.get(name, "MISSING")
        if state in {"PENDING", "QUEUED", "IN_PROGRESS", "EXPECTED"}:
            return {
                "gate": gate_id,
                "sha": subject,
                "status": "pending",
                "detail": f"{name}={state}",
                "checks": check_rows,
            }
        if state in {"MISSING", ""}:
            return {
                "gate": gate_id,
                "sha": subject,
                "status": "missing",
                "detail": f"{name}=missing",
                "checks": check_rows,
            }
        if state == "SUCCESS" or state in neutral_ok:
            continue
        return {
            "gate": gate_id,
            "sha": subject,
            "status": "failed",
            "detail": f"{name}={state}",
            "checks": check_rows,
        }
    return {
        "gate": gate_id,
        "sha": subject,
        "status": "success",
        "detail": "all required success",
        "checks": check_rows,
    }


def build_phase_delivery_record(
    *,
    phase_branch: str,
    base_sha: str,
    head_sha: str,
    accepted_issues: list[dict[str, Any]],
    named_gate: dict[str, Any],
    merge_sha: str | None = None,
    phase_pr: dict[str, Any] | None = None,
    risk_exception_issue_prs: list[dict[str, Any]] | None = None,
    phase_id: str | None = None,
    immutable_base_sha: str | None = None,
    seal_revision: int | None = None,
    sealed_sha: str | None = None,
    candidate_identity: dict[str, Any] | None = None,
    gate_results: dict[str, Any] | None = None,
    stop_reason: str | None = None,
) -> dict[str, Any]:
    """Assemble a machine-readable Phase delivery record."""
    if not is_valid_sha(base_sha) or not is_valid_sha(head_sha):
        raise ValueError("base_sha and head_sha must be non-zero 40-hex SHAs")
    if merge_sha is not None and not is_valid_sha(merge_sha):
        raise ValueError("merge_sha must be null or a non-zero 40-hex SHA")
    if len(accepted_issues) < 1:
        raise ValueError("accepted_issues must be non-empty")

    record: dict[str, Any] = {
        "schemaVersion": 1,
        "deliveryMode": MODE_PHASE_INTEGRATION,
        "phaseBranch": phase_branch,
        "baseSha": normalize_sha(base_sha),
        "headSha": normalize_sha(head_sha),
        "mergeSha": normalize_sha(merge_sha) if merge_sha else None,
        "acceptedIssues": accepted_issues,
        "namedGateEvidence": named_gate,
    }
    if phase_pr is not None:
        record["phasePr"] = phase_pr
    if risk_exception_issue_prs:
        record["riskExceptionIssuePrs"] = risk_exception_issue_prs
    # W2 lifecycle fields are optional so the W1 delivery-record shape remains
    # readable.  The Integrator supplies them for Phase records it owns.
    if phase_id is not None:
        record["phaseId"] = phase_id
    if immutable_base_sha is not None:
        if not is_valid_sha(immutable_base_sha):
            raise ValueError("immutable_base_sha must be a non-zero 40-hex SHA")
        record["immutableBaseSha"] = normalize_sha(immutable_base_sha)
    if seal_revision is not None:
        if seal_revision not in {0, 1, 2}:
            raise ValueError("seal_revision must be 0, 1, or 2")
        record["sealRevision"] = seal_revision
        record["sealedCandidateRevisions"] = seal_revision
    if sealed_sha is not None:
        if not is_valid_sha(sealed_sha):
            raise ValueError("sealed_sha must be a non-zero 40-hex SHA")
        record["sealedSha"] = normalize_sha(sealed_sha)
        record["sealed"] = True
    if candidate_identity is not None:
        record["candidateIdentity"] = candidate_identity
    if gate_results is not None:
        record.update({key: value for key, value in gate_results.items() if key in {"fast", "bugbot", "full", "staging", "release"}})
    if stop_reason is not None:
        record["stopReason"] = stop_reason
    return record


def phase_ready_for_pr(accepted_issues: list[dict[str, Any]]) -> tuple[bool, str]:
    """True when every required Issue SHA is accepted and included on the Phase branch."""
    if len(accepted_issues) < 1:
        return False, "no_accepted_issues"
    seen_issue_numbers: set[str] = set()
    seen_branches: set[str] = set()
    for row in accepted_issues:
        branch = str(row.get("branch") or "")
        if branch in seen_branches:
            return False, f"duplicate_issue:{branch}"
        seen_branches.add(branch)
        issue_match = re.match(r"^issue/([1-9][0-9]{0,8})-", branch)
        if issue_match:
            number = issue_match.group(1)
            if number in seen_issue_numbers:
                return False, f"duplicate_issue:{number}"
            seen_issue_numbers.add(number)
        if not row.get("accepted"):
            return False, f"issue_not_accepted:{branch}"
        if not row.get("included"):
            return False, f"issue_not_included:{branch}"
        if not is_valid_sha(row.get("sha")):
            return False, f"issue_sha_invalid:{branch}"
        accepted_sha = row.get("acceptanceSha", row.get("acceptedSha"))
        if accepted_sha is not None and normalize_sha(str(accepted_sha)) != normalize_sha(str(row.get("sha"))):
            return False, f"acceptance_sha_mismatch:{branch}"
        live_sha = row.get("liveSha", row.get("tipSha"))
        if live_sha is not None and normalize_sha(str(live_sha)) != normalize_sha(str(row.get("sha"))):
            return False, f"stale_issue_tip:{branch}"
    return True, "all_required_issues_accepted_and_included"


def phase_draft_record_ready(
    record: dict[str, Any] | None,
    *,
    branch: str,
    head_sha: str,
    phase_branch_prefix: str = DEFAULT_PHASE_PREFIX,
    repo: str | Path | None = None,
) -> tuple[bool, str]:
    """Validate an early visibility draft without admitting candidate gates."""

    if not isinstance(record, dict):
        return False, "phase_delivery_record_missing"
    if record.get("schemaVersion") != 1 or record.get("deliveryMode") != MODE_PHASE_INTEGRATION:
        return False, "phase_delivery_schema_or_mode_invalid"
    if not is_phase_branch(branch, phase_branch_prefix):
        return False, "phase_delivery_branch_prefix_mismatch"
    if str(record.get("phaseBranch") or "") != branch:
        return False, "phase_delivery_branch_mismatch"
    recorded = normalize_sha(str(record.get("headSha") or ""))
    tip = normalize_sha(head_sha)
    if not is_valid_sha(recorded) or not is_valid_sha(tip):
        return False, "phase_delivery_head_sha_invalid"
    if repo is not None and is_phase_identity_commit(repo, tip):
        parent = git_first_parent_sha(repo, tip)
        if recorded != parent:
            return False, "phase_delivery_assembled_parent_mismatch"
        bound, detail = bind_phase_identity_fields(record, assembled_sha=recorded, tip_sha=tip)
        if not bound:
            return False, detail
    elif recorded != tip:
        return False, "phase_delivery_head_sha_mismatch"
    accepted = record.get("acceptedIssues")
    if not isinstance(accepted, list) or not accepted:
        return False, "no_accepted_issues"
    for row in accepted:
        if not row.get("accepted") or not is_valid_sha(row.get("sha")):
            return False, f"issue_not_accepted:{row.get('branch')}"
    return True, "early_phase_draft"


def validate_phase_delivery_record(
    record: dict[str, Any] | None,
    *,
    branch: str,
    head_sha: str,
    phase_branch_prefix: str = DEFAULT_PHASE_PREFIX,
    repo: str | Path | None = None,
) -> tuple[bool, str]:
    """Fail-closed validation of a Phase delivery record before opening a Phase PR.

    ``head_sha`` is the identity-binding Phase tip. The committed record names
    the assembled package as ``headSha`` (the tip's only parent). Without a repo,
    only legacy records that still name the tip itself are admitted.
    """
    if not isinstance(record, dict):
        return False, "phase_delivery_record_missing"
    if record.get("schemaVersion") != 1:
        return False, "phase_delivery_schema_invalid"
    if record.get("deliveryMode") != MODE_PHASE_INTEGRATION:
        return False, "phase_delivery_mode_invalid"
    phase_branch = str(record.get("phaseBranch") or "").strip()
    if not phase_branch:
        return False, "phase_delivery_branch_missing"
    if phase_branch != branch:
        return False, f"phase_delivery_branch_mismatch:{phase_branch}"
    if not is_phase_branch(phase_branch, phase_branch_prefix):
        return False, f"phase_delivery_branch_prefix_mismatch:{phase_branch}"
    record_head = normalize_sha(str(record.get("headSha") or ""))
    tip = normalize_sha(head_sha)
    if not is_valid_sha(record_head) or not is_valid_sha(tip):
        return False, "phase_delivery_head_sha_invalid"
    base = normalize_sha(str(record.get("baseSha") or ""))
    if not is_valid_sha(base):
        return False, "phase_delivery_base_sha_invalid"
    accepted = record.get("acceptedIssues")
    if not isinstance(accepted, list):
        return False, "phase_delivery_accepted_issues_invalid"
    if repo is not None:
        parent = git_first_parent_sha(repo, tip)
        if is_phase_identity_commit(repo, tip):
            if not parent:
                return False, "phase_delivery_tip_parent_missing"
            if record_head != parent:
                return False, f"phase_delivery_assembled_parent_mismatch:{record_head[:8]}!={parent[:8]}"
            bound, bind_detail = bind_phase_identity_fields(
                record, assembled_sha=record_head, tip_sha=tip
            )
            if not bound:
                return False, bind_detail
            if not git_is_ancestor(repo, record_head, tip):
                return False, "phase_delivery_assembled_not_ancestor"
            if not git_is_ancestor(repo, base, record_head):
                return False, "phase_delivery_base_not_ancestor"
            for row in accepted:
                if isinstance(row, Mapping) and is_valid_sha(row.get("sha")):
                    if not git_is_ancestor(repo, str(row.get("sha")), record_head):
                        return False, f"issue_not_included:{row.get('branch')}"
        else:
            if record_head != tip:
                return False, f"phase_delivery_head_sha_mismatch:{record_head[:8]}!={tip[:8]}"
    elif record_head != tip:
        return False, "phase_delivery_assembled_parent_unproven"
    return phase_ready_for_pr(accepted)


def main(argv: list[str] | None = None) -> int:
    import sys

    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] in {"-h", "--help"}:
        print(
            "Usage: delivery_modes.py <resolve-config|should-open-pr|named-gate|phase-ready>",
            file=sys.stderr,
        )
        return 2
    cmd = args[0]
    if cmd == "resolve-config":
        root = Path(args[1]) if len(args) > 1 else None
        cfg = load_delivery_config(root)
        json.dump(
            {
                "deliveryMode": cfg.delivery_mode,
                "phaseBranchPrefix": cfg.phase_branch_prefix,
            },
            sys.stdout,
        )
        print()
        return 0
    if cmd == "should-open-pr":
        data = json.load(sys.stdin)
        cfg = DeliveryConfig(
            delivery_mode=str(data.get("deliveryMode") or DEFAULT_DELIVERY_MODE),
            phase_branch_prefix=str(
                data.get("phaseBranchPrefix") or DEFAULT_PHASE_PREFIX
            ),
        )
        decision = should_open_pr_for_branch(
            str(data.get("branch") or ""),
            cfg,
            risk_class=data.get("riskClass"),
            review_ready=bool(data.get("reviewReady", True)),
        )
        json.dump(
            {
                "openPr": decision.open_pr,
                "reason": decision.reason,
                "riskClass": decision.risk_class,
            },
            sys.stdout,
        )
        print()
        return 0 if decision.open_pr else 2
    if cmd == "named-gate":
        data = json.load(sys.stdin)
        evidence = named_gate_evidence(
            gate=str(data.get("gate") or "fast-gate"),
            sha=data.get("sha"),
            checks=list(data.get("checks") or []),
            required=list(data.get("required") or []),
            expected_sha=data.get("expectedSha"),
            stale_event=bool(data.get("staleEvent")),
            allow_neutral=bool(data.get("allowNeutral")),
        )
        json.dump(evidence, sys.stdout)
        print()
        return 0 if evidence.get("status") == "success" else 1
    if cmd == "phase-ready":
        data = json.load(sys.stdin)
        ok, detail = phase_ready_for_pr(list(data.get("acceptedIssues") or []))
        json.dump({"ready": ok, "detail": detail}, sys.stdout)
        print()
        return 0 if ok else 2
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
