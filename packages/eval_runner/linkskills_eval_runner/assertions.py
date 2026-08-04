"""Deterministic assertion checks for observed eval outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, Union

from .models import AssertionResult, AssertionSpec


class AssertionHardFail(ValueError):
    """Raised when required assertion fields are missing from expected config or output."""


def _require_fields(spec_dict: dict[str, Any], required: list[str], *, context: str) -> None:
    """Hard-fail when expected assertion config keys are missing or null."""
    missing = [key for key in required if key not in spec_dict or spec_dict[key] is None]
    if missing:
        raise AssertionHardFail(
            f"{context}: missing expected assertion fields: {', '.join(missing)}"
        )


def parse_assertion_spec(
    raw: Any,
    *,
    require_keys: Optional[list[str]] = None,
) -> AssertionSpec:
    """Normalize a raw assertions mapping into AssertionSpec.

    When *require_keys* is provided, missing keys hard-fail immediately.
    """
    if raw is None:
        if require_keys:
            raise AssertionHardFail(
                f"assertions: missing expected assertion fields: {', '.join(require_keys)}"
            )
        return AssertionSpec()
    if not isinstance(raw, dict):
        raise AssertionHardFail("assertions: expected a mapping of assertion fields")
    if require_keys:
        _require_fields(raw, require_keys, context="assertions")

    must_contain = raw.get("must_contain") or []
    must_not_contain = raw.get("must_not_contain") or []
    json_fields = raw.get("json_schema_fields") or []
    file_exists = raw.get("file_exists") or []
    exit_code = raw.get("exit_code")
    exact = raw.get("exact_output")

    if exit_code is not None and not isinstance(exit_code, int):
        try:
            exit_code = int(exit_code)
        except (TypeError, ValueError) as exc:
            raise AssertionHardFail(f"assertions.exit_code must be an int, got {exit_code!r}") from exc

    if exact is not None and not isinstance(exact, str):
        exact = str(exact)

    return AssertionSpec(
        must_contain=[str(x) for x in must_contain],
        must_not_contain=[str(x) for x in must_not_contain],
        json_schema_fields=[str(x) for x in json_fields],
        exit_code=exit_code,
        file_exists=[str(x) for x in file_exists],
        exact_output=exact,
    )


def check_must_contain(output: str, needles: list[str]) -> list[AssertionResult]:
    results: list[AssertionResult] = []
    for needle in needles:
        ok = needle in output
        results.append(
            AssertionResult(
                name=f"must_contain:{needle!r}",
                passed=ok,
                detail="found" if ok else f"missing substring {needle!r}",
            )
        )
    return results


def check_must_not_contain(output: str, needles: list[str]) -> list[AssertionResult]:
    results: list[AssertionResult] = []
    for needle in needles:
        ok = needle not in output
        results.append(
            AssertionResult(
                name=f"must_not_contain:{needle!r}",
                passed=ok,
                detail="absent" if ok else f"forbidden substring {needle!r} present",
            )
        )
    return results


def check_json_schema_fields(output: str, fields: list[str]) -> list[AssertionResult]:
    """Require *fields* to exist as top-level keys in a JSON object output.

    Missing expected fields are hard-fail assertion results.
    """
    if not fields:
        return []
    results: list[AssertionResult] = []
    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        return [
            AssertionResult(
                name="json_schema_fields",
                passed=False,
                hard_fail=True,
                detail=f"output is not valid JSON: {exc}",
            )
        ]
    if not isinstance(data, dict):
        return [
            AssertionResult(
                name="json_schema_fields",
                passed=False,
                hard_fail=True,
                detail="output JSON must be an object to check schema fields",
            )
        ]
    missing = [name for name in fields if name not in data]
    if missing:
        results.append(
            AssertionResult(
                name="json_schema_fields",
                passed=False,
                hard_fail=True,
                detail=f"missing expected fields: {', '.join(missing)}",
            )
        )
    else:
        results.append(
            AssertionResult(
                name="json_schema_fields",
                passed=True,
                detail=f"present: {', '.join(fields)}",
            )
        )
    return results


def check_exit_code(observed: Optional[int], expected: Optional[int]) -> list[AssertionResult]:
    if expected is None:
        return []
    if observed is None:
        return [
            AssertionResult(
                name="exit_code",
                passed=False,
                hard_fail=True,
                detail=f"expected exit_code={expected} but observed exit code is missing",
            )
        ]
    ok = int(observed) == int(expected)
    return [
        AssertionResult(
            name="exit_code",
            passed=ok,
            hard_fail=not ok,
            detail="match" if ok else f"expected {expected}, observed {observed}",
        )
    ]


def check_file_exists(
    paths: list[str],
    *,
    workspace_root: Optional[Union[str, Path]] = None,
) -> list[AssertionResult]:
    results: list[AssertionResult] = []
    root = Path(workspace_root) if workspace_root else None
    for rel in paths:
        candidate = Path(rel)
        if not candidate.is_absolute() and root is not None:
            candidate = root / rel
        ok = candidate.exists()
        results.append(
            AssertionResult(
                name=f"file_exists:{rel}",
                passed=ok,
                hard_fail=not ok,
                detail="exists" if ok else f"missing file {candidate}",
            )
        )
    return results


def run_assertions(
    output: str,
    spec: AssertionSpec,
    *,
    observed_exit_code: Optional[int] = None,
    workspace_root: Optional[Union[str, Path]] = None,
) -> list[AssertionResult]:
    """Apply deterministic checks to *output* (and optional exit/file context)."""
    text = output if output is not None else ""
    results: list[AssertionResult] = []
    results.extend(check_must_contain(text, spec.must_contain))
    results.extend(check_must_not_contain(text, spec.must_not_contain))
    results.extend(check_json_schema_fields(text, spec.json_schema_fields))
    results.extend(check_exit_code(observed_exit_code, spec.exit_code))
    results.extend(check_file_exists(spec.file_exists, workspace_root=workspace_root))

    if spec.exact_output is not None:
        ok = text == spec.exact_output
        results.append(
            AssertionResult(
                name="exact_output",
                passed=ok,
                detail="match" if ok else "observed output differs from exact_output",
            )
        )
    return results


def assertions_passed(results: list[AssertionResult]) -> bool:
    """True when every assertion passed (empty list is a pass)."""
    return all(r.passed for r in results)


def assertions_hard_failed(results: list[AssertionResult]) -> bool:
    """True when any assertion is marked hard_fail and did not pass."""
    return any((not r.passed) and r.hard_fail for r in results)
