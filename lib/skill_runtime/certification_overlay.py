"""Certification overlay from the honest classification ledger.

Catalog generation defaults every skill to ``draft``. A skill becomes ``usable``
in ``catalog/index.json`` only when the phase10 ledger cites sealed live receipt
evidence paths and records ``classification: usable``. Hand-editing the index
without ledger evidence is overwritten on the next catalog rebuild.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional


DEFAULT_LEDGER_REL = Path("evidence/phase10/skill-classification-draft.json")
ALLOWED_STATES = frozenset(
    {"draft", "eval_pending", "usable", "deprecated", "retired"}
)


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


def overlay_from_ledger(ledger: Mapping[str, Any]) -> Dict[str, str]:
    """Build skill_id → certification_state from ledger entries.

    ``usable`` requires non-empty ``sealed_live_receipt_evidence``. Missing or
    invalid states fall back to ``draft`` (fail closed).
    """
    skills = ledger.get("skills") or {}
    if not isinstance(skills, Mapping):
        return {}
    overlay: Dict[str, str] = {}
    for skill_id, raw in skills.items():
        if not isinstance(raw, Mapping):
            overlay[str(skill_id)] = "draft"
            continue
        state = str(raw.get("classification") or "draft").strip() or "draft"
        if state not in ALLOWED_STATES:
            state = "draft"
        evidence = raw.get("sealed_live_receipt_evidence") or []
        if state == "usable" and not (
            isinstance(evidence, list) and any(str(p).strip() for p in evidence)
        ):
            state = "draft"
        overlay[str(skill_id)] = state
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
    return overlay_from_ledger(ledger)


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
