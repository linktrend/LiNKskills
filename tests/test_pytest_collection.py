"""Ensure pytest collection excludes archive/ by default."""

from __future__ import annotations

from pathlib import Path


def test_pytest_does_not_collect_archive() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    archive_tests = list((repo_root / "archive").rglob("test_*.py"))
    # archive may contain historical test files; default collection must ignore them.
    ini = (repo_root / "pytest.ini").read_text(encoding="utf-8")
    assert "archive" in ini
    assert "norecursedirs" in ini
    # Sanity: archive tree exists and has at least one test_*.py somewhere.
    assert archive_tests, "expected historical test_*.py under archive/ for this guard"
