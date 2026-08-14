"""Stdlib-friendly JSON Schema loader and bounded contract validator.

The validator intentionally supports the small, deterministic subset used by
the repository's v0.1 and v0.2 contracts. It remains dependency-free so fresh
checkouts can validate contract fixtures before package installation.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.1"

_JSON_TYPE_MAP = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


@dataclass
class ValidationError:
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


@dataclass
class ValidationResult:
    ok: bool
    errors: list[ValidationError] = field(default_factory=list)

    def raise_for_errors(self) -> None:
        if not self.ok:
            joined = "; ".join(str(e) for e in self.errors)
            raise ValueError(f"validation failed: {joined}")


def schemas_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "schemas"


def list_schemas() -> list[str]:
    return sorted(
        path.name
        for pattern in ("*-v0.1.json", "*-v0.2.json")
        for path in schemas_dir().glob(pattern)
    )


def load_schema(name: str) -> dict[str, Any]:
    """Load a schema by filename or an explicitly versioned short name."""
    filename = name if name.endswith(".json") else f"{name}.json"
    if not filename.endswith(".json"):
        filename = f"{filename}.json"
    # normalize short names like skill-pack
    candidates = [
        schemas_dir() / filename,
        schemas_dir() / f"{name}-v0.1.json",
        schemas_dir() / f"{name}-v0.2.json",
        schemas_dir() / f"{name}.json",
    ]
    for path in candidates:
        if path.is_file():
            with path.open(encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                raise TypeError(f"schema root must be object: {path}")
            return data
    raise FileNotFoundError(f"schema not found: {name}")


def validate_required(instance: Any, required: list[str], path: str = "$") -> list[ValidationError]:
    errors: list[ValidationError] = []
    if not isinstance(instance, dict):
        errors.append(ValidationError(path, "expected object for required-field check"))
        return errors
    for key in required:
        if key not in instance:
            errors.append(ValidationError(f"{path}.{key}", "required field missing"))
    return errors


def validate_instance(instance: Any, schema: dict[str, Any] | str, *, path: str = "$") -> ValidationResult:
    """Validate instance against a schema dict or schema name."""
    root = load_schema(schema) if isinstance(schema, str) else schema
    errors: list[ValidationError] = []
    _validate(instance, root, root, path, errors)
    return ValidationResult(ok=not errors, errors=errors)


def _resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError(f"only local refs supported: {ref}")
    node: Any = root
    for part in ref[2:].split("/"):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"unresolved $ref: {ref}")
        node = node[part]
    if not isinstance(node, dict):
        raise TypeError(f"$ref target must be object: {ref}")
    return node


def _type_matches(value: Any, declared: str | list[str]) -> bool:
    types = declared if isinstance(declared, list) else [declared]
    for t in types:
        py = _JSON_TYPE_MAP.get(t)
        if py is None:
            continue
        if t == "number" and isinstance(value, bool):
            continue
        if t == "integer" and isinstance(value, bool):
            continue
        if isinstance(value, py):
            if t == "number" and isinstance(value, bool):
                continue
            return True
    return False


def _validate(
    instance: Any,
    schema: dict[str, Any],
    root: dict[str, Any],
    path: str,
    errors: list[ValidationError],
) -> None:
    _validate_combinators(instance, schema, root, path, errors)

    if "$ref" in schema:
        _validate(instance, _resolve_ref(root, schema["$ref"]), root, path, errors)
        return

    if "const" in schema and instance != schema["const"]:
        errors.append(ValidationError(path, f"expected const {schema['const']!r}"))
        return

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(ValidationError(path, f"value not in enum {schema['enum']!r}"))
        return

    if "type" in schema and not _type_matches(instance, schema["type"]):
        errors.append(ValidationError(path, f"expected type {schema['type']!r}, got {type(instance).__name__}"))
        return

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < int(schema["minLength"]):
            errors.append(ValidationError(path, f"string shorter than minLength {schema['minLength']}"))
        if "maxLength" in schema and len(instance) > int(schema["maxLength"]):
            errors.append(ValidationError(path, f"string longer than maxLength {schema['maxLength']}"))
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            errors.append(ValidationError(path, f"string does not match pattern {schema['pattern']!r}"))
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(instance.replace("Z", "+00:00"))
            except ValueError:
                errors.append(ValidationError(path, "invalid date-time"))

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(ValidationError(path, f"value below minimum {schema['minimum']}"))
        if "exclusiveMinimum" in schema and instance <= schema["exclusiveMinimum"]:
            errors.append(ValidationError(path, f"value not above exclusiveMinimum {schema['exclusiveMinimum']}"))
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(ValidationError(path, f"value above maximum {schema['maximum']}"))

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < int(schema["minItems"]):
            errors.append(ValidationError(path, f"array shorter than minItems {schema['minItems']}"))
        if "maxItems" in schema and len(instance) > int(schema["maxItems"]):
            errors.append(ValidationError(path, f"array longer than maxItems {schema['maxItems']}"))
        if schema.get("uniqueItems"):
            encoded = [json.dumps(item, sort_keys=True, separators=(",", ":")) for item in instance]
            if len(set(encoded)) != len(encoded):
                errors.append(ValidationError(path, "array items must be unique"))
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for idx, item in enumerate(instance):
                _validate(item, item_schema, root, f"{path}[{idx}]", errors)

    if isinstance(instance, dict):
        if "maxProperties" in schema and len(instance) > int(schema["maxProperties"]):
            errors.append(ValidationError(path, f"object has more than maxProperties {schema['maxProperties']}"))
        required = schema.get("required") or []
        errors.extend(validate_required(instance, required, path=path))
        props = schema.get("properties") or {}
        for key, child_schema in props.items():
            if key in instance and isinstance(child_schema, dict):
                _validate(instance[key], child_schema, root, f"{path}.{key}", errors)
        if schema.get("additionalProperties") is False:
            extras = set(instance) - set(props)
            for key in sorted(extras):
                errors.append(ValidationError(f"{path}.{key}", "additional property not allowed"))

    forbidden = schema.get("x-forbidden-property-names") or []
    if forbidden:
        _find_forbidden_properties(instance, set(forbidden), path, errors)


def _validate_combinators(
    instance: Any,
    schema: dict[str, Any],
    root: dict[str, Any],
    path: str,
    errors: list[ValidationError],
) -> None:
    """Validate the compositional keywords used by the v2 record variants."""
    for child in schema.get("allOf") or []:
        if isinstance(child, dict):
            _validate(instance, child, root, path, errors)

    alternatives = schema.get("oneOf")
    if isinstance(alternatives, list):
        successes = 0
        for child in alternatives:
            branch_errors: list[ValidationError] = []
            if isinstance(child, dict):
                _validate(instance, child, root, path, branch_errors)
            if not branch_errors:
                successes += 1
        if successes != 1:
            errors.append(ValidationError(path, f"oneOf expected exactly one matching branch, got {successes}"))

    alternatives = schema.get("anyOf")
    if isinstance(alternatives, list):
        if not any(
            isinstance(child, dict) and not _branch_errors(instance, child, root, path)
            for child in alternatives
        ):
            errors.append(ValidationError(path, "anyOf expected at least one matching branch"))

    if isinstance(schema.get("not"), dict) and not _branch_errors(instance, schema["not"], root, path):
        errors.append(ValidationError(path, "not condition matched"))

    condition = schema.get("if")
    if isinstance(condition, dict):
        if not _branch_errors(instance, condition, root, path):
            child = schema.get("then")
        else:
            child = schema.get("else")
        if isinstance(child, dict):
            _validate(instance, child, root, path, errors)


def _branch_errors(instance: Any, schema: dict[str, Any], root: dict[str, Any], path: str) -> list[ValidationError]:
    branch_errors: list[ValidationError] = []
    _validate(instance, schema, root, path, branch_errors)
    return branch_errors


def _find_forbidden_properties(
    instance: Any,
    forbidden: set[str],
    path: str,
    errors: list[ValidationError],
) -> None:
    if isinstance(instance, dict):
        for key, value in instance.items():
            if key.lower() in forbidden:
                errors.append(ValidationError(f"{path}.{key}", "forbidden property name"))
            _find_forbidden_properties(value, forbidden, f"{path}.{key}", errors)
    elif isinstance(instance, list):
        for idx, value in enumerate(instance):
            _find_forbidden_properties(value, forbidden, f"{path}[{idx}]", errors)
