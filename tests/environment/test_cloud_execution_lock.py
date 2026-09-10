#!/usr/bin/env python3
"""ENV-00: hash-locked cloud/CI environment contract tests."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = REPO_ROOT / "requirements-dev.lock"
REQ_PATH = REPO_ROOT / "requirements-dev.txt"
CI_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
DOC_PATH = REPO_ROOT / "docs" / "development" / "CLOUD-EXECUTION.md"

INSTALLABLE_LOCAL = (
    "packages/core",
    "packages/tool_runtime",
    "packages/gateway",
    "packages/client",
    "packages/mcp_server",
    "packages/librarian_domain",
    "packages/publisher",
    "packages/eval_runner",
)

HASH_LINE = re.compile(r"^\s+--hash=sha256:[0-9a-f]{64}\s*\\?\s*$")
REQ_LINE = re.compile(r"^([A-Za-z0-9_.+-]+(?:\[[^\]]+\])?)==([^\\\s]+)")


def _lock_text() -> str:
    return LOCK_PATH.read_text(encoding="utf-8")


def _lock_stanzas() -> list[tuple[str, str, list[str]]]:
    """Return (name, version, hashes) for every locked requirement."""
    stanzas: list[tuple[str, str, list[str]]] = []
    current: tuple[str, str, list[str]] | None = None
    for raw in _lock_text().splitlines():
        if raw.startswith("#") or not raw.strip():
            continue
        req = REQ_LINE.match(raw)
        if req:
            if current is not None:
                stanzas.append(current)
            current = (req.group(1), req.group(2), [])
            continue
        if HASH_LINE.match(raw):
            digest = raw.split("sha256:", 1)[1].split()[0].rstrip("\\")
            assert current is not None, f"hash without requirement: {raw}"
            current[2].append(digest)
            continue
        raise AssertionError(f"unrecognized lock line: {raw!r}")
    if current is not None:
        stanzas.append(current)
    return stanzas


def test_lockfile_exists_and_is_fully_hashed() -> None:
    stanzas = _lock_stanzas()
    assert stanzas, "requirements-dev.lock has no requirement stanzas"
    names = [name.split("[", 1)[0].lower() for name, _ver, _hashes in stanzas]
    for expected in ("pytest", "pyyaml", "setuptools", "wheel", "cryptography", "psycopg"):
        assert expected in names, f"missing top-level pin {expected}"
    for name, version, hashes in stanzas:
        assert version, f"{name} missing version"
        assert hashes, f"{name}=={version} has no sha256 hashes"
        assert len(set(hashes)) == len(hashes), f"{name} duplicate hashes"


def test_lockfile_does_not_pin_local_or_product_packages() -> None:
    names = {name.split("[", 1)[0].lower() for name, _ver, _hashes in _lock_stanzas()}
    forbidden = {
        "linkskills",
        "linkskills-core",
        "linkskills-tool-runtime",
        "linkskills-gateway",
        "linkskills-client",
        "linkskills-mcp",
        "linkskills-librarian",
        "linkskills-publisher",
        "linkskills-eval-runner",
    }
    assert names.isdisjoint(forbidden)


def test_requirements_dev_txt_remains_range_input() -> None:
    text = REQ_PATH.read_text(encoding="utf-8")
    assert "pyyaml>=" in text
    assert "pytest>=" in text
    assert "psycopg[binary]>=" in text
    assert "cryptography>=" in text


def test_ci_installs_lock_with_require_hashes_on_protected_matrix() -> None:
    text = CI_PATH.read_text(encoding="utf-8")
    assert "ubuntu-24.04-arm" in text
    assert 'python-version: "3.11"' in text
    assert "python -m pip install --require-hashes -r requirements-dev.lock" in text
    assert "pip install -r requirements-dev.txt" not in text
    assert "tests/environment" in text


def test_cloud_execution_doc_records_install_order_and_pythonpath_only() -> None:
    text = DOC_PATH.read_text(encoding="utf-8")
    assert "python -m pip install --require-hashes -r requirements-dev.lock" in text
    positions = [text.index(f"pip install --no-deps -e {path}") for path in INSTALLABLE_LOCAL]
    assert positions == sorted(positions)
    umbrella = text.index("pip install --no-deps -e .")
    assert umbrella > positions[-1]
    assert "packages/contracts" in text and "PYTHONPATH" in text
    assert "packages/persistence" in text
    assert "not pip-installable" in text


def test_contracts_and_persistence_remain_pythonpath_only() -> None:
    assert not (REPO_ROOT / "packages" / "contracts" / "pyproject.toml").exists()
    assert not (REPO_ROOT / "packages" / "persistence" / "pyproject.toml").exists()
    for path in INSTALLABLE_LOCAL:
        assert (REPO_ROOT / path / "pyproject.toml").is_file()


def test_lock_stanza_digest_is_stable_marker() -> None:
    """Comment headers may change; hashed stanzas must remain parseable."""
    body = "".join(
        line
        for line in _lock_text().splitlines(True)
        if line.strip() and not line.startswith("#")
    )
    assert "==" in body and "--hash=sha256:" in body
    pytest.importorskip("hashlib")
    import hashlib

    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    assert len(digest) == 64
