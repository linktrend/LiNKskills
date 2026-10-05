#!/usr/bin/env python3
"""Offline, value-redacting validator for this skill's declared input schema."""
import json
import sys
from pathlib import Path


def _emit(status, *, reason=None, missing_fields=None, validation_errors=None):
    result = {
        "status": status,
        "missing_fields": sorted(missing_fields or []),
        "validation_errors": validation_errors or [],
        "value_echo": False,
        "external_effects": [],
        "mutations": [],
    }
    if reason:
        result["reason"] = reason
    print(json.dumps(result, sort_keys=True))


def _at_path(value, path):
    for part in path:
        if isinstance(value, dict):
            value = value.get(part)
        elif isinstance(value, list) and isinstance(part, int) and 0 <= part < len(value):
            value = value[part]
        else:
            return None
    return value


def main():
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        _emit("FAILED", reason="invalid_json")
        return 2
    if not isinstance(value, dict):
        _emit("FAILED", reason="expected_object")
        return 2

    schema_path = Path(__file__).resolve().parent.parent / "references" / "schemas.json"
    try:
        document = json.loads(schema_path.read_text(encoding="utf-8"))
        schema = document["definitions"]["input"]
        from jsonschema import Draft202012Validator, FormatChecker
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        errors = sorted(
            validator.iter_errors(value),
            key=lambda error: (tuple(str(part) for part in error.absolute_path), str(error.validator)),
        )
    except ImportError:
        _emit("FAILED", reason="jsonschema_unavailable")
        return 2
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        _emit("FAILED", reason="input_schema_unavailable_or_invalid")
        return 2

    if not errors:
        _emit("INPUT_VALID")
        return 0

    missing = set()
    safe_errors = []
    for error in errors:
        path = list(error.absolute_path)
        safe_errors.append({"path": ".".join(str(part) for part in path), "keyword": str(error.validator)})
        if error.validator == "required":
            parent = _at_path(value, path)
            if isinstance(parent, dict):
                missing.update(f"{'.'.join(str(part) for part in path)}.{name}".strip(".")
                               for name in error.validator_value if name not in parent)
    _emit("NEEDS_CONTEXT", missing_fields=missing, validation_errors=safe_errors)
    return 3


if __name__ == "__main__":
    sys.exit(main())
