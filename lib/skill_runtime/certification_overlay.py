"""Certification overlay from the honest classification ledger.

Catalog generation defaults every skill to ``draft``. A skill becomes ``usable``
in ``catalog/index.json`` only when the phase10 ledger cites sealed live receipt
evidence that **verifies** (HMAC + binding hashes + PASS) — not merely nonempty
path strings. Hand-editing the index without ledger evidence is overwritten on
the next catalog rebuild.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


DEFAULT_LEDGER_REL = Path("evidence/phase10/skill-classification-draft.json")
ALLOWED_STATES = frozenset(
    {"draft", "eval_pending", "usable", "deprecated", "retired"}
)
_PASS_STATUSES = frozenset({"passed", "pass", "ok", "success"})


def _ensure_core_importable() -> None:
    """Add packages/core so linkskills_core is importable from repo scripts."""
    repo = Path(__file__).resolve().parents[2]
    core = str(repo / "packages" / "core")
    if core not in sys.path:
        sys.path.insert(0, core)


def classification_ledger_path(repo_root: Path) -> Path:
    """Return the default classification ledger path."""
    return Path(repo_root) / DEFAULT_LEDGER_REL


def load_classification_ledger(
    repo_root: Path,
    *,
    ledger_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Load the phase10 classification ledger JSON."""
    path = Path(ledger_path) if ledger_path is not None else classification_ledger_path(repo_root)
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"classification ledger must be an object: {path}")
    return payload


def resolve_repo_contained_path(repo_root: Path, raw: str) -> Optional[Path]:
    """Resolve ``raw`` to a file path strictly under ``repo_root``.

    Rejects empty strings, ``..`` escapes, and absolute paths outside the repo.
    """
    text = str(raw or "").strip()
    if not text:
        return None
    root = Path(repo_root).resolve()
    candidate = Path(text)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved


def _iter_receipts(evidence: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    """Collect executor receipts from sealed evidence document shapes."""
    out: List[Mapping[str, Any]] = []
    cases = evidence.get("cases")
    if isinstance(cases, Sequence) and not isinstance(cases, (str, bytes, bytearray)):
        for raw in cases:
            if not isinstance(raw, Mapping):
                continue
            receipt = raw.get("execution_receipt")
            if receipt is None:
                nested = raw.get("evidence")
                if isinstance(nested, Mapping):
                    receipt = nested.get("execution_receipt")
            if isinstance(receipt, Mapping):
                out.append(receipt)
    if out:
        return out
    for key in ("execution_receipts", "receipts"):
        value = evidence.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for raw in value:
                if isinstance(raw, Mapping):
                    out.append(raw)
    return out


def _evidence_result_passed(evidence: Mapping[str, Any]) -> bool:
    """True when sealed evidence records an overall PASS.

    Accepts ``certified: true`` and/or every case ``status`` in
    {passed, pass, ok, success}. Fail closed when neither signal is present.
    """
    certified = evidence.get("certified")
    if certified is True:
        cases = evidence.get("cases")
        if isinstance(cases, Sequence) and not isinstance(cases, (str, bytes, bytearray)):
            for raw in cases:
                if not isinstance(raw, Mapping):
                    return False
                status = str(raw.get("status") or "").strip().lower()
                if status and status not in _PASS_STATUSES:
                    return False
        return True
    if certified is False:
        return False

    cases = evidence.get("cases")
    if not isinstance(cases, Sequence) or isinstance(cases, (str, bytes, bytearray)):
        return False
    if not cases:
        return False
    for raw in cases:
        if not isinstance(raw, Mapping):
            return False
        status = str(raw.get("status") or "").strip().lower()
        if status not in _PASS_STATUSES:
            return False
    return True


def _expected_tool_hashes(entry: Mapping[str, Any]) -> Optional[frozenset[str]]:
    """Optional ledger-expected tool hashes (single or list)."""
    raw = entry.get("tool_hashes")
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes, bytearray)):
        values = {str(v).strip() for v in raw if str(v).strip()}
        return frozenset(values) if values else None
    single = str(entry.get("tool_hash") or "").strip()
    if single:
        return frozenset({single})
    return None


def _receipts_bind_expected(
    skill_id: str,
    entry: Mapping[str, Any],
    evidence: Mapping[str, Any],
    receipts: Sequence[Mapping[str, Any]],
) -> bool:
    """Bind skill_id + release/profile/suite/tool hashes across all receipts."""
    if not receipts:
        return False

    expected_release = str(
        entry.get("skill_release_hash") or entry.get("release_hash") or ""
    ).strip()
    expected_profile = str(
        entry.get("profile_hash") or entry.get("execution_profile_hash") or ""
    ).strip()
    expected_suite = str(entry.get("suite_hash") or "").strip()
    expected_tools = _expected_tool_hashes(entry)

    # Top-level evidence fields also bind when present on the document.
    doc_skill = str(evidence.get("skill_id") or "").strip()
    if doc_skill and doc_skill != skill_id:
        return False
    doc_release = str(evidence.get("skill_release_hash") or evidence.get("release_hash") or "").strip()
    if expected_release and doc_release and doc_release != expected_release:
        return False
    doc_profile = str(
        evidence.get("profile_hash") or evidence.get("execution_profile_hash") or ""
    ).strip()
    if expected_profile and doc_profile and doc_profile != expected_profile:
        return False
    doc_suite = str(evidence.get("suite_hash") or "").strip()
    if expected_suite and doc_suite and doc_suite != expected_suite:
        return False

    for receipt in receipts:
        if str(receipt.get("skill_id") or "").strip() != skill_id:
            return False

        release = str(receipt.get("skill_release_hash") or "").strip()
        if not release:
            return False
        if expected_release and release != expected_release:
            return False

        profile = str(
            receipt.get("execution_profile_hash") or receipt.get("profile_hash") or ""
        ).strip()
        if not profile:
            return False
        if expected_profile and profile != expected_profile:
            return False

        suite = str(receipt.get("suite_hash") or "").strip()
        if not suite:
            return False
        if expected_suite and suite != expected_suite:
            return False

        tool_calls = receipt.get("tool_calls")
        if not isinstance(tool_calls, Sequence) or isinstance(
            tool_calls, (str, bytes, bytearray)
        ):
            return False
        if not tool_calls:
            return False
        for tc in tool_calls:
            if not isinstance(tc, Mapping):
                return False
            tool_hash = str(tc.get("tool_hash") or "").strip()
            if not tool_hash:
                return False
            if expected_tools is not None and tool_hash not in expected_tools:
                return False

        toolchain = receipt.get("toolchain")
        if toolchain is not None and not isinstance(toolchain, Mapping):
            return False

    return True


def verify_sealed_live_evidence(
    repo_root: Path,
    skill_id: str,
    entry: Mapping[str, Any],
) -> bool:
    """Return True only when every cited sealed path verifies for ``skill_id``."""
    evidence_paths = entry.get("sealed_live_receipt_evidence") or []
    if not isinstance(evidence_paths, list) or not evidence_paths:
        return False

    _ensure_core_importable()
    from linkskills_core.certification import evaluate_certification_evidence

    verified_any = False
    for raw_path in evidence_paths:
        resolved = resolve_repo_contained_path(repo_root, str(raw_path))
        if resolved is None or not resolved.is_file():
            return False
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return False
        if not isinstance(payload, dict):
            return False

        decision = evaluate_certification_evidence(payload)
        if not decision.allowed:
            return False
        if not _evidence_result_passed(payload):
            return False

        receipts = _iter_receipts(payload)
        if not _receipts_bind_expected(skill_id, entry, payload, receipts):
            return False
        verified_any = True

    return verified_any


def overlay_from_ledger(
    ledger: Mapping[str, Any],
    *,
    repo_root: Path,
) -> Dict[str, str]:
    """Build skill_id → certification_state from ledger entries.

    ``usable`` requires verified sealed live receipt evidence under ``repo_root``.
    Missing or invalid states fall back to ``draft`` (fail closed).
    """
    skills = ledger.get("skills") or {}
    if not isinstance(skills, Mapping):
        return {}
    overlay: Dict[str, str] = {}
    root = Path(repo_root)
    for skill_id, raw in skills.items():
        sid = str(skill_id)
        if not isinstance(raw, Mapping):
            overlay[sid] = "draft"
            continue
        state = str(raw.get("classification") or "draft").strip() or "draft"
        if state not in ALLOWED_STATES:
            state = "draft"
        if state == "usable" and not verify_sealed_live_evidence(root, sid, raw):
            state = "draft"
        overlay[sid] = state
    return overlay


def hash_overlay_from_ledger(ledger: Mapping[str, Any]) -> Dict[str, Dict[str, str]]:
    """Build skill_id → sealed release/profile hashes from ledger entries."""
    skills = ledger.get("skills") or {}
    if not isinstance(skills, Mapping):
        return {}
    out: Dict[str, Dict[str, str]] = {}
    for skill_id, raw in skills.items():
        if not isinstance(raw, Mapping):
            continue
        release = str(
            raw.get("skill_release_hash") or raw.get("release_hash") or ""
        ).strip()
        profile = str(raw.get("profile_hash") or "").strip()
        if not release and not profile:
            continue
        meta: Dict[str, str] = {}
        if release:
            meta["skill_release_hash"] = release
            meta["release_hash"] = release
        if profile:
            meta["profile_hash"] = profile
        out[str(skill_id)] = meta
    return out


def load_certification_overlay(
    repo_root: Path,
    *,
    ledger_path: Optional[Path] = None,
) -> Dict[str, str]:
    """Load certification_state overlay for catalog generation."""
    ledger = load_classification_ledger(repo_root, ledger_path=ledger_path)
    if not ledger:
        return {}
    return overlay_from_ledger(ledger, repo_root=repo_root)


def load_hash_overlay(
    repo_root: Path,
    *,
    ledger_path: Optional[Path] = None,
) -> Dict[str, Dict[str, str]]:
    """Load sealed release/profile hash overlay for catalog generation."""
    ledger = load_classification_ledger(repo_root, ledger_path=ledger_path)
    if not ledger:
        return {}
    return hash_overlay_from_ledger(ledger)
