"""Tests for deterministic eval assertions."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from linkskills_eval_runner.assertions import (
    AssertionHardFail,
    assertions_hard_failed,
    assertions_passed,
    check_exit_code,
    check_file_exists,
    check_json_schema_fields,
    check_must_contain,
    check_must_not_contain,
    parse_assertion_spec,
    run_assertions,
)
from linkskills_eval_runner.models import AssertionSpec


def test_must_contain_and_must_not_contain():
    spec = AssertionSpec(
        must_contain=["hello", "world"],
        must_not_contain=["secret"],
    )
    results = run_assertions("hello brave world", spec)
    assert assertions_passed(results)
    assert all(r.passed for r in check_must_contain("hello", ["hello"]))
    assert not check_must_not_contain("has secret", ["secret"])[0].passed


def test_json_schema_fields_hard_fail_on_missing():
    output = json.dumps({"ok": True, "message": "echo"})
    ok = check_json_schema_fields(output, ["ok", "message"])
    assert assertions_passed(ok)

    missing = check_json_schema_fields(output, ["ok", "missing_field"])
    assert not assertions_passed(missing)
    assert assertions_hard_failed(missing)


def test_exit_code_and_file_exists(tmp_path: Path):
    present = tmp_path / "artifact.txt"
    present.write_text("x", encoding="utf-8")

    exit_ok = check_exit_code(0, 0)
    assert assertions_passed(exit_ok)

    exit_bad = check_exit_code(1, 0)
    assert assertions_hard_failed(exit_bad)

    files = check_file_exists(["artifact.txt", "missing.txt"], workspace_root=tmp_path)
    assert files[0].passed
    assert not files[1].passed
    assert files[1].hard_fail


def test_parse_assertion_spec_hard_fails_on_missing_expected_fields():
    with pytest.raises(AssertionHardFail):
        parse_assertion_spec({}, require_keys=["must_contain"])

    spec = parse_assertion_spec(
        {
            "must_contain": ["a"],
            "json_schema_fields": ["id"],
            "exit_code": 0,
            "file_exists": ["out.txt"],
        }
    )
    assert spec.must_contain == ["a"]
    assert spec.json_schema_fields == ["id"]
    assert spec.exit_code == 0
    assert spec.file_exists == ["out.txt"]
