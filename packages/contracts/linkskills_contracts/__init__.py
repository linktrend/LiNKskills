"""LiNKskills contract schemas and lightweight validators (v0.1)."""

from .validate import (
    SCHEMA_VERSION,
    ValidationError,
    ValidationResult,
    list_schemas,
    load_schema,
    schemas_dir,
    validate_instance,
    validate_required,
)

__all__ = [
    "SCHEMA_VERSION",
    "ValidationError",
    "ValidationResult",
    "list_schemas",
    "load_schema",
    "schemas_dir",
    "validate_instance",
    "validate_required",
]

__version__ = "0.1.0"
