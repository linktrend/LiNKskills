#!/usr/bin/env python3
"""Offline, value-redacting validator for the HR skill's declared input schema."""
import json
import sys
from pathlib import Path


def _emit(status, *, reason=None, missing_fields=None, invalid_fields=None):
    result = {
        "status": status,
        "missing_fields": sorted(missing_fields or []),
        "invalid_fields": sorted(invalid_fields or []),
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


def _display_path(path):
    return ".".join(str(part) for part in path)


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
        from jsonschema.exceptions import SchemaError
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        errors = sorted(
            validator.iter_errors(value),
            key=lambda error: (tuple(str(part) for part in error.absolute_path), str(error.validator)),
        )
    except ImportError:
        _emit("FAILED", reason="jsonschema_unavailable")
        return 2
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, SchemaError):
        _emit("FAILED", reason="input_schema_unavailable_or_invalid")
        return 2

    if not errors:
        _emit("ENVELOPE_PRESENT")
        return 0

    missing = set()
    invalid = set()
    for error in errors:
        path = list(error.absolute_path)
        location = _display_path(path)
        if error.validator == "required":
            parent = _at_path(value, path)
            if isinstance(parent, dict):
                missing.update(f"{location}.{name}".strip(".")
                               for name in error.validator_value if name not in parent)
        elif error.validator == "additionalProperties":
            parent = _at_path(value, path)
            allowed = error.schema.get("properties", {})
            if isinstance(parent, dict):
                invalid.update(f"unexpected:{location}.{name}".strip(".")
                               for name in parent if name not in allowed)
        else:
            invalid.add(location or "input")
    _emit("NEEDS_CONTEXT", missing_fields=missing, invalid_fields=invalid)
    return 3


if __name__ == "__main__":
    sys.exit(main())
